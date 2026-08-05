# Automatización SECOP II — UDEA

Bot RPA que automatiza la publicación de procesos de contratación en la plataforma
[SECOP II](https://www.colombiacompra.gov.co/secop-ii) de la Universidad de Antioquia,
integrando datos desde Google Sheets y documentos desde OnBase.

Refactor en arquitectura MVC del proyecto original (`automatizacion.py` / `funciones.py` /
`globales.py`), usando [SeleniumBase](https://seleniumbase.io/) en lugar de Selenium puro.

## Arquitectura

```
main.py                    → Punto de entrada
services/orquestador.py    → Orquesta el pipeline completo (State Valve pattern)
pages/                     → Page Objects, uno por paso del flujo
  base_page.py                → Clase base común (envuelve SeleniumBase)
  login_page.py                Login SECOP II
  creacion_proceso_page.py     Paso 1: Creación del proceso
  informacion_general_page.py  Paso 2: Información general
  configuracion_page.py        Paso 3: Configuración del proceso
  cuestionario_page.py         Paso 4: Cuestionario UNSPSC
  documentos_page.py           Paso 5: Documentos (OnBase) y publicación
  onbase_page.py                Descarga y filtrado de documentos en OnBase
  publicacion_page.py           Obtiene el enlace público tras publicar
data/google_sheets_manager.py → Conexión y repositorios de Google Sheets (gspread)
utils/
  execution_context.py       → Estado por hilo: paso actual, errores, advertencias
  logger.py                  → print centralizado (alias `print`), UTF-8 forzado
  mappers.py                 → Normalización y extracción de datos de fila
config/settings.py           → Carga variables de entorno (.env) y reglas de negocio
```

### Flujo de 5 pasos con reanudación automática

Cada registro en Google Sheets tiene columnas `Proceso 1`..`Proceso 5`. El orquestador solo
ejecuta un paso si su columna está vacía y no hay error previo en el registro (patrón *State
Valve*), lo que permite reanudar desde cualquier punto sin duplicar trabajo.

## Requisitos

- Python 3.10+ (probado con 3.12 y 3.14)
- Google Chrome instalado
- Cuenta de servicio de Google Cloud con acceso a Sheets API y Drive API

## Instalación

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

> En Windows, si `pip install -r requirements.txt` falla con
> `ERROR: To modify pip, please run the following command...`, es porque `pip` necesita
> auto-actualizarse y no puede sobrescribir su propio ejecutable en uso. Usa siempre
> `python.exe -m pip install ...` (nunca `pip install ...` directo) hasta tener el venv
> activado con `pip` ya actualizado.

## Configuración

1. Copia `.env.example` a `.env` y completa los valores reales:

   | Variable | Descripción |
   |---|---|
   | `NOMBRE_ESTACION` | Estación de trabajo cuyos registros pendientes se procesan |
   | `HOJA_DATOS` | Título exacto del Google Sheet (ojo con espacios al inicio/fin) |
   | `WORKSHEET` | Nombre de la pestaña con los registros |
   | `USUARIO_SECOP` / `PASS_SECOP` | Credenciales de SECOP II |
   | `USER_ONBASE` / `PASS_ONBASE` | Credenciales de OnBase |
   | `URL_LOGIN_SECOP` / `URL_SECOP` / `URL_ONBASE` | URLs de las plataformas |
   | `CASO_PRUEBA` | Nombre/prefijo del proceso usado en `tests/` |
   | `HEADLESS_MODE` | `True` para correr Chrome sin ventana |
   | `PUBLICAR_SIN_DOCUMENTOS` | Si `False`, detiene el proceso cuando OnBase no retorna documentos |
   | `N_PASOS_TEST` | Pasos a ejecutar en `tests/test_orquestador.py` (1-5) |
   | `DOWNLOAD_DIR` | (Opcional) ruta de descarga de documentos OnBase; por defecto `documentos/` |

2. Coloca el JSON de credenciales de la cuenta de servicio de Google como
   `data/client_sheet.json` (o en la raíz del proyecto).

3. Comparte el Google Sheet indicado en `HOJA_DATOS` con el `client_email` de ese JSON
   (rol Editor, ya que el bot escribe resultados en las columnas `Proceso N`).

## Ejecución

```powershell
.\venv\Scripts\python.exe main.py
```

Procesa todos los registros pendientes de `NOMBRE_ESTACION` y va guardando el progreso
(URLs por paso) directamente en Google Sheets.

## Tests

Ver [tests/README.md](tests/README.md) para el detalle de cada test individual por paso.
Para correr el pipeline completo (o parcial, vía `N_PASOS_TEST`) contra `CASO_PRUEBA`:

```powershell
.\venv\Scripts\python.exe tests\test_orquestador.py
```

## Notas

- `documentos/` y `downloaded_files/` son carpetas de trabajo (descargas de OnBase);
  no se versionan.
- El logger (`utils/logger.py`) fuerza codificación UTF-8 en stdout/stderr para poder
  usar emojis en los logs de progreso sin romper la consola de Windows (cp1252 por defecto).
