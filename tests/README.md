# Pruebas de la Aplicación

Esta carpeta contiene scripts de prueba de integración para cada paso del pipeline de automatización de SECOP II, así como utilidades para validar componentes individuales.

## Pipeline Completo

| Paso | Archivo | Page Object | Columna GSheets |
|------|---------|-------------|-----------------|
| **Paso 1** | `test_creacion_proceso.py` | `CreacionProcesoPage` | `Proceso 1` |
| **Paso 2** | `test_informacion_general.py` | `InformacionGeneralPage` | `Proceso 2` |
| **Paso 3** | `test_configuracion.py` | `ConfiguracionPage` | `Proceso 3` |
| **Paso 4** | `test_cuestionario.py` | `CuestionarioPage` | `Proceso 4` |
| **Paso 5** | `test_documentos.py` | `DocumentosPage` + `PublicacionPage` | `Proceso 5` |

## Utilidades

- `test_gsheets.py`: Valida la conexión a Google Sheets y la descarga de datos.
- `test_login.py`: Valida el login aislado en SECOP II.

## ¿Cómo ejecutar los tests?

Para los scripts de prueba que interactúan con el archivo `env` de la raíz, así como credenciales relativas (`client_sheet.json`), lo más recomendable es **ejecutar los scripts estando en la carpeta raíz del proyecto**, no desde esta carpeta `tests/`.

### Ejecución secuencial del pipeline

```bash
# Desde la raíz del proyecto: automatizacionsecop2-main/

# Paso 1: Creación del proceso
venv\Scripts\python tests\test_creacion_proceso.py

# Paso 2: Información general
venv\Scripts\python tests\test_informacion_general.py

# Paso 3: Configuración del proceso
venv\Scripts\python tests\test_configuracion.py

# Paso 4: Cuestionario
venv\Scripts\python tests\test_cuestionario.py

# Paso 5: Documentos y publicación
venv\Scripts\python tests\test_documentos.py
```

### Prerequisitos por paso

- **Paso 1**: Registro en GSheets con `Nombre` que coincida con `CASO_PRUEBA` del `env`.
- **Paso 2**: `Proceso 1` debe tener URL (ejecutar Paso 1 primero).
- **Paso 3**: `Proceso 2` debe tener URL (ejecutar Paso 2 primero).
- **Paso 4**: `Proceso 3` debe tener URL (ejecutar Paso 3 primero).
- **Paso 5**: `Proceso 4` debe tener URL (ejecutar Paso 4 primero).

### Notas importantes

- **Paso 5** usa `pyautogui` para adjuntar archivos (ventana nativa de Windows). **No mover el mouse ni cambiar de ventana** mientras se ejecuta.
- Cada test espera confirmación con ENTER antes de cerrar el navegador, permitiendo inspección visual.
- Los resultados (URLs) se persisten automáticamente en Google Sheets.

## Archivos HTML de referencia

- `html_configuracion.html`: HTML capturado del formulario de configuración (Paso 3) para validar selectores.
- `html_modal_error.html`: HTML capturado de un modal de error para debugging.
