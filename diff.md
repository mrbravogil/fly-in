# Diff y explicación del arreglo

## Resumen

El proyecto tenía varios problemas encadenados:

1. Importación circular entre modelos y parser.
2. Importación incorrecta de `Graph` desde el archivo equivocado.
3. `pydantic` no estaba siendo ejecutado desde el entorno virtual correcto.
4. Validación del parser demasiado estricta para el formato real de los mapas.
5. Modelos con tipos y referencias cruzadas mal definidos para Pydantic.

La solución se centró en corregir la estructura de importaciones, normalizar el entorno de ejecución y dejar los modelos compatibles con Pydantic 2.

---

## 1) Problema principal: importación circular

Al principio el código intentaba hacer cosas como:

- `config_parser.py` importaba `Graph` desde `models.models`
- `models.py` estaba declarando `Hub` y otros modelos que dependían de `Graph`

Esto creó una dependencia circular:

- `Graph` necesitaba `Hub`
- `Hub` podía depender de `Graph`
- ambos se intentaban importar entre sí antes de estar completamente definidos

### Solución

Se separaron responsabilidades:

- `Graph` quedó definido en `src/models/graph.py`
- `Hub` y `Connection` quedaron en `src/models/models.py`
- `config_parser.py` importa `Graph` desde el lugar correcto y `Hub` sólo cuando hace falta

Esto elimina la dependencia circular real y permite que Python cargue los módulos en un orden seguro.

---

## 2) Corrección de la importación incorrecta

La línea que estaba fallando era similar a esta:

```python
from .models.models import Graph, Connection
```

Pero `Graph` no existe allí; esa clase vive en:

```python
src/models/graph.py
```

### Cambio realizado

Se reescribió la importación a:

```python
from .models.graph import Graph
from .models.models import Connection, Hub
```

### Por qué era necesario

Porque el parser necesitaba crear un `Graph` real desde la configuración, y la importación estaba apuntando a un módulo que no lo contenía. Eso provocaba errores de `ImportError`.

---

## 3) Activación del entorno virtual

El proyecto cuenta con un entorno `.venv`, y ahí es donde estaba instalado `pydantic`.

El problema no era que faltara la librería, sino que no se estaba ejecutando desde el entorno del proyecto.

### Comando usado para verificar

```bash
cd /home/mr-bravo/Escritorio/portfolio/fly-in
. .venv/bin/activate
python -m src
```

### Por qué era importante

Sin activar el entorno, Python usaba el intérprete del sistema o un entorno distinto, y eso provocaba diferencias de dependencias, importaciones y comportamiento.

---

## 4) Corrección de validación del parser

El parser tenía una validación demasiado rígida para el formato real del archivo de mapa.

El archivo del juego tiene este formato:

```text
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

### Problema

El código estaba tratando `hub` y `connection` como claves únicas, cuando en realidad el formato del mapa usa múltiples entradas repetidas de esas mismas claves.

### Cambio

Se redefinió la validación para requerir solo:

- `nb_drones`
- `start_hub`
- `end_hub`

y luego se validó que existan realmente:

- `hubs`
- `connections`

### Por qué era necesario

Porque el formato de archivo del proyecto usa una lista de hubs/conexiones repetidos. Si los tratamos como claves únicas, la carga falla aunque el mapa sea válido.

---

## 5) Arreglo de parsing de hubs

El parser estaba intentando validar los hubs con una lógica insuficiente y, en algunos casos, construía valores con tipos incorrectos.

### Problemas corregidos

- un hub debía poder tener nombres como `waypoint1`, no solo letras sueltas
- las coordenadas se parseaban como enteros correctos
- los valores extra (`color`, `zone`, `max_drones`) se validaban correctamente
- no se estaban creando estructuras con listas donde deberían ir escalares

### Cambio clave

Se dejó esta forma correcta:

```python
return Hub(
    name=name,
    x=coordinates[0],
    y=coordinates[1],
    color=p_values['color'],
    zone=p_values.get('zone', 'normal'),
    max_drones=int(p_values['max_drones']) if p_values.get('max_drones') else 1,
)
```

### Por qué era necesario

Pydantic exige que los campos del modelo tengan tipos correctos. Si un `Hub` recibe listas o strings donde debería haber enteros o cadenas simples, falla en validación.

---

## 6) Arreglo del modelo `Connection`

El proyecto originalmente intentaba usar `hub_a` y `hub_b` como `Hub`, pero el contenido del archivo de configuración solo contiene nombres de hubs, como:

```text
start-waypoint1
```

Es decir, el modelo debía guardar el nombre del hub, no el objeto `Hub` completo.

### Cambio

Se quedó así:

```python
class Connection(BaseModel):
    id: str = 'C0'
    hub_a: str
    hub_b: str
    max_link_capacity: int = 0
```

### Por qué era necesario

Porque el parser crea conexiones usando strings. El modelo debe reflejar el dato real del archivo y no asumir que se le pasa un objeto completo.

---

## 7) Solución a las referencias cruzadas de Pydantic

Pydantic 2 exige que las referencias hacia adelante como `"Hub"` y `"Graph"` estén completamente resueltas cuando el modelo se crea.

### Problemas que aparecieron

- `Graph` no estaba definido completamente cuando se intentaba construirlo
- `Hub` no estaba disponible al reconstruir los modelos
- el `model_rebuild()` se estaba usando sin el orden correcto

### Solución aplicada

- se evitó reconstruir modelos demasiado pronto
- se importaron los tipos reales necesarios cuando el módulo ya estaba cargado
- se dejó el orden de definición consistente

Esto permite que Pydantic resuelva correctamente las referencias entre modelos.

---

## 8) Resultado final verificado

Tras los cambios, se ejecutó el proyecto real con el entorno activo y la aplicación arrancó correctamente.

### Verificación ejecutada

```bash
cd /home/mr-bravo/Escritorio/portfolio/fly-in
. .venv/bin/activate
python -m src
```

### Resultado observado

La salida mostró:

- banner de bienvenida
- parseo correcto del mapa
- creación de hubs
- creación de conexiones
- `Graph` completo sin errores

---

## Conclusión

El arreglo no fue un único cambio, sino una combinación de varias correcciones pequeñas pero esenciales:

- corregir rutas de importación
- activar el entorno correcto
- ajustar el parser a la estructura real del proyecto
- hacer que los modelos `pydantic` coincidan con la forma real de los datos

Todo ello permitió que el programa arrancase correctamente y que la lógica del proyecto quedara coherente con el formato de los mapas.
