import os
import sys
import time

# Agregar la raíz del proyecto al sys.path para importaciones absolutas
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)

# Cargar las variables desde el archivo 'env' de la raíz ANTES de importar los módulos del proyecto
from dotenv import load_dotenv
env_path = os.path.join(root_dir, 'env')
load_dotenv(env_path)

from pages.login_page import LoginPage
from pages.base_page import BasePage
from config.settings import URL_LOGIN_SECOP

def test_login():
    print(f"Iniciando prueba de BasePage + LoginPage...")
    print(f"Usando archivo entorno en: {env_path}")
    print(f"URL de login esperada: {URL_LOGIN_SECOP}")

    print("Iniciando navegador Chrome...")
    driver = BasePage.crear_driver()
    try:
        login_page = LoginPage(driver)

        # Ejecutar secuencia de login
        login_page.iniciar_sesion()

        # Verificación sencilla para el test
        current_url = driver.current_url
        print(f"Secuencia de login ejecutada sin excepciones.")
        print(f"URL Pos-login: {current_url}")

        print("Cerrando el navegador en 5 segundos...")
        time.sleep(5)

    except Exception as e:
        print(f"Error durante el test de login: {e}")
    finally:
        try:
            driver.quit()
        except Exception:
            pass

if __name__ == '__main__':
    test_login()
