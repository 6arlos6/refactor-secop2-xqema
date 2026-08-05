# -*- coding: utf-8 -*-
import sys
from builtins import print as python_print
from utils.execution_context import ExecutionContext

# La consola de Windows usa por defecto cp1252, que no soporta emojis y
# rompe el print con UnicodeEncodeError. Se fuerza UTF-8 en la salida estandar.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def log_step(*args, **kwargs):
    """
    Imprime en consola y actualiza el estado del hilo actual.
    Drop-in replacement del print nativo.
    """
    mensaje = " ".join(map(str, args))
    python_print(*args, **kwargs)
    ExecutionContext.set_step(mensaje)
