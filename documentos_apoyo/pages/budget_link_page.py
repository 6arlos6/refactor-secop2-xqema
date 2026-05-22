from seleniumbase import BaseCase
from pages.base_page import BasePage
from utils.mappers import formatear_valor_gt
from utils.logger import log_step as print

class BudgetLinkPage(BasePage):
    def __init__(self, sb:BaseCase):
        self.sb = sb

    #  1. NAVEGACIÓN Y METADATOS DEL MÓDULO
    TITULO_MODULO_CDP = "//h5[contains(normalize-space(), 'Contratación') and following-sibling::p[contains(normalize-space(), 'CONTRATO / INICIO') or contains(normalize-space(), 'VINCULAR DISPONIBILIDAD PRESUPUESTAL / NUEVO CONTRATO')]]"

    #  2. FORMULARIO BÚSQUEDA DE CONTRATO
    BTN_CONSULTAR_CONTRATO = "//button[contains(., 'Consultar')]"
    BTN_CONTINUAR_CONTRATO = "//button[contains(., 'Continuar')]"

    #  3. TABLA DE RESULTADOS Y VINCULACIÓN (CDP)
    INPUT_BUSQUEDA_PARA_ANEXAR = "(//input[@id='search'])[1]"
    
    INPUT_BUSQUEDA_ANEXADO = "(//input[@id='search'])[2]"

    # Selector maestro de doble validación
    BTN_VINCULAR_FILA_ESPECIFICA = (
        "//div[@role='row']["
        "div[@data-field='BUDGET_AVAILABILITY_LINK_AMOUNT' and @title='{0}'] and "
        "div[@data-field='BUDGET_AVAILABILITY_IDENTIFIER' and @title='{1}']"
        "]//button[@title='Vincular']"
    )
    MSG_EXITO_VINCULACION_CDP = "//div[contains(., 'Se ha vinculado la disponibilidad presupuestal exitosamente')]"

    #  4. TABLA DE CDPs YA VINCULADOS (Validación Previa)
    FILA_CDP_YA_VINCULADO = (
        "//div[@role='row']["
        "div[contains(@data-field, 'BUDGET_AVAILABILITY_AMOUNT') and contains(@title, '{0}')] and "
        "div[@data-field='BUDGET_AVAILABILITY_IDENTIFIER' and @title='{1}']"
        "]//button[@title='Desvincular']"
    )

    def navegar_a_vincular_cdp(self):
        """
        Navega al módulo de vinculación de CDP al contrato asegurando que la página cargue por completo.
        """
        self.navegar_y_esperar_carga(
            nombre_modulo="Vinculación de CDP",
            selector_principal=self.TITULO_MODULO_CDP,
            nombre_submenu="Vincular Disponibilidad"
        )

    def verificar_cdp_vinculado(self, valor_cdp, codigo_cdp):
        """
        Verifica si la combinación exacta de valor y CDP ya aparece 
        en la tabla de vinculaciones actuales.
        """
        print(f"🧐 Verificando si el CDP {codigo_cdp} para el valor '{valor_cdp}' ya está vinculado...")

        try:
            if not self.sb.is_element_visible(self.INPUT_BUSQUEDA_ANEXADO):
                try:
                    self.sb.wait_for_element_visible(self.INPUT_BUSQUEDA_ANEXADO, timeout=4)
                except:
                    print("⚠️ No se encontró tabla de vinculaciones previas. Asumiendo que se debe vincular.")
                    return False
            
            self.sb.wait_for_element_visible(self.INPUT_BUSQUEDA_ANEXADO)
            self.sb.clear(self.INPUT_BUSQUEDA_ANEXADO)
            self.sb.type(self.INPUT_BUSQUEDA_ANEXADO, codigo_cdp)
            self.sb.sleep(1.5)

            xpath_cdp = self.FILA_CDP_YA_VINCULADO.format(valor_cdp, codigo_cdp)
            
            if self.sb.is_element_visible(xpath_cdp):
                print(f"ℹ️ El CDP {codigo_cdp} con ese valor YA ESTÁ VINCULADO actualmente.")
                return True
            else:
                print("✔️ La combinación no está vinculada. Procediendo a asociarla...")
                return False
        except Exception as e:
            print(f"⚠️ Error verificando (se omitirá verificación): {e}")
            return False
        
    def vincular_disponibilidad_presupuestal(self, num_contrato, codigo_cdp, valor_cdp):
        """
        Busca el contrato, avanza a la tabla de CDPs y realiza la vinculación 
        validando la combinación exacta de Rubro + CDP.
        """

        VALOR_CDP_FORMATEADO = formatear_valor_gt(valor_cdp)

        print(f"🔍 Consultando contrato No. {num_contrato}...")

        # 1. Buscar Contrato (Usando el selector de BasePage)
        self.sb.wait_for_element_visible(self.INPUT_CONTRATO_NO)
        self.sb.clear(self.INPUT_CONTRATO_NO)
        self.sb.type(self.INPUT_CONTRATO_NO, num_contrato)
        
        self.sb.wait_for_element_clickable(self.BTN_CONSULTAR_CONTRATO)
        self.sb.click(self.BTN_CONSULTAR_CONTRATO)
        
        # 2. Validar si el contrato existe y continuar
        try:
            print("⏳ Esperando confirmación de consulta...")
            self.sb.wait_for_element_visible(self.BTN_CONTINUAR_CONTRATO, timeout=10)
            self.sb.click(self.BTN_CONTINUAR_CONTRATO)
        except Exception:
            print(f"❌ El contrato {num_contrato} no existe o no habilitó el botón Continuar.")
            return False

        self.sb.sleep(1.5)

        if self.verificar_cdp_vinculado(VALOR_CDP_FORMATEADO, codigo_cdp):
            return True
        
        # 3. Filtrar en la tabla
        print(f"🔎 Buscando CDP {codigo_cdp} en la tabla de disponibilidades...")
        try:
            self.sb.wait_for_element_visible(self.INPUT_BUSQUEDA_PARA_ANEXAR)
            self.sb.clear(self.INPUT_BUSQUEDA_PARA_ANEXAR)
            self.sb.type(self.INPUT_BUSQUEDA_PARA_ANEXAR, codigo_cdp)
            self.sb.sleep(1.5)
        except:
            print(f"❌ El contrato {num_contrato} no tiene rubros vinculados para proceder.")
            return False
        
        # 4. Vincular Fila Exacta
        xpath_vincular = self.BTN_VINCULAR_FILA_ESPECIFICA.format(VALOR_CDP_FORMATEADO, codigo_cdp)
        
        try:
            print(f"🎯 Intentando vincular fila [Valor: {VALOR_CDP_FORMATEADO} | CDP: {codigo_cdp}]")
            self.sb.wait_for_element_visible(xpath_vincular, timeout=10)
            self.sb.click(xpath_vincular)
            
            # 5. Confirmar guardado
            self.sb.wait_for_element_visible(self.MSG_EXITO_VINCULACION_CDP, timeout=12)
            print("✅ Disponibilidad presupuestal vinculada exitosamente.")
            return True
            
        except Exception as e:
            print(f"❌ Error: No se encontró la combinación Valor/CDP o falló la confirmación. Detalle: {e}")
            return False

    