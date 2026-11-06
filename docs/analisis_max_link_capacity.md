# Investigación: `max_link_capacity`

## Conclusión

El parser lee el valor y los cambios locales en `Fly_in` ya corrigen dos fallos
de reservas: guardan el enlace antes de mover el dron y registran la ocupación
por turno. Las pruebas observadas confirman que el límite se aplica a cruces en
la misma dirección.

Queda un fallo si `max_link_capacity` se refiere al enlace bidireccional como
una sola conexión: el grafo representa cada sentido con un objeto `Connection`
distinto, con contadores independientes. Por ello, un cruce en un sentido no
consume capacidad del sentido contrario.

## Recorrido del valor

1. [`ConfigParser._parse_connection`](../src/config_parser.py#L285) convierte
   `max_link_capacity` a entero y lo asigna a `Connection`.
2. [`Graph._bidirectional_coon`](../src/models/graph.py#L93) copia el valor al
   enlace en sentido inverso.
3. Al ejecutar un movimiento, [`Fly_in._turn_validation`](../src/fly_in.py#L99)
   delega la comprobación en `Drone.can_move`, que llama a
   [`Connection.has_capacity`](../src/models/models.py#L117).
4. Si el movimiento se completa,
   [`Fly_in._reserve_capacity`](../src/fly_in.py#L196) conserva el origen antes
   de mover el dron y registra la reserva usando el identificador de la
   conexión direccional.

## Causas encontradas

- `Connection.has_capacity()` consulta las reservas del turno y los drones
  presentes en ese objeto `Connection`. La simulación no utiliza
  `Connection.enter()` para registrar cruces; por eso depende de
  `reserve_turn()`, que sí se llama tras cada movimiento completado.
- [`Graph._bidirectional_coon`](../src/models/graph.py#L96) crea otro objeto
  `Connection` para el sentido inverso. Aunque copia `max_link_capacity`, no
  comparte `turn_capacity`. Así, una reserva en `waypoint1-waypoint2` no afecta
  a `waypoint2-waypoint1`.
- La reserva en `Fly_in` está indexada por `(connection.id, turn)`. Como los
  sentidos tienen identificadores distintos, esa clave tampoco puede
  representar por sí sola el límite compartido del enlace.
- `Planner.validate_move()` consulta reservas de conexión, pero no es invocado
  por `Planner.plan()` en el flujo actual. La validación efectiva de cada
  movimiento ocurre en `_turn_validation()` y `Drone.can_move()`.

## Reproducción observada

Se parseó `maps/easy/01_linear_path.txt` y se cambió la capacidad de los dos
sentidos solo en memoria. Al ejecutar dos drones, se observó:

```text
capacidad=1, cruces por turno en waypoint1-waypoint2=[1, 1]
capacidad=2, cruces por turno en waypoint1-waypoint2=[2]
```

Esto confirma que el límite actualizado funciona en un solo sentido. En una
prueba directa adicional, se reservó un turno en el sentido de ida: ese objeto
informó que ya no tenía capacidad para `1`, mientras que el objeto del sentido
inverso todavía informó que sí tenía capacidad. Los contadores son
independientes. El mapa local no se modificó para estas pruebas.

## Diff adicional propuesto (no aplicado)

El diff anterior ya está reflejado en los cambios locales de
`src/fly_in.py` y `src/models/models.py`. Para compartir el límite entre ambos
sentidos, cada conexión necesita una clave canónica, independiente de la
dirección, y la validación y reserva deben usarla. Por ejemplo:

```diff
diff --git a/src/models/models.py b/src/models/models.py
@@
     turn_capacity: dict[int, int] = Field(default_factory=dict)
     max_link_capacity: int = 9999
+
+    @property
+    def capacity_key(self) -> tuple[str, str]:
+        """Return the undirected identity of this connection."""
+        if self.hub_a < self.hub_b:
+            return self.hub_a, self.hub_b
+        return self.hub_b, self.hub_a
diff --git a/src/fly_in.py b/src/fly_in.py
@@
         connection = self.graph.find_connection(drone.current_hub.name,
                                                 next_hub.name)
         if connection is None:
             return False
+
+        key = (connection.capacity_key, turn)
+        if self.reservations.get(key, 0) >= connection.max_link_capacity:
+            return False
 
         return drone.can_move(connection, turn) is True
@@
-        key_conn = (connection.id, turn)
+        key_conn = (connection.capacity_key, turn)
         self.reservations[key_conn] = self.reservations.get(key_conn, 0) + 1
         connection.reserve_turn(turn)
diff --git a/src/planner.py b/src/planner.py
@@
-            conn_occupation = reservations.get((connection.id, turn), 0)
+            conn_occupation = reservations.get(
+                (connection.capacity_key, turn), 0
+            )
             if conn_occupation >= connection.max_link_capacity:
                 return False
```

La comprobación en `_turn_validation()` es necesaria porque es la ruta que
autoriza los movimientos en la simulación actual; cambiar solo la clave de
reserva no bastaría, ya que `Drone.can_move()` consulta el contador del objeto
direccional. La consulta en `Planner.validate_move()` mantiene coherente ese
validador si se conecta al planificador en el futuro.

## Nota de validación

El parser actualmente rechaza capacidades negativas, pero acepta `0`, aunque
su mensaje de error dice que el valor debe ser positivo. Es un problema de
validación separado del conteo bidireccional descrito arriba.
