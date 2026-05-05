# HAR Analytics

Herramienta de línea de comandos (CLI) escrita en Python que analiza archivos HAR (**HTTP Archive**) para generar reportes de performance interactivos en formato HTML.
Ideal para inspeccionar tiempos de respuesta de requests de red capturadas desde el DevTools del navegador, comparar endpoints, y detectar cuellos de botella.

---

## ¿Qué hace `script.py`?

El script principal orquesta un pipeline de análisis en cuatro fases:

### 1. Descubrimiento y parseo de archivos HAR
Acepta como entrada un **archivo `.har` individual** o una **carpeta** que puede contener múltiples archivos `.har` (incluyendo subcarpetas). Por cada request encontrada extrae:

- URL completa y endpoint base (sin query params)
- Parámetros OData: `$select` y `$filter`
- Método HTTP y código de estado
- Tiempos de cada fase de red: *Queueing, Connection, Request Sent, Server Response, Content Download*
- Tiempo total de la request
- Tamaño de la respuesta

### 2. Aplicación de filtros
Filtra las requests por URL usando patrones de texto o expresiones regulares. Si no se especifica ningún filtro, se incluyen todas las requests.

### 3. Cálculo de estadísticas
Agrupa las requests por URL y calcula por cada endpoint:

| Métrica | Descripción |
|---|---|
| **Count** | Número de requests |
| **Min / Max** | Tiempo mínimo y máximo |
| **Avg** | Promedio de tiempo |
| **P50 / P90 / P95 / P99** | Percentiles de tiempo de respuesta |
| **Min/Max por fase** | Tiempos de cada fase de red (Queueing, Conn, etc.) |

También calcula métricas globales sobre el total de requests filtradas.

### 4. Generación del reporte HTML
Genera un archivo HTML interactivo con:

- **Resumen general**: tabla comparativa de todos los endpoints con sus métricas clave
- **Gráfica de resumen**: barras agrupadas de Min/Max total por URL
- **Detalle por URL**: sección individual para cada endpoint con tabla completa y gráfica de tiempos Min/Max por fase de red
- Metadata del análisis: fecha, archivos procesados y filtros aplicados

---

## Instalación

### Requisitos previos
- Python 3.9+
- pip

### Instalar dependencias

Las dependencias principales del proyecto son:

```
plotly
pandas
numpy
```

## Uso básico

Ejecuta el script desde la carpeta `app/`:

```bash
# Analizar un archivo HAR individual
python script.py ruta/al/archivo.har

# Analizar todos los .har de una carpeta (y subcarpetas)
python script.py ruta/a/la/carpeta/
```

El reporte se guarda por defecto como `report.html` en el directorio actual.

---

## Opciones disponibles

```
python script.py <input> [--filter PATRON] [--output RUTA]
```

| Argumento | Descripción | Valor por defecto |
|---|---|---|
| `input` | Ruta al archivo `.har` o carpeta con archivos `.har` | *(requerido)* |
| `--filter` | Filtro de URL (substring o regex). Puede usarse múltiples veces | Sin filtro (incluye todo) |
| `--output` | Ruta del archivo HTML de salida | `report.html` |

---

## Filtros

El argumento `--filter` permite incluir **únicamente las requests cuya URL contenga el patrón indicado**. Soporta tanto texto plano como expresiones regulares.

### Filtro por substring (texto)

```bash
# Solo requests que contengan "api/products" en la URL
python script.py ./hars/ --filter "api/products"
```

### Filtro por expresión regular (regex)

```bash
# Solo requests a endpoints que terminen en /orders o /items
python script.py ./hars/ --filter "/(orders|items)$"
```

### Múltiples filtros

Puedes encadenar varios `--filter`. Se incluirá una request si coincide con **al menos uno** de los filtros (lógica OR):

```bash
python script.py ./hars/ --filter "api/products" --filter "api/customers"
```

---

## Ejemplos completos

```bash
# Reporte de todos los endpoints en session.har
python script.py session.har

# Filtrar solo requests de inventario y guardar en un nombre personalizado
python script.py ./capturas/ --filter "inventory" --output reporte_inventario.html

# Filtrar endpoints OData con regex y guardar en subdirectorio
python script.py ./hars/ --filter "EntitySet\(\d+\)" --output ./reportes/odata.html

# Combinar múltiples filtros
python script.py ./hars/ --filter "api/v2" --filter "api/v3" --output reporte_v2_v3.html
```

---

## Estructura del proyecto

```
HAR-Analitics/
├── app/
│   ├── script.py        # Punto de entrada principal (CLI)
│   ├── har_reader.py    # Descubrimiento y parseo de archivos HAR
│   ├── filters.py       # Lógica de filtrado de requests por URL
│   ├── stats.py         # Cálculo de métricas y percentiles
│   └── report_html.py   # Generación del reporte HTML con gráficas
└── libs.txt             # Dependencias del proyecto
```

---

## ¿Cómo obtener un archivo HAR?

1. Abre las **DevTools** de tu navegador (F12)
2. Ve a la pestaña **Network**
3. Realiza las acciones que quieres capturar
4. Clic derecho sobre cualquier request → **Save all as HAR with content**

---

## Notas

- Las URLs son **decodificadas** automáticamente (URL decode) antes de procesarse.
- Los endpoints se **ordenan alfabéticamente** en el reporte para facilitar la comparación.
- Los tiempos negativos reportados por el navegador (valores `-1`) se normalizan a `0`.
- El reporte HTML generado es **autocontenido** (no requiere servidor, se abre directo en el navegador).
