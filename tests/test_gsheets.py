import os
import sys

# Agregar el directorio raíz al path para poder importar módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from data.google_sheets_manager import GoogleSheetsConnection, ContratosRepository

def init_repo():
    """Helper genérico para inicializar y retornar el repositorio."""
    load_dotenv('.env')
    
    db_name = os.getenv("HOJA_DATOS", "DATOS_SECOP_II").strip("'")
    worksheet_name = os.getenv("WORKSHEET", "BASE_DATOS_BYS").strip("'")
    scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    conn = GoogleSheetsConnection("client_sheet.json", db_name, scopes)
    print("Conexion inicializada correctamente.")
    
    repo = ContratosRepository(conn.document, worksheet_name)
    print("Repositorio inicializado correctamente.")
    
    return repo, worksheet_name

def test_connection_and_read():
    """Prueba 1: Solo conectarse y buscar."""
    print("=== INICIANDO TEST DE CONEXION Y LECTURA ===")
    try:
        repo, ws_name = init_repo()
        
        print(f"Buscando el contrato que inicie con '4500141458-PRUEBA' en la hoja {ws_name}...")
        datos = repo.sheet.get_all_values()
        if not datos:
            print("La hoja esta vacia.")
            return

        headers = datos[0]
        if "Nombre" in headers:
            idx_nombre = headers.index("Nombre")
            encontrados = []
            for i, row in enumerate(datos[1:], start=2): # fila 2 en adelante
                if len(row) > idx_nombre and row[idx_nombre].startswith("4500141458-PRUEBA"):
                    encontrados.append((i, row[idx_nombre]))
            
            if encontrados:
                print(f"Exito! Se encontro {len(encontrados)} registro(s) que coinciden:")
                for fila, nombre in encontrados:
                    print(f"  - Fila {fila}: {nombre}")
            else:
                print("No se encontro ningun registro que empiece con '4500141458-PRUEBA'.")
        else:
            print("No se encontro la columna 'Nombre' en los encabezados.")
            
    except Exception as e:
        print(f"Error durante test de lectura: {e}")
    print("=== FIN TEST DE CONEXION Y LECTURA ===\n")

def test_write():
    """Prueba 2: Solo escribir en un registro existente."""
    print("=== INICIANDO TEST DE ESCRITURA ===")
    try:
        repo, ws_name = init_repo()
        
        print(f"Buscando el contrato que inicie con '4500141458-PRUEBA' para proceder a escribir...")
        datos = repo.sheet.get_all_values()
        if not datos:
            print("La hoja esta vacia, no se puede escribir.")
            return

        headers = datos[0]
        if "Nombre" in headers:
            idx_nombre = headers.index("Nombre")
            # Para este test, encontramos el primero y escribimos
            for i, row in enumerate(datos[1:], start=2):
                if len(row) > idx_nombre and row[idx_nombre].startswith("4500141458-PRUEBA"):
                    try:
                        mensaje = "estoy escribiendo correctamente desde python"
                        print(f"Escribiendo '{mensaje}' en la fila {i}, columna 'Observaciones'...")
                        repo.actualizar_celda_por_nombre(i, "Observaciones", mensaje)
                        print("Escritura exitosa.")
                        break # Parar en el primer registro y salir
                    except Exception as e:
                        print(f"Error al escribir en la celda: {e}")
        else:
            print("No se encontro la columna 'Nombre' en los encabezados.")
            
    except Exception as e:
        print(f"Error durante test de escritura: {e}")
    print("=== FIN TEST DE ESCRITURA ===\n")


if __name__ == '__main__':
    # Ejecutamos ambos tests secuencialmente
    test_connection_and_read()
    test_write()
