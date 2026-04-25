# Pruebas de la Aplicación

Esta carpeta contiene scripts creados como utilidades para realizar pruebas rápidas de las integraciones y componentes de la aplicación de manera aislada.

## Estructura

- `test_gsheets.py`: Un script independiente para validar de forma rápida que la conexión a Google Sheets se está inicializando correctamente usando los valores de entorno, y que se pueden descargar datos de la base de datos (por ejemplo, buscar un contrato de pruebas específico).

## ¿Cómo ejecutar los tests?

Para los scripts de prueba que interactúan con el archivo `env` de la raíz, así como credenciales relativas (`client_sheet.json`), lo más recomendable es **ejecutar los scripts estando en la carpeta raíz del proyecto**, no desde esta carpeta `tests/`.

### Ejecución de la prueba de Google Sheets

Si te encuentras en una consola (terminal), asegúrate de estar ubicado en la raíz del proyecto (`/.../automatizacionsecop2-main`). Luego ejecuta el siguiente comando:

```bash
python tests/test_gsheets.py
```

### Resultados esperados

Verás logs en la consola indicando lo siguiente:
- Los parámetros leídos desde el entorno.
- Inicialización del cliente de conexión a Google Sheets.
- La confirmación de si el contrato de prueba ha sido encontrado y el número de la fila.

### Adición de nuevos Tests
Si necesitas probar otros aspectos del web scraping, Selenium, o flujos específicos:
1. Crea un nuevo script con prefijo `test_` (ej. `test_login.py`) dentro de esta carpeta.
2. Asegúrate de siempre ejecutarlos ubicándote primero en la raíz del proyecto para que las rutas relativas funcionen adecuadamente.
