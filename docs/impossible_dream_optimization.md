# Análisis del código y mejora para resolver “The Impossible Dream” en 45 turnos o menos

## 1) Diagnóstico rápido

La implementación actual resuelve el mapa más difícil en 115 turnos en la ejecución real, no en 45. El problema principal no es el cálculo del camino en sí, sino la forma en que se toma la decisión en cada turno:

- cada dron recalcula una ruta individual desde su posición actual hacia el objetivo,
- todos intentan seguir el mismo corredor principal,
- el sistema no reserva capacidad ni coordina la salida en oleadas,
- la frontera de capacidad (`max_drones`, `max_link_capacity`) se comprueba solo de forma local y reactiva,
- los hubs restringidos y los nodos de convergencia se convierten en cuellos de botella porque no hay planificación global del tráfico.

La evidencia actual es clara: al ejecutar el mapa Challenger con el algoritmo existente, la simulación llega a:

- `TURNS: 115`

Esto está muy por encima del objetivo de 45 y muestra que la estrategia actual es una cola reactiva, no un planificador de flujo.

---

## 2) Qué hace el código actual

### 2.1 Pathfinding

En `src/pathfinding.py` se usa un Dijkstra sencillo para calcular la ruta más corta desde el hub actual hasta el final del grafo.

Problemas:

1. La ruta se calcula sin tener en cuenta la ocupación real del mapa.
2. La capacidad de cada enlace y cada hub no forma parte del coste del camino.
3. La ruta es reforzada solo por pesos de zona (`normal`, `restricted`, `priority`), pero no por congestión ni por tiempo de espera.
4. El método `reconstruct_path()` vuelve a calcular la ruta completo para cada dron y cada turno, con la misma visión del mapa.

Esto se ve muy bien en el grafo del mapa Challenger: hay varios cuellos de botella serializados en secuencia:

- `start -> gate_hell1 -> gate_hell2 -> ... -> gate_hell5`
- `micro_gate1 -> micro_gate2 -> micro_gate3`
- `false_hope1 -> false_hope2 -> false_hope3`
- `final_merge -> final_torture1 -> ... -> impossible_goal`

El problema es que todos los drones quieren pasar por esos puntos al mismo tiempo, pero el algoritmo no decide quién pasa primero ni en qué turno se libera cada tramo.

### 2.2 Simulación central

En `src/fly_in.py` el bucle principal hace esto:

- recorre cada dron,
- le asigna una ruta según su hub actual,
- comprobar si el siguiente hub es válido,
- mover solo si hay capacidad disponible.

Esto produce una lógica de tipo “greedy, turno a turno”.

Es suficiente para mapas fáciles, pero falla en mapas donde la optimización global pesa más que la decisión local. En “Impossible Dream” se necesita un planificador que resuelva:

- quién entra primero a cada cuello de botella,
- cuál es el juego de rutas que minimiza colas,
- qué drones deben esperar aunque tenga un coste local más alto,
- cómo se aprovechan zonas priority sin bloquear la convergencia final.

### 2.3 Estado de los drones

En `src/models/models.py` el dron tiene:

- `current_hub`
- `current_connection`
- `status` (`normal` / `restricted`)
- `path`

La lógica de movimiento está bien para un modelo simple, pero es insuficiente para una planificación de flujo por oleadas. El coste de un movimiento se considera solo en el instante actual, no como un recurso compartido a lo largo del tiempo.

---

## 3) Problemas concretos del mapa “Impossible Dream”

El mapa está diseñado para explotar varios puntos que el código actual no gestiona:

### 3.1 Cuellos de botella serializados

Hay varias zonas donde la capacidad es 1 o muy baja:

- `gate_hell1` a `gate_hell5` tienen `max_drones=1`
- `micro_gate1`, `micro_gate2`, `micro_gate3` también están limitados
- `conv_restricted1` a `conv_restricted9` tienen zonas restringidas con capacidad 1
- la ruta final `final_merge -> final_torture1 -> ... -> impossible_goal` tiene varias colas en serie

Con 25 drones, si todos avanzan “a lo loco” en la misma dirección, la cola crece y se repite cada turno. El algoritmo actual no aplica un criterio de prioridad ni de ventana de salida.

### 3.2 Rutas alternativas sin elección inteligente

El mapa tiene caminos muertos (`maze_dead_a`, `maze_dead_b`) y rutas que parecen buenas pero llevan a trampas (`priority_trap1`, `priority_trap2`, etc.).

El algoritmo actual solo usa la ruta más corta según pesos, pero no tiene:

- penalización por “peligro” o congestión,
- separación de rutas por grupo de drones,
- selección de ramales según el estado real del tráfico.

### 3.3 Restricción temporal

Las zonas `restricted` tienen costo de movimiento extra y requieren manejar su estado. El código hace esto localmente, pero no entiende que un dron puede estar “bloqueado” en una zona restringida durante más de un turno porque el siguiente paso depende del acceso a la ruta de salida.

Eso produce esperas artificiales y valoraciones incorrectas del tiempo real de cada dron.

---

## 4) Qué hay que cambiar para bajar a 45 turnos

La solución no es “mejorar Dijkstra”. La solución es cambiar el modelo de análisis de una ruta individual a un problema de planificación de flujo y sincronización.

### 4.1 Reemplazar la lógica reactiva por una planificación global

Necesitamos un planificador con estas responsabilidades:

1. Calcular una ruta candidata para cada dron o grupo de drones.
2. Estimar el tiempo de llegada a cada hub.
3. Reservar capacidad por turno en cada hub y conexión.
4. Decidir qué drones esperan en la salida para evitar bloquear la colas internas.
5. Eliminar la “competencia” por el mismo cuello de botella.

Esto implica pasar de un enfoque tipo:

- “mueve los drones que pueden moverse ahora”

A otro tipo:

- “asigna cada dron a un slot temporal y un camino preferido para minimizar el tiempo total de llegada”.

### 4.2 Introducir un grafo con tiempo

La idea clave es usar un grafo expandido en el tiempo.

En lugar de modelar solo `(hub)`, se modela `(hub, turno)`. Así una ruta ya no es solo una secuencia de nodos, sino una secuencia de estados temporales:

- estado: `(hub_actual, t)`
- acción: mover a `(siguiente_hub, t + 1)`
- restricción: el hub y la conexión deben tener disponibilidad en ese turno

Esto permite evitar conflictos reales del tipo:

- “dos drones intentando entrar al mismo hub en el mismo turno”,
- “tres drones intentando cruzar la misma conexión simultáneamente”,
- “un dron se queda bloqueado porque otro ya ha reservado ese slot”.

### 4.3 Aplicar reserva por capacidad y prioridad por grupos

Para el mapa Challenger, conviene separar los 25 drones en oleadas:

- Grupo A: drones destinados a la rama rápida y limpia
- Grupo B: drones que deben pasar por rutas de reserva o de bloqueo
- Grupo C: drones que esperan en nodos previos para no saturar el paso final

La regla práctica es:

- entrar a `gate_hell1..5` en pequeñas oleadas,
- no disparar 25 drones a la vez,
- reservar capacidad en cada nodo de convergencia antes de avanzar,
- empujar primero los drones con mayor “urgencia” de llegada o menor flexibilidad de ruta.

Esto reduce el fenómeno de “todos quieren usar la misma ruta y se quedan bloqueados en una cola infinita”.

### 4.4 Añadir penalización por congestionamiento

La ruta no debería basarse solo en peso del nodo, sino también en una función como esta:

- `cost = distancia + alpha * congestion_estimada + beta * riesgo_de_trampa + gamma * espera_esperada`

Esto hace que un dron elija un camino menos directo si evita un cuello de botella que ya está saturado.

En el mapa, la diferencia entre:

- una rama aparentemente “rápida” (`false_hope1 -> false_hope2 -> false_hope3`)
- y una rama con más capacidad de desembarque o menos bloqueo

solo se ve si el costo incluye la carga real del tráfico.

---

## 5) Mejora arquitectónica recomendada

### 5.1 Nueva capa: `Planner`

Añadir una clase separada, por ejemplo:

- `Planner`
- `TrafficReservation`
- `RouteAssignment`
- `TimeExpandedGraph`

Responsabilidades:

- calcular rutas con costes dinámicos,
- decidir la ventana de salida por dron,
- asignar rutas con reservas de capacidad,
- validar el siguiente paso antes de mover.

La clase `Fly_in` no debería decidir por cada dron individualmente en cada turno sin contexto. Debe consultar al planner primero.

### 5.2 Separar ruta y programación

Hoy `PathFinder` devuelve una ruta más corta, pero no sabe nada del tiempo ni del estado del sistema. Conviene dividir la responsabilidad en dos niveles:

- `PathFinder`: calcula rutas base sobre el grafo estático
- `Planner`: decide la ruta efectiva + la ventana temporal + los slots reservados

Es decir, no solo “qué camino sigue”, sino “cuándo lo sigue y bajo qué reserva”.

### 5.3 Añadir reservas por turno

Una estructura tipo:

```python
reservations = {
    ('hub_name', turn): 0,
    ('connection_id', turn): 0,
}
```

La validación del movimiento pasa a ser:

```python
if hub_capacity_available(hub, turn) and connection_capacity_available(conn, turn):
    reserve_slot(...)
else:
    wait_or_choose_alternative_route(...)
```

Esto rompe la lógica local actual y sustituye la cola reactiva por programación real.

---

## 6) Estrategia concreta para “Impossible Dream”

### 6.1 Fase 1: preparar la entrada

La zona inicial es brutal: hay 25 drones entrando en una secuencia de 5 puertas con capacidad 1.

Para llegar a 45 turnos, no se puede disparar a todos a la vez. La estrategia debería ser:

- tomar 5 drones por oleada,
- mandar cada oleada a una de las puertas según el flujo disponible,
- dejar que los siguientes esperen en `start` o en tránsito corto antes de entrar al cuello de botella.

No es necesario que todos avancen al mismo ritmo. El objetivo es saturar cada paso sin generarse bloqueos en cascada.

### 6.2 Fase 2: evitar trampas y no preferir rutas “bonitas” a costa de la cola

Aunque `priority` parece una zona buena, en este mapa muchas rutas priority llevan a trampas y a peores convergencias. Por eso la heurística actual debería cambiar:

- `priority` ya no tiene prioridad absoluta,
- la prioridad debe depender del estado de congestión del siguiente segmento,
- si una ruta priority está saturada, el planificador la desactiva y desplaza el dron a una ruta alternativa con menos bloqueo.

### 6.3 Fase 3: reservar el final antes que el medio

El cuello de botella real está en la convergencia final: `final_merge -> final_torture1 -> ... -> impossible_goal`.

La clave es reservar capacidad en esa zona con adelanto. Si el planner deja que los drones arriben sin control, la cola se acumula y los turnos se disparan.

La regla debe ser:

- cada dron debe saber si la última sección está libre antes de entrar a la fase anterior,
- si no lo está, debe quedarse en un punto intermedio y agruparse con otros drones del mismo rango,
- esto evita que toda la lista colapse en la misma zona final.

### 6.4 Fase 4: usar turns de espera como parte del plan

La mejora no consiste en “no esperar jamás”; consiste en esperar donde el coste es bajo y el beneficio es alto.

Por ejemplo:

- un dron puede esperar en `start` o en `micro_gate1` si eso evita que toda la ola choque más tarde en `final_merge`.

En una cola de 25 drones, un retraso pequeño en la entrada suele traducirse en una mejora grande en el tiempo total de finalización.

---

## 7) Pseudocódigo recomendado

```python
class Planner:
    def __init__(self, graph):
        self.graph = graph

    def plan(self, drones):
        # 1. Repartir drones por flujo y urgencia
        groups = self.group_by_path_flexibility(drones)

        # 2. Calcular rutas base con coste dinámico
        routes = {
            drone.id: self.compute_route_with_congestion_penalty(drone)
            for drone in drones
        }

        # 3. Preparar reservas temporales
        reservations = {}

        # 4. Generar un plan por turnos
        schedule = []
        for turn in range(0, 80):
            actions = []
            for drone in self.order_by_urgency(groups):
                if self.is_ready(drone, turn, reservations):
                    next_hub = self.next_hub_for_turn(drone, turn, reservations)
                    if next_hub is not None:
                        actions.append((drone, next_hub, turn + 1))
                        self.reserve(drone, next_hub, turn + 1, reservations)
            schedule.append(actions)

            if self.all_finished(drones):
                return schedule

        raise RuntimeError("No feasible schedule found")
```

La diferencia clave es que aquí el sistema decide el movimiento en función del plan y no solo de la ruta local.

---

## 8) Cambios concretos sugeridos en el código

### En `src/pathfinding.py`

- cambiar la lógica para calcular costes con congestión,
- añadir una función que devuelva varias opciones de ruta, no solo una,
- separar “ruta base” y “ruta efectiva” de una misma ruta.

### En `src/fly_in.py`

- quitar la lógica de “mover todo lo que pueda inmediatamente”,
- introducir una fase de planificación antes del movimiento,
- mantener una cola de espera por tráfico y capacidad,
- permitir que un dron espere un turno si el siguiente tramo está saturado.

### En `src/models/models.py`

- añadir un dato de `reserved_turns` o `reservation` al dron/conexión,
- ampliar `Connection` para saber cuánta capacidad está ocupada en cada turno,
- separar las restricciones de hub y conexión en un estado del tiempo, no solo del estado actual.

### En `src/models/graph.py`

- añadir una representación de capacidad por turno,
- modelar `max_link_capacity` y `max_drones` como reservas temporales,
- incorporar un `time_step` o `turn` al grafo para identificar cuellos de botella reales.

---

## 9) Por qué esto puede bajar de 115 a 45

La mejora es posible porque el mapa no es “imposible” en sentido absoluto: es un problema de sincronización y de flujo. El código actual desperdicia muchísimos turnos en:

- colas duplicadas,
- rutas desordenadas,
- decisiones locales sin visión global,
- ausencia de planificación de la salida a cada paso crítico.

Cuando se introduce reserva y coordinación, el tiempo total cae porque los drones dejan de competir por el mismo hueco al mismo tiempo.

La diferencia entre 115 y 45 no viene de un micro-optimización de Dijkstra; viene de cambiar la estrategia de:

- “ruta individual”

por:

- “programación de flujo global con reservas temporales”.

---

## 10) Recomendación final

Si el objetivo es resolver “The Impossible Dream” en 45 turnos o menos, la mejora más importante es la siguiente:

> no buscar la ruta más corta por dron, sino encontrar el plan de movimiento más eficiente para todo el conjunto de drones.

En otras palabras:

- `route optimization` + `capacity reservation` + `turn-based scheduling` = la diferencia entre un algoritmo que “trata de llegar” y uno que “sabe cuándo y por dónde entrar”.

Con una estructura así, la simulación tiene muchas más probabilidades de acercarse al objetivo de 45 turnos sin caer en las colas cíclicas del mapa actual.

---

## 11) Resumen en una frase

El proyecto actual funciona bien para mapas simples, pero “Impossible Dream” exige un planificador de tráfico en vez de un Dijkstra reactivo; la clave está en coordinar capas, reservar capacidad por turno y retrasar selectivamente ciertos drones para evitar colapsos en los cuellos de botella.
