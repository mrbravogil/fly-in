# Representación de la posición actual de los drones

## Comportamiento deseado

La salida debe indicar dónde está cada dron en ese turno:

- En un hub: mostrar el nombre del hub.
- En tránsito por una conexión: mostrar los dos extremos de la conexión.
- Mostrar también los drones que esperan, pues siguen ocupando una posición.

Ejemplo:

```text
[D1: waypoint1] [D2: waypoint1-waypoint2]
```

Los desplazamientos normales duran un turno y dejan al dron directamente en
el hub de destino. La conexión se muestra como posición intermedia al viajar
hacia un hub `restricted`, cuyo desplazamiento dura dos turnos.

## Origen del problema

`Drone` ya tiene `current_hub` y `current_connection`, y
`Connection.enter()` asigna `current_connection`. Pero
`Fly_in._execute_schedule()` no llama a `enter()` y mueve directamente cada
dron con `move_next_hub()`. Además, `_record_move()` imprime el movimiento
origen-destino y no consulta la posición actual.

Para representar una conexión durante el turno de tránsito, el motor debe:

1. Llamar a `Connection.enter()` al iniciar un desplazamiento hacia un hub
   `restricted` y liberar el hub de origen.
2. Mantener el dron en `current_connection` durante ese turno.
3. En el siguiente turno, completar el desplazamiento con `move_next_hub()`.
4. Hacer que el planificador continúe al otro extremo de la conexión cuando el
   dron ya está en tránsito.

## Diff propuesto (no aplicado)

### Mostrar la posición actual en vez del movimiento

```diff
diff --git a/src/fly_in.py b/src/fly_in.py
@@
-    def _record_move(
-        self,
-        drone_movements: list[tuple[Drone, Hub, Hub]],
-    ) -> str:
-        """Build the terminal output for all moves in a turn."""
-        turn_print: str = ''
-        for drone, from_hub, to_hub in drone_movements:
-            connection = self.graph.find_connection(
-                from_hub.name, to_hub.name
-            )
-            if connection is None:
-                continue
-            code = self._assign_colour_code(from_hub, to_hub, drone)
-            if to_hub.is_end and to_hub.name == 'impossible_goal':
-                label = f'[{drone.id}: {from_hub.name} - {to_hub.name}]'
-                turn_print += self._rainbow_text(label)
-            else:
-                turn_print += (
-                    f'{code}[{drone.id}: '
-                    f'{from_hub.name} - {to_hub.name}] \x1b[0m'
-                )
-        return turn_print
+    def _record_positions(self, drones: list[Drone]) -> str:
+        """Build the terminal output from each drone's current location."""
+        positions: list[str] = []
+        for drone in drones:
+            if drone.current_connection is not None:
+                connection = drone.current_connection
+                position = f'{connection.hub_a}-{connection.hub_b}'
+            elif drone.current_hub is not None:
+                position = drone.current_hub.name
+            else:
+                position = 'sin ubicación'
+            positions.append(f'[{drone.id}: {position}]')
+        return ' '.join(positions)
@@
-            drone_movements = self._execute_schedule(schedule, turns)
-            turn_print = self._record_move(drone_movements)
+            self._execute_schedule(schedule, turns)
+            turn_print = self._record_positions(self.graph.drones)
             if turn_print:
                 print(turn_print)
```

### Guardar y completar el estado de tránsito

```diff
diff --git a/src/fly_in.py b/src/fly_in.py
@@
                 if connection is None:
                     return False
+
+                if drone.current_connection is None:
+                    key = (connection.capacity_key, turn)
+                    reserved = self.reservations.get(key, 0)
+                    in_transit = sum(
+                        len(link.current_drones)
+                        for link in self.graph.connections
+                        if link.capacity_key == connection.capacity_key
+                    )
+                    if (reserved >= connection.max_link_capacity
+                            or in_transit >= connection.max_link_capacity):
+                        return False
 
                 return drone.can_move(connection, turn) is True
@@
-    def _execute_schedule(
-        self, schedule: list[tuple], turn: int
-    ) -> list[tuple[Drone, Hub, Hub]]:
-        drone_movements: list[tuple[Drone, Hub, Hub]] = []
+    def _execute_schedule(
+        self, schedule: list[tuple], turn: int
+    ) -> None:
         for action in schedule:
             drone, next_hub, t = action
-
-            if self._turn_validation(drone, next_hub, t):
-                if drone.current_hub is None:
-                    continue
-                from_hub: Hub = drone.current_hub
-                drone.path = self.path_finder.reconstruct_path(
-                    drone.current_hub, self.graph, turn, self.reservations
-                )
-                drone.move_next_hub(next_hub, t)
-
-                if drone.current_hub is None:
-                    continue
-                if drone.current_hub.name != next_hub.name:
-                    continue
-
-                drone_movements.append((drone, from_hub, next_hub))
-                self._reserve_capacity(from_hub, next_hub, turn + 1)
-
-        return drone_movements
+            if not self._turn_validation(drone, next_hub, t):
+                continue
+            if drone.current_hub is None:
+                continue
+            from_hub = drone.current_hub
+
+            if (next_hub.zone == 'restricted'
+                    and drone.current_connection is None):
+                connection = self.graph.find_connection(
+                    from_hub.name, next_hub.name
+                )
+                drone.path = [from_hub, next_hub]
+                if connection is None or not connection.enter(drone, t):
+                    continue
+                if drone in from_hub.drones:
+                    from_hub.drones.remove(drone)
+                self._reserve_capacity(from_hub, next_hub, t)
+                continue
+
+            drone.path = self.path_finder.reconstruct_path(
+                drone.current_hub, self.graph, turn, self.reservations
+            )
+            in_transit = drone.current_connection is not None
+            drone.move_next_hub(next_hub, t)
+            if (drone.current_hub is not None
+                    and drone.current_hub.name == next_hub.name
+                    and not in_transit):
+                self._reserve_capacity(from_hub, next_hub, t)
@@
-        key = (connection.capacity_key, turn)
-        if self.reservations.get(key, 0) > connection.max_linkt_capacity:
-            return False
-
         key_hub = (hub.name, turn)
```

La capacidad se valida antes de mover el dron; `_reserve_capacity()` queda
encargado de registrar el cruce. Así no se consulta el nombre incorrecto
`max_linkt_capacity`.

### Continuar hacia el destino mientras está en la conexión

```diff
diff --git a/src/planner.py b/src/planner.py
@@
         for group in groups:
             for drone in group:
+                if drone.current_connection is not None:
+                    if drone.current_hub is None:
+                        continue
+                    connection = drone.current_connection
+                    next_name = (
+                        connection.hub_b
+                        if connection.hub_a == drone.current_hub.name
+                        else connection.hub_a
+                    )
+                    schedule.append(
+                        (drone, original_hubs[next_name], turn + 1)
+                    )
+                    continue
+
                 routes: list[list[Hub]] = self.get_alt_routes(
                     drone, turn, reservations
                 )
```

Los cambios son una propuesta de implementación; no se han aplicado al código.
