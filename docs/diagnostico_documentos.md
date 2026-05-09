# Diagnóstico: Proceso de Carga de Documentos (Paso 5)

## 1. Flujo actual (paso a paso)

```
Proceso 4 URL (Cuestionario completado)
    │
    ├─► Navegar a URL → Click tab "Documentos del Proceso" (lnk_stpmStepManager5)
    │
    ├─► OnBasePage (driver Chrome INDEPENDIENTE)
    │       ├─ Login en OnBase con credenciales de entorno
    │       ├─ Navegar: Menú → Consulta personalizada → itemLabel133
    │       ├─ Frames: frmViewer → html_form → escribir número contrato → save
    │       ├─ Frames: frmViewer → customQueryResultsFrame → frameDocSelect
    │       ├─ Seleccionar filas (excluyendo tipologías/nombres de globales)
    │       ├─ Clic derecho → menú contextual: "Enviar" → "Archivo"
    │       ├─ Clic "Guardar" → descarga SavedDocument.zip a DOWNLOAD_DIR
    │       ├─ Extraer ZIP → renombrar duplicados → quitar acentos
    │       └─ Retorna lista de nombres de archivos
    │
    ├─► Click "Anexar documentos" (ID: incContractDocumentsbtnUploadDocumentGen)
    │       → Abre NUEVA VENTANA del navegador (Vortal Upload)
    │
    ├─► Cambiar a nueva ventana → maximize
    │
    ├─► [ZONA WINDOWS-ESPECÍFICA: pyautogui]
    │       Win+R → escribe ruta de DOWNLOAD_DIR → Enter (abre Explorador)
    │       Ctrl+E → Ctrl+C (copia rutas de archivos)
    │       Alt+F4 (cierra Explorador)
    │       Click en centro de pantalla (y=200) → Ctrl+V (pega rutas)
    │
    ├─► Click "Subir archivos" (ID: btnUploadFilesButtonBottom)
    │
    ├─► Esperar hasta que count("Documento anexo") >= num_filas
    │
    ├─► Click "Cerrar" (ID: btnCancelBottomButtom) → volver ventana principal
    │
    ├─► Esperar indicador de carga (/html/body/div[2]/div[2]/.../td[2])
    │
    ├─► Click "Ir a publicar" (ID: btnOption_trRowToolbarTop_tdCell1_tbToolBar_Finish)
    │       → Esperar invisibilidad del indicador de carga
    │
    ├─► Click "Publicar" (ID: tbToolBarPlaceHolder_btnPublishRequest)
    │       → Aceptar alerta si aparece (vincular rubro como principal)
    │       → Esperar cambio de URL (timeout 50s)
    │
    └─► PublicacionPage (driver Chrome INDEPENDIENTE, modo incógnito)
            ├─ Login → navegar a URL publicada
            ├─ Click breadcrumb expediente (//*[@id='breadcrumb']/a[4])
            ├─ Click "Ver enlace" (ID: btnSeePublicContractNoticeLink)
            ├─ Leer texto de span (ID: spnPublicContractNoticeLink)
            ├─ Navegar al enlace → leer label (ID: lblDisplayPhaseLink_0)
            └─ Retorna texto del enlace público
```

---

## 2. Problemas identificados en la implementación actual

| # | Archivo | Problema | Severidad |
|---|---------|----------|-----------|
| 1 | `documentos_page.py` | `click_cuando_estable` no elimina `vortal-preloader` antes del click | Alta |
| 2 | `documentos_page.py` | Toda la sección pyautogui es **Windows-only** | Alta |
| 3 | `documentos_page.py` | `self._wait()` usaba método que no existía en `base_page.py` | Alta (corregido) |
| 4 | `documentos_page.py` | `LOADING_INDICATOR` selector absoluto `/html/body/div[2]/...` muy frágil | Media |
| 5 | `documentos_page.py` | `path_docs = DOWNLOAD_DIR + "\\"` separador hardcodeado | Baja |
| 6 | `onbase_page.py` | `import time` estaba dentro del método, no en nivel de módulo | Baja (corregido) |
| 7 | `test_documentos.py` | `strftime("%#d/%m/%Y")` → `%#d` es Windows-only (`%-d` en Linux/Mac) | Baja |

---

## 3. Zona crítica: ventana de carga de archivos

La razón por la que se usa `pyautogui` es que se asume que SECOP II abre un
**diálogo nativo del sistema operativo** al hacer clic en el área de subida.

Sin embargo, muchos sistemas Vortal (incluyendo variantes de SECOP II) usan
un elemento `<input type="file">` oculto con CSS, y luego JavaScript dispara
el `click()` sobre ese input al hacer clic en la zona visible del botón.

**Si ese `<input type="file">` existe en el DOM, Selenium puede inyectar
directamente las rutas de los archivos sin ninguna interacción con el SO.**

---

## 4. Inspección de página requerida

Para determinar si la solución OS-agnostica es aplicable, necesitas inspeccionar
la ventana de carga de SECOP II. Sigue estos pasos:

### 4.1 Abrir el inspector en la ventana de upload

1. Ejecuta el test hasta el punto donde se abre la nueva ventana (después de
   hacer clic en `incContractDocumentsbtnUploadDocumentGen`).
2. Coloca un `input("\nPausa: inspecciona la ventana ahora. Enter para continuar...")` 
   **temporalmente** en `documentos_page.py` justo después de `self.driver.maximize_window()`.
3. Cambia manualmente al foco de la nueva ventana del navegador.
4. Presiona `F12` para abrir DevTools.

### 4.2 Elementos a buscar (copiar al reportar)

En la pestaña **Elements** de DevTools, busca con `Ctrl+F`:

```
input[type="file"]
```

Reporta lo que encuentres. Los casos posibles son:

**Caso A — Input visible o semioculto (solución directa):**
```html
<input type="file" id="????" name="????" multiple accept="*/*" style="display:none">
```
→ Selenium puede usarlo directamente.

**Caso B — Input con clase Vortal:**
```html
<input type="file" class="VortalFileUpload" ...>
```
→ Selenium puede usarlo directamente.

**Caso C — No existe input[type=file] en el DOM:**  
→ El sistema usa un componente Flash/ActiveX o diálogo nativo real.  
→ pyautogui es la única opción en ese caso.

### 4.3 Otros elementos relevantes a reportar

```javascript
// Ejecutar en la consola de DevTools de la ventana de upload:
document.querySelectorAll('input[type="file"]').length;
document.querySelectorAll('input[type="file"]').forEach(el => {
    console.log('id:', el.id, 'name:', el.name, 'style:', el.getAttribute('style'), 'class:', el.className);
});
```

También busca el botón de subida:
```javascript
document.getElementById('btnUploadFilesButtonBottom');
```

Y el contenedor principal de la página:
```javascript
document.getElementById('spnPageTitle')?.textContent;
```

---

## 5. Solución OS-agnostica propuesta

Si se confirma que existe `<input type="file">` (Caso A o B), reemplazar
la sección de pyautogui en `documentos_page.py` por:

```python
# ================================================================
# ADJUNTE OS-AGNOSTICO: inyeccion directa en input[type='file']
# Reemplaza toda la sección pyautogui (win+r, ctrl+e, etc.)
# Requiere que SECOP II tenga un <input type="file"> en el DOM.
# ================================================================

# Selector del input — ajustar con el ID/clase encontrado en inspección
FILE_INPUT_SELECTOR = "input[type='file']"  # Reemplazar con selector exacto

file_input = self.driver.find_element(By.CSS_SELECTOR, FILE_INPUT_SELECTOR)

# Algunos inputs tipo file están ocultos con CSS — hacerlos visibles para SB
self.driver.execute_script(
    "arguments[0].style.display='block'; arguments[0].style.visibility='visible';",
    file_input
)

# Construir string de rutas absolutas (separadas por \n para múltiples archivos)
rutas_absolutas = "\n".join(
    os.path.abspath(os.path.join(DOWNLOAD_DIR, nombre))
    for nombre in lista_documentos
)
file_input.send_keys(rutas_absolutas)

# ================================================================
```

**Ventajas de este enfoque:**
- Funciona en Windows, Linux y macOS
- No depende de resolución de pantalla ni de foco de ventana
- No usa `time.sleep()` arbitrarios
- Compatible con ejecución headless (`headless=True`)
- Los paths se construyen con `os.path.abspath` + `os.path.join` (cross-platform)

---

## 6. Selectores frágiles a mejorar

### `LOADING_INDICATOR` (selector absoluto, muy frágil)

```python
# Actual — se rompe si cambia cualquier div en la jerarquía:
LOADING_INDICATOR = "/html/body/div[2]/div[2]/div[2]/div[1]/table/tbody/tr/td[2]"
```

**Para reemplazar:** inspeccionar qué texto o atributo tiene ese `<td>`. 
Ejecuta en DevTools de la ventana principal (después de adjuntar documentos):
```javascript
document.querySelector(
  "body > div:nth-child(2) > div:nth-child(2) > div:nth-child(2) > div > table > tbody > tr > td:nth-child(2)"
)?.textContent;
// O busca el elemento de carga con:
document.querySelectorAll('td[class*="load"], td[class*="progress"], td[class*="upload"]');
```

Reporta el `id`, `class`, o texto del elemento para construir un selector robusto.

---

## 7. Estado del test `test_documentos.py`

El test está **correctamente estructurado** y sigue el mismo patrón que los tests probados:
- Lee `datos['proceso_4']` de Google Sheets (dependencia del Paso 4) ✅
- Valida que `proceso_4` no esté vacío antes de continuar ✅
- Usa `Driver` (mismo que otros tests) ✅
- Guarda `Proceso 5`, `Fecha publicación` y `Ejecutado` en Google Sheets ✅
- Manejo de errores con traceback completo ✅

**Única nota:** `strftime("%#d/%m/%Y")` usa `%#d` que es Windows-only.
En Linux/Mac usar `%-d`. Solución cross-platform:

```python
# Cross-platform: construir la fecha manualmente
fecha_str = f"{fecha_publicacion.day}/{fecha_publicacion.strftime('%m/%Y')}"
```

---

## 8. Resumen de cambios aplicados

| Archivo | Cambio | Motivo |
|---------|--------|--------|
| `base_page.py` | + método `_wait(timeout)` | `documentos_page` lo necesita para `.until()` custom |
| `base_page.py` | `esperar_cambio_url` refactorizada para usar `_wait` | Eliminar duplicación |
| `documentos_page.py` | `click_cuando_estable` → `esperar_y_click_limpio` | Mismo vortal-preloader del Paso 4 |
| `documentos_page.py` | + `import os` | Necesario para `os.sep` |
| `documentos_page.py` | `DOWNLOAD_DIR + "\\"` → `DOWNLOAD_DIR + os.sep` | Cross-platform |
| `onbase_page.py` | `import time` al nivel de módulo | Buenas prácticas Python |
