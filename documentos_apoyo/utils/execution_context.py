import threading

class ExecutionContext:
    """
    Gestor de estado global por hilo. 
    Garantiza que en implementaciones multihilo, cada ejecución tenga su propio estado aislado.
    """
    _local_data = threading.local()

    # --- LÓGICA PASOS ---
    @classmethod
    def set_step(cls, step_description: str):
        """Actualiza el paso actual de la automatización."""
        cls._local_data.current_step = step_description

    @classmethod
    def get_step(cls) -> str:
        """Recupera en qué paso exacto iba el bot antes de fallar."""
        # Si no se ha seteado nada, devuelve un valor por defecto seguro
        return getattr(cls._local_data, 'current_step', 'Paso no definido (Fallo inicial)')

    # --- LÓGICA DE SEMÁFORO (COLORES) ---
    @classmethod
    def set_color(cls, color: str):
        """Valores permitidos: 'verde', 'amarillo', 'rojo'"""
        cls._local_data.status_color = color

    @classmethod
    def get_color(cls) -> str:
        return getattr(cls._local_data, 'status_color', 'verde')
    
    # --- LÓGICA DE ADVERTENCIAS (SOFT FAILS) ---
    @classmethod
    def add_warning(cls, warning_message: str):
        """Agrega una advertencia y degrada el estado del contrato a amarillo."""
        if not hasattr(cls._local_data, 'warnings'):
            cls._local_data.warnings = []
        cls._local_data.warnings.append(warning_message)
        cls.set_color('amarillo')

    @classmethod
    def get_warnings(cls) -> list:
        return getattr(cls._local_data, 'warnings', [])

    # --- REINICIO (NUEVO CONTRATO) ---
    @classmethod
    def clear(cls):
        cls._local_data.current_step = 'Iniciando proceso'
        cls._local_data.status_color = 'verde'
        cls._local_data.warnings = []