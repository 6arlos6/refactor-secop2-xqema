# -*- coding: utf-8 -*-
import threading


class ExecutionContext:
    """
    Gestor de estado global por hilo.
    Reemplaza globales.py con manejo thread-safe usando threading.local().
    """
    _local_data = threading.local()

    # --- PASO ACTUAL ---
    @classmethod
    def set_step(cls, step_description: str):
        cls._local_data.current_step = step_description

    @classmethod
    def get_step(cls) -> str:
        return getattr(cls._local_data, 'current_step', 'Paso no definido')

    # --- SEMAFORO (COLORES) ---
    @classmethod
    def set_color(cls, color: str):
        cls._local_data.status_color = color

    @classmethod
    def get_color(cls) -> str:
        return getattr(cls._local_data, 'status_color', 'verde')

    # --- ADVERTENCIAS ---
    @classmethod
    def add_warning(cls, warning_message: str):
        if not hasattr(cls._local_data, 'warnings'):
            cls._local_data.warnings = []
        cls._local_data.warnings.append(warning_message)
        cls.set_color('amarillo')

    @classmethod
    def get_warnings(cls) -> list:
        return getattr(cls._local_data, 'warnings', [])

    # --- ESTADO DE LOGIN (reemplaza globales.logueado) ---
    @classmethod
    def set_logged_in(cls, value: bool):
        cls._local_data.logged_in = value

    @classmethod
    def is_logged_in(cls) -> bool:
        return getattr(cls._local_data, 'logged_in', False)

    # --- ESTADO DE ERROR (reemplaza globales.error) ---
    @classmethod
    def set_error(cls, value: bool):
        cls._local_data.has_error = value

    @classmethod
    def has_error(cls) -> bool:
        return getattr(cls._local_data, 'has_error', False)

    # --- ESTADOS DE PROCESOS (reemplaza globales.estado_proceso_1..5) ---
    @classmethod
    def set_proceso(cls, numero: int, valor: str):
        setattr(cls._local_data, f'estado_proceso_{numero}', valor)

    @classmethod
    def get_proceso(cls, numero: int) -> str:
        return getattr(cls._local_data, f'estado_proceso_{numero}', '')

    # --- REINICIO (NUEVO REGISTRO) ---
    @classmethod
    def clear(cls):
        cls._local_data.current_step = 'Iniciando proceso'
        cls._local_data.status_color = 'verde'
        cls._local_data.warnings = []
        cls._local_data.has_error = False
        cls._local_data.logged_in = getattr(cls._local_data, 'logged_in', False)
        for i in range(1, 6):
            setattr(cls._local_data, f'estado_proceso_{i}', '')
