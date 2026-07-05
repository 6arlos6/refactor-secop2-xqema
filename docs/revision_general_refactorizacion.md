# Revisión general de la refactorización SECOP II — RPA

Auditoría solicitada en [archivos_de_apoyo/plan_revision_general.md](../archivos_de_apoyo/plan_revision_general.md). Compara el proyecto refactorizado actual (`services/`, `pages/`, `utils/`, `config/`) contra el proyecto legado monolítico (`funciones.py`, `globales.py`, `automatizacion.py`, en la raíz del repo).

## 1. Resumen ejecutivo

El proyecto refactorizado implementa correctamente el patrón MVC: `services/orquestador.py` como controlador con un patrón *State Valve* (cada paso se ejecuta solo si su columna está vacía y no hay error previo), `pages/*.py` como Page Objects que heredan de `pages/base_page.py`, y `utils/`+`config/` como infraestructura (logger observador, contexto de ejecución thread-safe, configuración centralizada). SeleniumBase se usa en la inmensa mayoría de las interacciones con el navegador; el Selenium manual que queda está justificado y documentado inline (autocompletes jQuery UI, `Select()` nativo, `ActionChains` atómico para OnBase, esperas dentro de iframes). La compatibilidad Windows/Linux y headless/normal se mantiene mediante `config/settings.py` (detección de plataforma, Chrome snap en Linux, flag `HEADLESS_MODE`) y la eliminación de `pyautogui` del flujo de documentos (reemplazado por `input[type=file].send_keys()`).

Se revisó exhaustivamente el código legado (`funciones.py` 1078 líneas, `globales.py`, `automatizacion.py` 217 líneas — este último es el verdadero punto de entrada legado que orquestaba el ciclo de vida completo, no `main.py`) contra el refactor. La gran mayoría de las reglas de negocio no obvias del original **ya están migradas correctamente**, incluyendo el filtro de registros pendientes por "Estación de trabajo" (verificado en `data/google_sheets_manager.py:59-84`), que era fácil de pasar por alto porque en el legado vivía en el bucle principal de `automatizacion.py`, no en `funciones.py`.

Se implementaron 4 mejoras de bajo riesgo (ver sección 2) y se documentaron, sin implementar, las de riesgo medio/alto (sección 3), conforme a la restricción del plan de priorizar estabilidad sobre optimización.

## 2. Mejoras implementadas

- [x] **Descripción:** Estandarizar la navegación a través de `BasePage.navegar_a()` en lugar de `self.driver.get()`/`driver.get()` directo.
      **Motivo:** `navegar_a()` ya existe en `BasePage` y es literalmente un wrapper de `self.driver.get(url)` — el cambio es puramente de forma (consistencia y legibilidad), no de comportamiento.
      **Riesgo:** Bajo (mismo código subyacente, mismo efecto).
      **Archivos modificados:** [pages/cuestionario_page.py](../pages/cuestionario_page.py) (línea 30), [pages/documentos_page.py](../pages/documentos_page.py) (línea 52), [pages/publicacion_page.py](../pages/publicacion_page.py) (líneas 70-71 y 134 — en la primera se reordenó la creación de `base = BasePage(driver)` para que ocurra antes de navegar).

- [x] **Descripción:** Centralizar en `config/settings.py` las listas y diccionarios de reglas de negocio de dominio que vivían hardcodeados en `utils/mappers.py`: `TIPOLOGIAS_EXCLUIDAS`, `NOMBRES_EXCLUIDOS` (filtrado de documentos OnBase), `DICCIONARIO_NORMALIZACION_TIPOLOGIA` (normalización de tipo de contrato) e `INVALID_CHARS` (validación de descripción).
      **Motivo:** Cumple el punto 4 del plan de auditoría ("centralizar configuraciones"). Los valores son idénticos, solo cambia su ubicación; `utils/mappers.py` ahora los re-exporta desde `config.settings` para que ningún import existente se rompa.
      **Riesgo:** Bajo (mismo valor, mismo comportamiento; verificado con grep que no queda ninguna referencia rota y que todos los módulos importan correctamente).
      **Archivos modificados:** [config/settings.py](../config/settings.py) (nuevas constantes al final del archivo), [utils/mappers.py](../utils/mappers.py) (las define ahora vía import desde `config.settings`).

- [x] **Descripción:** Loguear una advertencia explícita cuando la variable de entorno `CASO_PRUEBA` no está definida en `.env`, en lugar de caer en el valor por defecto en silencio.
      **Motivo:** Confirmado por grep que `CASO_PRUEBA` solo se usa en `tests/*.py` (no en `services/orquestador.py` ni `main.py`), así que no hay riesgo de afectar producción. El valor por defecto se mantiene igual; solo se añade visibilidad para no ocultar una configuración de entorno de pruebas incompleta.
      **Riesgo:** Bajo (no cambia el valor resultante en ningún escenario, solo añade un mensaje informativo).
      **Archivos modificados:** [config/settings.py](../config/settings.py) (línea ~64 y siguientes).

- [x] **Descripción:** Renombrar el método privado `_click_action_chains` a `_click_disparando_blur` en `ConfiguracionPage`.
      **Motivo:** El nombre original era incorrecto y confuso — el propio docstring del método explica que **ya no usa `ActionChains`** sino `scrollIntoView` + JS click (una estrategia headless-compatible que sustituyó al `ActionChains` original). El método es privado, con solo 2 usos, ambos dentro del mismo archivo.
      **Riesgo:** Nulo (rename mecánico verificado con grep, sin usos externos al archivo).
      **Archivos modificados:** [pages/configuracion_page.py](../pages/configuracion_page.py) (líneas 126 y 154).

**Verificación realizada tras los cambios:** `python -m py_compile` sobre los 8 archivos tocados, importación en caliente de todos los módulos de `pages/`, `utils/`, `config/` y `services/` afectados, y `pytest --collect-only` sobre toda la carpeta `tests/` (9 tests recolectados sin errores de import). No se ejecutaron los tests end-to-end porque requieren credenciales reales de SECOP II/OnBase no disponibles en esta sesión — se deja como verificación manual pendiente para el equipo (ver sección 7).

## 3. Mejoras recomendadas (no implementadas)

- [ ] **Descripción:** Agregar reintento de login (2 intentos) en `LoginPage.iniciar_sesion()`, replicando el patrón ya existente en `PublicacionPage` (`MAX_INTENTOS_LOGIN=2`).
      **Justificación:** SECOP II usa un STS (Identity Provider) que intermitentemente devuelve error de "sesión expirada" en el primer intento — `PublicacionPage` ya soluciona esto con un segundo intento. Extender el mismo patrón a `LoginPage` mejoraría la robustez del login principal del flujo.
      **Riesgo de implementación:** Medio — cambia comportamiento funcional observable (tiempos de espera adicionales, hasta un `time.sleep(5)` extra entre intentos) y podría enmascarar errores reales de credenciales si no se acota bien el número de reintentos. Requiere pruebas contra el ambiente real antes de adoptarse.

- [ ] **Descripción:** Mover `OPCIONES_TIPO_PERSONA` (diccionario en `pages/informacion_general_page.py:94-100`, con tuplas `(tipo_proveedor, tipo_identificador)` como claves) a `config/settings.py`, igual que se hizo con las listas de `utils/mappers.py`.
      **Justificación:** Sería consistente con la mejora #2 ya implementada, pero es un mapeo de UI acoplado 1:1 al flujo de esa página específica (no una regla de negocio reutilizable como las de exclusión de OnBase).
      **Riesgo de implementación:** Bajo, pero de valor marginal — se prioriza no tocarlo para mantener el alcance de cambios acotado a lo de mayor impacto/menor riesgo.

- [ ] **Descripción:** Externalizar a configuración la URL pública de SECOP reconstruida como fallback en `pages/publicacion_page.py` (`https://community.secop.gov.co/Public/Tendering/OpportunityDetail/Index?noticeUID=...`).
      **Justificación:** Es una URL hardcodeada, frágil si SECOP II cambia su estructura de dominio o rutas.
      **Riesgo de implementación:** Alto sin un entorno de pruebas real — es un fallback poco frecuente (solo se activa si el flujo normal de obtención del enlace falla) y es idéntico al comportamiento ya validado en producción; tocarlo sin poder probarlo contra SECOP II real podría introducir una regresión silenciosa en un camino de recuperación crítico.

- [ ] **Descripción:** Agregar mocking de Google Sheets y fixtures `pytest` explícitas (con `@pytest.mark.parametrize`) a la suite de `tests/`, para permitir tests offline y CI.
      **Justificación:** Hoy los tests son "script-first" (dependen de credenciales reales y de un navegador real); esto limita la posibilidad de integrar CI/CD.
      **Riesgo de implementación:** Bajo en sí mismo, pero de alcance amplio (requiere refactor de toda la carpeta `tests/`) — queda fuera del criterio de "mejora de bajo riesgo y alcance acotado" de esta auditoría. Se recomienda como iniciativa separada.

## 4. Reglas de negocio encontradas en el proyecto original

| # | Regla de negocio | Ubicación original | Estado en refactor | Prioridad | Recomendación |
|---|---|---|---|---|---|
| 1 | Filtro de registros pendientes por "Estación de trabajo" + "Nombre" no vacío + "Ejecutado" ≠ "SI" | `automatizacion.py:172-177` (bucle principal, no en `funciones.py`) | Migrada — `data/google_sheets_manager.py:59-84` (`obtener_registros_pendientes`), invocada desde `services/orquestador.py:54` | Alta | Ninguna |
| 2 | Validación de caracteres inválidos en la descripción del objeto | `funciones.py:1065-1071` | Migrada — `utils/mappers.py` (`contains_invalid_chars`, constante `INVALID_CHARS` ahora en `config/settings.py`), usada en `pages/informacion_general_page.py` | Alta | Ninguna |
| 3 | Normalización de tipo de contrato vía diccionario de homologación | `funciones.py` (dentro de `informacion_general`) | Migrada — `utils/mappers.py` (`normalizar_tipo_contrato`, diccionario ahora en `config/settings.py`) | Alta | Ninguna |
| 4 | Mapeo tipo_proveedor + tipo_identificador → opción de creación de contratista | `funciones.py:269-282` | Migrada — `pages/informacion_general_page.py:94-100` (`OPCIONES_TIPO_PERSONA`) | Alta | Considerar mover a config (ver sección 3, bajo impacto) |
| 5 | Ciudad forzada a "MEDELLIN" para proveedores con identificador extranjero | `funciones.py:290-291` | Migrada — `pages/informacion_general_page.py` (bloque de localización) | Alta | Ninguna |
| 6 | Contrato marco opcional (se omite si está vacío o es "No Aplica") | `funciones.py:174` | Migrada — `pages/informacion_general_page.py` (`_configurar_contrato_marco`) | Media | Ninguna |
| 7 | Cálculo de duración entre fecha de inicio y fin (`obtener_dias`) | `funciones.py:41-48` | Migrada — `utils/mappers.py:obtener_dias`, invocada en `pages/informacion_general_page.py:507` (confirmado con grep, tiene llamador activo) | Media | Ninguna |
| 8 | Branching Funcionamiento vs. Inversión con radios y campos distintos para destinación de gasto | `funciones.py:460-527` | Migrada — `pages/configuracion_page.py` (`_configurar_destinacion_gasto` con dispatch a `_configurar_funcionamiento`/`_configurar_inversion`) | Alta | Ninguna |
| 9 | Validación `len(codigo_cdp) == len(saldo_cdp)` antes de procesar CDPs | `funciones.py:533-534` | Migrada — `pages/configuracion_page.py:129-130` | Alta | Ninguna |
| 10 | Distribución proporcional del valor estimado entre múltiples CDPs, con el último absorbiendo el residuo del redondeo | `funciones.py` (bloque de distribución en `configuracion_proceso`) | Migrada — `pages/configuracion_page.py` (`_agregar_cdps`, ~líneas 417-463) | Alta | Ninguna |
| 11 | Subunidad ejecutora hardcodeada `"00-00-00"` para todos los CDPs | `funciones.py:568` | Migrada — `pages/configuracion_page.py:522` (mismo valor) | Media | Ninguna |
| 12 | Registro en SIIF forzado a "No" | `funciones.py:529-531` | Migrada — `pages/configuracion_page.py:126` (vía `_click_disparando_blur`, ver mejora #4) | Media | Ninguna |
| 13 | Cantidad de producto hardcodeada a `"1"` en el cuestionario | `funciones.py:640` | Migrada — `pages/cuestionario_page.py:56` | Media | Ninguna |
| 14 | Exclusión de documentos OnBase por tipología y nombre, con excepción especial: "CERTIFICADO DE ANTECEDENTES" se incluye solo si su nombre no está en la lista de nombres excluidos | `globales.py:21-37`, `funciones.py` (dentro de `descargar_onbase`, ~línea 900) | Migrada — `utils/mappers.py` (constantes ahora en `config/settings.py`), lógica en `pages/onbase_page.py:248-251` | Alta | Ninguna |
| 15 | Renombrado de documentos duplicados (sufijo numérico) y normalización de acentos (`unidecode`) al procesar el ZIP de OnBase | `funciones.py:952-971` | Migrada — `pages/onbase_page.py` (~líneas 340-355) | Media | Ninguna |
| 16 | Adjunte de documentos a SECOP II vía copiar/pegar rutas de archivo con `pyautogui` (Windows-only) | `funciones.py:704-734` | **Reemplazada por una solución superior**: `pages/documentos_page.py:_cargar_archivos_via_input()` usa `input[type=file].send_keys()` de Selenium — multiplataforma y compatible con headless | Alta | Ninguna (ya resuelto, mejor que el original) |
| 17 | Login con reintento ante error transitorio de sesión | No existía en el original (single-attempt) | Parcial — existe solo en `pages/publicacion_page.py` (`MAX_INTENTOS_LOGIN=2`), es una mejora introducida en el refactor, no ausente del original | Baja | Ver sección 3 (extenderlo a `LoginPage`, documentado y no implementado por riesgo medio) |
| 18 | `array_valores` — variable global declarada en `globales.py:15` y nunca utilizada | `globales.py:15` | No aplica — era código muerto en el original | Baja | Ninguna, solo nota informativa |
| 19 | Mensaje final al usuario vía popup de `tkinter` (`mostrarMensaje`) al terminar el lote | `automatizacion.py:213`, `funciones.py:1014-1017` | No migrado — el refactor usa solo logging por consola (`print` final en `orquestador.py:100`) | Baja | Ninguna: un popup bloqueante de GUI no es apropiado para un RPA headless/desatendido; el logging por consola/logger observador es la evolución correcta |

## 5. Evaluación general

### 5.1 Arquitectura
Separación de responsabilidades clara y consistente: el orquestador no conoce selectores ni detalles de UI, las páginas no escriben directamente en Google Sheets, y la infraestructura (logger, contexto, config) es transversal sin acoplarse a SECOP II. El patrón *State Valve* (columnas `Proceso 1..5` vacías como condición de ejecución) reproduce fielmente — y mejora, al centralizarlo — el mecanismo de reanudación que en el legado estaba disperso entre `globales.py` y los condicionales de `automatizacion.py`.

### 5.2 Uso de SeleniumBase
Aproximadamente el 95% de las interacciones usan la API de SeleniumBase (`sb.click`, `sb.type`, `wait_for_element_visible`, `wait_for_text`, `js_click`, `execute_script`). El Selenium manual restante está acotado a casos donde SeleniumBase no ofrece equivalente directo (autocompletes jQuery UI que requieren eventos de teclado reales, `Select()` nativo para dropdowns, `ActionChains` atómico para CTRL+click en la grilla legacy de OnBase, esperas dentro de iframes anidados) y está documentado inline explicando el porqué en cada caso.

### 5.3 Cumplimiento del patrón MVC
Sólido: Controller (`services/orquestador.py`) → View/Page Object (`pages/*.py` vía `BasePage`) → Model/persistencia (`data/google_sheets_manager.py`). Las únicas excepciones (páginas que crean su propio driver: `PublicacionPage`, `OnBasePage`) están justificadas porque requieren sesiones de navegador independientes, no por descuido de diseño.

### 5.4 Mantenibilidad
Buena: código documentado con explicaciones de *por qué* (no solo *qué*), especialmente en los `time.sleep()` que persisten — cada uno indica por qué no pudo reemplazarse por una espera dinámica (mayoritariamente limitaciones de OnBase legacy o de re-renderizado de jQuery UI/VortalFramework en SECOP II). Con esta auditoría se centralizaron además las últimas listas de reglas de negocio que quedaban fuera de `config/`.

### 5.5 Reutilización de código
`BasePage` concentra más de 40 métodos genéricos (clicks, esperas, escritura, frames, dropdowns) reutilizados por las 8 páginas sin duplicación relevante. Los patrones específicos de SECOP II (eliminación de overlays `blockUI`/`vortal-preloader`, autocomplete con fallback a teclado) están encapsulados una sola vez en la clase base.

### 5.6 Riesgos técnicos identificados
- Dependencia de estructura de URL/HTML de SECOP II para el fallback de obtención de enlace público (documentado en sección 3, no mitigado).
- Ausencia de reintento de login en el flujo principal (`LoginPage`), a diferencia de `PublicacionPage`.
- Suite de tests dependiente de credenciales y navegador real; sin mocking ni CI, cualquier cambio solo puede validarse manualmente contra el ambiente real de SECOP II/OnBase.
- El módulo `OnBasePage` es el más largo (~280 líneas) por la naturaleza legacy de OnBase (frames anidados, AJAX sin señales DOM confiables); es aceptable dado el contexto, pero es el que ofrece menor margen de simplificación futura.

### 5.7 Recomendaciones para futuras refactorizaciones
1. Evaluar mocking de Google Sheets para poder ejecutar la suite de `tests/` sin credenciales reales y habilitar CI.
2. Si se decide reforzar la resiliencia del login, extender el patrón de reintento de `PublicacionPage` a `LoginPage` con pruebas exhaustivas en el ambiente real antes de desplegar.
3. Mantener la disciplina actual de documentar el *por qué* de cada `time.sleep()` que se agregue a futuro, siguiendo el estándar ya establecido en `onbase_page.py` y `configuracion_page.py`.

## 6. Oportunidades de optimización de tiempos de espera (sleeps) con SeleniumBase

Inventario completo de los `time.sleep()`/`self.sb.sleep()` que persisten en `pages/` tras la refactorización, clasificados por nivel de riesgo de reemplazarlos por una espera dinámica de SeleniumBase (`wait_for_element_visible`, `wait_for_element_present`, `wait_for_element_not_visible`, `wait_for_text`) y la estrategia concreta sugerida para cada caso. **Ninguno de estos cambios fue implementado** en esta auditoría: todos alteran el *timing* real de interacción con SECOP II/OnBase, que es exactamente el tipo de cambio que el plan de auditoría pide documentar sin tocar salvo que se pueda validar contra el ambiente real.

### 6.1 Riesgo bajo — candidatos con mayor probabilidad de éxito

| # | Ubicación | Sleep actual | Propósito | Estrategia SeleniumBase sugerida |
|---|---|---|---|---|
| 1 | `configuracion_page.py:386` y `:406` | `self.sb.sleep(2)` tras `seleccionar_dropdown()` (Funcionamiento/Inversión) | Esperar a que SECOP II re-renderice el bloque de radios de presupuesto tras cambiar el `<select>` | `self.sb.wait_for_element_present(self.RADIO_PNG_NO, timeout=5)` inmediatamente después del `seleccionar_dropdown()`, antes de `_esperar_desbloqueo_ui()`. Si el radio ya existe en el DOM antes del cambio (solo cambia de visibilidad, no se recrea), usar en su lugar `wait_for_element_visible` con un `assert not` previo sobre el estado "oculto" — requiere inspeccionar el HTML real para decidir cuál de las dos aplica. |
| 2 | `onbase_page.py:141` | `time.sleep(2)` tras abrir el menú de navegación (JS click) | Esperar a que el menú desplegable termine su animación CSS antes de buscar el siguiente ítem | `self.sb.wait_for_element_visible('#customquery', timeout=5)` — el propio código ya espera este elemento justo después (línea 143), así que solo hay que mover la espera dinámica antes del sleep en vez de después. |
| 3 | `onbase_page.py:147` | `time.sleep(2)` tras click en "Consulta Personalizada" | Esperar a que el panel lateral cargue antes de entrar al `NavPanelIFrame` | Ya existe `EC.frame_to_be_available_and_switch_to_it` justo después (línea 153) — se puede intentar eliminar el sleep intermedio y dejar que ese `WebDriverWait` (que ya tiene polling) absorba la espera real. |

### 6.2 Riesgo medio — requieren validar contra el HTML real antes de tocarlos

| # | Ubicación | Sleep actual | Propósito | Estrategia SeleniumBase sugerida | Por qué es riesgo medio |
|---|---|---|---|---|---|
| 4 | `configuracion_page.py:499` | `self.sb.sleep(3)` tras entrar al iframe `SIIFModal_iframe` | "El iframe carga lento" (comentario original) | `WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, self.RADIO_CDP)))` en vez de sleep fijo — ya se usa un wait similar 4 líneas después (línea 503), se podría fusionar ambas esperas en una sola. | El código ya usa `sb.*` deliberadamente evitado aquí porque "reinicia el contexto de frame" (comentario línea 469-475 del hallazgo original) — hay que confirmar que un `WebDriverWait` raw (no `sb.*`) no tiene el mismo problema antes de fusionar. |
| 5 | `configuracion_page.py:574` | `self.sb.sleep(3)` antes de `_click_guardar()` | Buffer previo al guardado final del formulario | `self._esperar_desbloqueo_ui()` (ya existe en la clase) en vez de un sleep ciego — esperaría específicamente a que `.blockUI`/`.vortal-preloader` desaparezcan. | El formulario de configuración es el más complejo del flujo (fechas, CDPs, radios); un guardado prematuro podría enviar el formulario con un campo aún no confirmado por el framework Vortal, produciendo un error de validación silencioso. |
| 6 | `documentos_page.py:103` | `time.sleep(5)` tras cargar archivos en el `input[type=file]` | Esperar a que SECOP II procese la selección de archivos antes de hacer click en "Subir" | Buscar si aparece algún indicador de archivo(s) cargado(s) en el popup (ej. contador de archivos seleccionados) y usar `self.sb.wait_for_text(...)` sobre ese contador en vez de un sleep fijo. | No se identificó con certeza un selector DOM que confirme "selección procesada" — requiere inspeccionar el popup `DocumentAlternateUpload` en vivo para encontrar la señal correcta. |
| 7 | `documentos_page.py:115` | `time.sleep(3)` tras click en "Subir archivos" | Esperar a que el servidor inicie el procesamiento del upload antes de leer la tabla de archivos | Reemplazar por el mismo `wait_for_text("Documento anexo", ...)` que ya se usa 10 líneas después (línea 124-126), simplemente adelantando esa condición. | Bajo riesgo de romper, pero el `_wait(120).until(...)` que le sigue ya tolera la variabilidad — fusionar podría no dar ganancia real de tiempo, solo simplicidad de código. |

### 6.3 Riesgo alto / no recomendable tocar sin ambiente de pruebas

| # | Ubicación | Sleep actual | Por qué no se recomienda optimizar ahora |
|---|---|---|---|
| 8 | `onbase_page.py:171` | `time.sleep(5)` — "OnBase tarda ~5s en cargar frmViewer tras seleccionar item del menú" | El propio comentario del archivo (línea 9-11) documenta que OnBase **no tiene señales DOM confiables de carga completa**; ya se intentó resolver dinámicamente y no funcionó, por eso quedó como sleep fijo. |
| 9 | `onbase_page.py:235,253,256,269,271,282,290,294` | Sleeps de 0.5s a 3s alrededor de la selección `CTRL+click`, `context_click` y navegación de menú contextual de la grilla legacy de OnBase | Estos sleeps protegen una secuencia de `ActionChains` atómica (documentada en líneas 217-231) que ya es frágil de por sí — la grilla de OnBase solo reconoce eventos de mouse "confiables" (`isTrusted:true`), no eventos sintéticos. Cualquier intento de espera dinámica que dependa de detectar un cambio de estado en esa grilla arriesga romper la sincronización fina entre `key_down`→`click`→`key_up` que hace funcionar la selección múltiple en headless. |
| 10 | `documentos_page.py:143,157` | `time.sleep(5)`/`time.sleep(3)` | Ya son *fallbacks* que se ejecutan solo cuando una espera dinámica previa (`esperar_presente`/`esperar_invisible` sobre `LOADING_INDICATOR`) falla — no son el camino primario, así que optimizarlos no aporta valor: el camino feliz ya usa espera dinámica. |
| 11 | `configuracion_page.py:147,168,174,188,195,199,202,210,221,225,228,232,257,263,491,507,529` | Sleeps de 0.3s-1s dentro de `_esperar_desbloqueo_ui`, `_click_disparando_blur`, `_escribir_fecha`, `_escribir_como_humano`, `_click_radio_dinamico`, `_agregar_un_cdp` | Ya son "micro-pausas" complementarias a esperas dinámicas existentes (`wait_for_element_not_visible`, `wait_for_element_visible`), usadas para dar margen a que un evento JS/blur se propague antes de la siguiente acción. Reducirlas ganaría fracciones de segundo por paso, pero el riesgo de introducir `StaleElementReferenceException` intermitentes en un flujo que hoy es estable no se justifica frente a la ganancia. |
| 12 | `creacion_proceso_page.py:218` | `self.sb.sleep(1)` tras `wait_for_element_visible` del resultado del autocomplete de "unidad de contratación" | Ya está precedido por una espera dinámica real (línea 217); el sleep es solo el margen adicional que jQuery UI Autocomplete necesita para terminar de pintar el resultado antes del `ActionChains.click()`. Bajo valor de optimización, alto riesgo relativo (afecta la selección de unidad contratante, un campo obligatorio temprano en el flujo). |

### 6.4 Caso especial — no es una espera de UI

- **`publicacion_page.py:66`** — `time.sleep(5)` entre el primer y segundo intento de login (`MAX_INTENTOS_LOGIN=2`). No es una espera a que un elemento aparezca, sino un *backoff* deliberado antes de reintentar tras una falla de sesión del STS de SECOP II. No aplica una estrategia de `wait_for_element_*` porque no está esperando un elemento — está dando tiempo a que el servidor de identidad se recupere. No se recomienda tocarlo.

### Resumen de la oportunidad

De los ~50 sleeps inventariados en `pages/`, **3 son candidatos de riesgo bajo** (tabla 6.1), **4 de riesgo medio** (tabla 6.2, requieren inspeccionar el DOM real de SECOP II/OnBase antes de tocarlos) y el resto (~40, mayoritariamente en `onbase_page.py` y las micro-pausas de `configuracion_page.py`) se recomienda **no tocar**: ya están documentados como necesarios por limitaciones reales de los frameworks legacy/jQuery UI, o son fallbacks de un camino de error que no se ejecuta en el flujo normal. La ganancia de tiempo total esperable de optimizar solo los candidatos de riesgo bajo/medio es del orden de 15-20 segundos por registro procesado (principalmente en `configuracion_page.py`), frente a un pipeline completo que toma varios minutos por proceso — es una mejora de calidad de código más que de rendimiento significativo, y por eso el plan de auditoría prioriza no implementarla sin poder validarla contra el ambiente real primero.

## 7. Anexos

### Metodología de verificación
- Lectura completa (línea por línea) de: `funciones.py`, `globales.py`, `automatizacion.py`, `main.py`, `services/orquestador.py`, `pages/base_page.py`, las 8 páginas de `pages/`, `utils/logger.py`, `utils/execution_context.py`, `utils/mappers.py`, `config/settings.py`, `data/google_sheets_manager.py` (fragmentos relevantes).
- Verificación puntual por `grep` de: todos los usos de los símbolos movidos/renombrados (antes y después del cambio), todas las referencias a `navegar_a`/`driver.get`, y todos los `time.sleep()` documentados en `onbase_page.py`, `configuracion_page.py`, `documentos_page.py` y `creacion_proceso_page.py`.
- Verificación de compilación e importación (`py_compile` + import directo) de los 8 archivos modificados, y `pytest --collect-only` sobre toda la carpeta `tests/` (9 tests recolectados sin error).
- No se ejecutaron pruebas end-to-end contra SECOP II/OnBase reales por no disponer de credenciales de un ambiente de pruebas en esta sesión; se recomienda que el equipo corra `tests/test_orquestador.py` (con `N_PASOS_TEST` bajo y `HEADLESS_MODE=True`/`False`) antes de dar por cerrada esta auditoría en producción.

### Archivos de referencia usados
- Legado: `funciones.py`, `globales.py`, `automatizacion.py` (punto de entrada real del ciclo de vida legado), `main.py` (ya reemplazado por la versión refactorizada).
- Materiales de apoyo históricos (`archivos_de_apoyo/`, `documentos_apoyo/`, `docs/diagnostico_documentos.md`): artefactos de un proyecto de referencia distinto, usados en el pasado para portar patrones (headless `SB()`, logger + `ExecutionContext`) que **ya fueron adoptados y mejorados** en el proyecto principal; no requirieron acción adicional en esta auditoría.
