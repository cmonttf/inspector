# Inspector

Inspector es una herramienta de línea de comandos en Python orientada a analizar proyectos de software, especialmente proyectos PHP legacy o mixtos. El objetivo es entregar, en una sola ejecución, un resumen útil del proyecto: conteo de archivos por extensión, detección de framework PHP, identificación de Kendo, dependencias externas del servidor y uso de funciones OCI obsoletas.

## Objetivo

El proyecto está pensado para inspeccionar código fuente de forma rápida sin depender de la ejecución del sistema objetivo. La herramienta usa patrones de archivos, estructura del proyecto y análisis estático de contenido para inferir tecnologías y riesgos comunes; este tipo de fingerprinting tecnológico es una práctica habitual para clasificar frameworks y componentes de una aplicación.

## Funcionalidades

- Conteo de archivos por extensión, respetando `.gitignore` cuando el directorio es un repositorio Git.
- Detección de proyectos PHP y clasificación entre PHP puro o framework PHP.
- Detección de Laravel y CodeIgniter mediante estructura de carpetas, archivos característicos y, cuando existe, `composer.json`.
- Detección de Kendo UI basada en evidencias fuertes como assets, namespace e inicializaciones específicas, evitando falsos positivos por atributos genéricos como `data-role`, que también son usados por jQuery Mobile.
- Detección de dependencias externas al proyecto, como `include` absolutos, extensiones PHP declaradas y uso real de comandos del sistema.
- Detección de aliases y funciones OCI8 obsoletas o deprecadas, como `ociparse`, `ocilogon` y `ocifetchinto`.

## Estructura del proyecto

Una estructura recomendada para el paquete es la siguiente:

```text
inspector/
├── __init__.py
├── cli.py
├── contado.py
├── inspector.py
├── models.py
├── utils.py
└── detectors/
    ├── __init__.py
    ├── framework_detector.py
    ├── kendo_detector.py
    ├── oci_deprecated_detector.py
    ├── php_detector.py
    └── server_dependencies_detector.py
```

### Responsabilidades

| Archivo | Responsabilidad |
|---|---|
| `cli.py` | Punto de entrada CLI, parseo de argumentos y salida en consola. |
| `contado.py` | Conteo de archivos por extensión y formateo del resultado. |
| `inspector.py` | Orquestación de detectores y construcción del resultado final. |
| `utils.py` | Utilidades compartidas: lectura de archivos, JSON, regex y recolección de archivos. |
| `models.py` | Modelos estructurados para resultados y evidencias. |
| `detectors/*.py` | Detectores especializados por tecnología o riesgo. |

## Requisitos

- Python 3.9 o superior para una base compatible con servidores Linux comunes; si se usan anotaciones modernas como `X | None`, eso requiere Python 3.10+, por lo que para compatibilidad amplia conviene mantener `Optional[...]` y tipos de `typing` clásicos.
- Acceso de lectura al directorio del proyecto a inspeccionar.
- Git instalado si se quiere respetar `.gitignore` usando `git ls-files`; en ausencia de Git, la herramienta puede caer a un recorrido recursivo convencional del árbol de archivos.

## Instalación

Clonar o copiar el paquete dentro de un directorio de trabajo y ejecutar desde la carpeta padre del paquete.

```bash
cd /ruta/padre
python3 -m inspector.cli /ruta/proyecto
```

Si el sistema no expone el comando `python`, es normal usar `python3`; en sistemas Unix-like el comando `python` puede no existir o no estar vinculado por defecto a Python 3.[16][17]

## Uso

### Análisis completo

Este comando ejecuta el flujo completo: contador de archivos + detectores.

```bash
python3 -m inspector.cli proyecto
```

### Solo contador

```bash
python3 -m inspector.cli count proyecto
```

### Solo inspección

```bash
python3 -m inspector.cli inspect proyecto
```

### Salida JSON

```bash
python3 -m inspector.cli proyecto --json
```

El uso de subcomandos en `argparse` es una forma estándar de construir CLIs extensibles, y también permite mantener un modo por defecto para el análisis completo cuando no se especifica subcomando.

## Qué detecta

### 1. Conteo de archivos

Cuenta archivos válidos por extensión considerando extensiones simples y compuestas, por ejemplo `.blade.php`, `.env` y otras variantes especiales. Cuando el proyecto está bajo Git, se apoya en `git ls-files --cached --others --exclude-standard` para respetar exclusiones estándar del repositorio.[11]

### 2. Framework PHP

La herramienta busca señales típicas de frameworks PHP:

- Laravel: `artisan`, `bootstrap/app.php`, `routes/`, dependencia `laravel/framework` y versión en `composer.lock` o archivos internos del framework.
- CodeIgniter 3: `application/config/config.php`, `system/core/CodeIgniter.php` y estructura clásica del framework.
- CodeIgniter 4: `spark`, `app/Config`, `codeigniter4/framework` y estructura moderna del framework.

### 3. PHP puro

Inspector distingue entre “usa PHP” y “es PHP puro”. Si se detecta un framework PHP, el proyecto no debe clasificarse como PHP puro, aunque obviamente siga siendo un proyecto escrito en PHP.

### 4. Kendo UI

La detección de Kendo se basa en señales fuertes como:

- CDN oficial de Telerik/Kendo.
- archivos JS/CSS de Kendo.
- llamadas como `kendoGrid()`.
- namespace `kendo.ui`.

No conviene usar `data-role="..."` como evidencia suficiente, porque jQuery Mobile también basa su marcado en `data-role`, lo que genera falsos positivos.

### 5. Dependencias del servidor

Se reportan como dependencias relevantes:

- `include` o `require` con rutas absolutas fuera del proyecto.
- extensiones PHP declaradas en Composer como `ext-*`.
- uso real de comandos del sistema mediante `exec`, `system`, `shell_exec` o similares.

Esto permite distinguir entre librerías realmente externas al proyecto y coincidencias accidentales en texto o comentarios.

### 6. OCI obsoleto

Se detectan aliases antiguos de OCI8, como `ociparse`, `ociexecute`, `ocilogon` y `ocifetchinto`. El manual de PHP documenta estos aliases obsoletos y recomienda migrar a funciones `oci_*` modernas o a variantes nuevas de fetch según el caso.

## Ejemplo de salida

```text
================================================================
Proyecto           : /var/www/html/private/apps/proyecto
Archivos analizados: 1243
================================================================

php_puro
--------
Detectado : No
Confianza : media
Datos:
  - usa_php: True
  - php_puro: False
  - framework_detectado: codeigniter3

framework_php
-------------
Detectado : Sí
Confianza : media
Datos:
  - framework: codeigniter3
  - framework_detectado: True
```

## Diseño y criterios

El diseño del proyecto favorece separación de responsabilidades: cada detector resuelve un problema acotado y el orquestador compone el resultado final. Este enfoque facilita mantener reglas específicas, reducir falsos positivos y agregar nuevos detectores sin romper el resto del sistema.

Algunas decisiones importantes del proyecto:

- Evitar que “usa PHP” se interprete como “PHP puro”.
- Exigir evidencias fuertes para detectar Kendo, para no confundirlo con jQuery Mobile.
- Separar dependencias externas del proyecto, extensiones PHP y binarios del sistema para reducir ruido.
- Mantener compatibilidad con Python 3.9 para facilitar despliegue en servidores legacy.

## Posibles mejoras

- Detectar más frameworks PHP o CMS, por ejemplo Symfony, Yii, CakePHP o WordPress.
- Detectar stack frontend adicional, como Bootstrap, Vue, React, jQuery o DataTables.
- Añadir exportación a CSV o Markdown.
- Añadir exclusión configurable de carpetas como `vendor`, `node_modules`, `demo`, `examples` o `tests` para reducir falsos positivos.
- Agregar severidad por hallazgo y recomendaciones automáticas de migración para OCI legacy o dependencias externas críticas.

## Licencia y uso interno

Este proyecto está orientado a análisis interno, auditoría técnica y documentación de aplicaciones existentes. También puede servir como apoyo en procesos de modernización, inventario tecnológico o estimación de deuda técnica.