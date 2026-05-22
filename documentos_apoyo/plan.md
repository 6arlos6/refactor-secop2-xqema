Necesito que analices los siguientes archivos de un proyecto de refactor que uso MVC
e implementes las siguientes modificaciones en el proyecto actual.

1. analiza como documentos_apoyo\services\orquestador.py 
   en la linea 76 usa "with SB(headless=headless_mode, window_size="1920,1080") as sb: " para
activar o desactivar el modo handles, hazlo similar en el orquestador de este proyecto (documentos_apoyo\services\orquestador.py).

Y tambien ponlo en los test (tests/) para que cuando se desee hacer un test se pueda usar ese modo handles en el orquestador
y en los test.



2. Analiza como funciona Loguer utils/logger.py and execution_contex.py (documentos_apoyo\utils\execution_context.py
documentos_apoyo\utils\logger.py) del otro proyecto (mira como se implementa en las pages de documentos_apoyo\pages y como lo hereda implicitamente el orquestador documentos_apoyo\services\orquestador.py)
   en los distintas pages e implementalo en las paginas de este refactoring (pages/)
   para permitir hacer prints en pantalla y tener un logger. y usa el excecution contest en el orquestador
   de este proyecto (services\orquestador.py)


3. Crea un test para el orquestador que permita ejecutar los N primero pasaos haciendo la lectura y escritura respectiva en google sheet y que pueda ser habdles mode TRUE o FALSE segun se requiera. 