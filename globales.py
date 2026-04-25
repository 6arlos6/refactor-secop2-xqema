#definición de variables globales
def init():
    global estado_proceso_1
    estado_proceso_1 = ""
    #revisa el estado del proceso 2
    global estado_proceso_2
    estado_proceso_2 = ""
    #revisa el estado del proceso 3
    global estado_proceso_3
    estado_proceso_3 = ""
    #revisa el estado del proceso 4
    global estado_proceso_4
    estado_proceso_4 = ""
    #array de valores globales
    array_valores = []
    #variable para controlar si se encuentra logueado
    global logueado
    logueado = False
    global error
    error = False
    global tipologias_excluidas
    tipologias_excluidas = ['CERTIFICADO DE ANTECEDENTES', 'DOCUMENTO DE IDENTIDAD', 'CERTIFICACIÓN BANCARIA', 'CERTIFICACION BANCARIA']
    global nombres_excluidos
    nombres_excluidos = [ 
                        'DELITOSSEXUALES', 
                        'DELITOS_SEXUALES', 
                        'DELITOS-SEXUALES', 
                        'DELITOS SEXUALES',  
                        'REGISTRO-DEUDORES-MOROSOS-ALIMENTARIOS', 
                        'REGISTRO_DEUDORES_MOROSOS_ALIMENTARIOS', 
                        'REGISTRO-DEUDORES-MOROSOS-ALIMENTARIOS',
                        'REGISTRODEUDORESMOROSOSALIMENTARIOS',
                        'DEUDORES-MOROSOS',
                        'DEUDORES_MOROSOS',
                        'DEUDORES MOROSOS',
                        'DEUDORESMOROSOS',
                        'REDAM'
                        ]