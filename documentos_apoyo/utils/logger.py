from builtins import print as python_print
from utils.execution_context import ExecutionContext

def log_step(*args, **kwargs):
    """
    Imprime en consola y a la vez actualiza el estado del hilo actual.
    Actúa como un reemplazo directo (drop-in replacement) del print nativo.
    """
    # 1. Unimos los argumentos tal como lo hace el print original
    mensaje = " ".join(map(str, args))
    
    # 2. Imprimimos en la consola normal para que veas el log en vivo
    python_print(*args, **kwargs)
    
    # 3. Actualizamos el estado global seguro para este hilo
    ExecutionContext.set_step(mensaje)