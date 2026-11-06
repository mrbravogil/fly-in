# Investigación: `max_link_capacity`

## Conclusión

El valor se parsea y llega al objeto `Connection`, pero el simulador no lo
aplica correctamente al mover drones. El problema principal está en el
seguimiento de la capacidad por turno, no en la lectura del archivo de mapa.

## Recorrido del valor

1. [`ConfigParser._parse_connection`](../src/config_parser.py#L285) convierte
   `max_link_capacity` a entero y lo asigna a `Connection`.
2. [`Graph._bidirectional_coon`](../src/models/graph.py#L93) copia el valor al
   enlace en sentido inverso.
3. Al ejecutar un movimiento, [`Fly_in._turn_validation`](../src/fly_in.py#L99)
   delega la comprobación en `Drone.can_move`, que llama a
   [`Connection.has_capacity`](../src/models/models.py#L117).
4. Si el movimiento se completa, [`Fly_in._reserve_capacity`](../src/fly_in.py#L196)
   debería reservar el enlace para ese turno, pero la búsqueda del enlace usa
   extremos incorrectos.

## Causas encontradas

- `Connection.has_capacity()` reemplaza `turn_capacity[turn]` con
  `len(current_drones)` cada vez que se consulta. Así descarta las reservas
  hechas con `reserve_turn()` en vez de contar contra ellas. Además, la
  simulación mueve cada dron de forma inmediata y no llama a
  `Connection.enter()`, por lo que `current_drones` no refleja los cruces
  realizados en el turno. La corrección propuesta conserva ambas
  comprobaciones: las reservas del turno y los drones que estén actualmente
  en el enlace.
- `_reserve_capacity()` se llama después de `drone.move_next_hub()`. Para
  entonces `drone.current_hub` ya es el destino; buscar una conexión desde ese
  destino hasta el mismo `hub` no encuentra el enlace, y la función retorna
  antes de registrar ninguna reserva.
- La reserva de conexión en `Fly_in` usa `(hub.name, turn)`, pero
  `Planner.validate_move()` consulta `(connection.id, turn)`. Aunque ese
  validador no es invocado desde `Planner.plan()`, las claves inconsistentes
  también impiden que esas reservas se compartan correctamente.

## Reproducción observada

Se parseó `maps/easy/01_linear_path.txt`, se cambió a `1` la capacidad del
enlace `waypoint1-waypoint2` solo en memoria y se ejecutó el mapa. El resultado
fue:

```text
[D1: waypoint1 - waypoint2] [D2: waypoint1 - waypoint2]
```

Ambos drones cruzaron el enlace en el mismo turno pese a que su capacidad era
`1`. El mapa local declara capacidad `2`; no se modificó para esta prueba.

## Diff propuesto (no aplicado)

El cambio siguiente conserva el origen antes de mover el dron, registra la
reserva bajo el identificador de la conexión y consulta las reservas por turno
en `Connection.has_capacity()`.

```diff
diff --git a/src/models/models.py b/src/models/models.py
@@
     def has_capacity(self, turn: int) -> bool:
         """Return True when the connection still has room for this turn."""
-        self.turn_capacity[turn] = len(self.current_drones)
-        return self.turn_capacity[turn] < self.max_link_capacity
+        return (
+            self.turn_capacity.get(turn, 0) < self.max_link_capacity
+            and len(self.current_drones) < self.max_link_capacity
+        )
diff --git a/src/fly_in.py b/src/fly_in.py
@@
                 from_hub: Hub = drone.current_hub
                 drone.path = self.path_finder.reconstruct_path(
                     drone.current_hub, self.graph, turn, self.reservations
                 )
                 drone.move_next_hub(next_hub, t)
@@
-                self._reserve_capacity(drone, next_hub, turn + 1)
+                self._reserve_capacity(from_hub, next_hub, turn + 1)
@@
-    def _reserve_capacity(self, drone: Drone, hub: Hub, turn: int) -> None:
+    def _reserve_capacity(self, from_hub: Hub, hub: Hub,
+                          turn: int) -> None:
         """Reserve the destination hub and connection for this turn."""
-        if drone.current_hub is None:
-            return
-
-        connection = self.graph.find_connection(drone.current_hub.name,
-                                                hub.name)
+        connection = self.graph.find_connection(from_hub.name, hub.name)
         if connection is None:
             return
@@
-        key_conn = (hub.name, turn)
+        key_conn = (connection.id, turn)
         self.reservations[key_conn] = self.reservations.get(key_conn, 0) + 1
         connection.reserve_turn(turn)
```

En este diff, la línea de `from_hub` dentro de `_execute_schedule()` ya existe:
se muestra como contexto para dejar claro que debe conservarse y usarse al
reservar.

## Nota de validación

El parser actualmente rechaza capacidades negativas, pero acepta `0`, aunque
su mensaje de error dice que el valor debe ser positivo. Esto es un problema de
validación separado: no explica por qué una capacidad positiva como `1` permite
varios cruces en el mismo turno.
