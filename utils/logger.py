# -*- coding: utf-8 -*-
from builtins import print as python_print
from utils.execution_context import ExecutionContext


def log_step(*args, **kwargs):
    """
    Imprime en consola y actualiza el estado del hilo actual.
    Drop-in replacement del print nativo.
    """
    mensaje = " ".join(map(str, args))
    python_print(*args, **kwargs)
    ExecutionContext.set_step(mensaje)
