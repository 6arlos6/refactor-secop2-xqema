import os
import sys
import time

# Agregar la raíz del proyecto al sys.path para importaciones absolutas
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)

from dotenv import load_dotenv
env_path = os.path.join(root_dir, '.env')
load_dotenv(env_path)

from seleniumbase import SB
from pages.login_page import LoginPage
from config.settings import URL_LOGIN_SECOP, HEADLESS_MODE

def test_login():
    print(f"Iniciando prueba de BasePage + LoginPage...")
    print(f"Usando archivo entorno en: {env_path}")
    print(f"URL de login esperada: {URL_LOGIN_SECOP}")

    headless_mode = HEADLESS_MODE
    print("Iniciando navegador Chrome...")
    if headless_mode:
        print("Ejecutando en modo sin ventana (Headless)")
    else:
        print("Ejecutando con interfaz grafica visible")

    try:
        with SB(headless=headless_mode) as sb:
            sb.set_window_size(1920, 1080)
            login_page = LoginPage(sb)

            # Ejecutar secuencia de login
            login_page.iniciar_sesion()

            # Verificación sencilla para el test
            current_url = sb.get_current_url()
            print(f"Secuencia de login ejecutada sin excepciones.")
            print(f"URL Pos-login: {current_url}")

            print("Cerrando el navegador en 5 segundos...")
            time.sleep(5)
            # SB cierra el browser automaticamente al salir del with

    except Exception as e:
        print(f"Error durante el test de login: {e}")

if __name__ == '__main__':
    test_login()
