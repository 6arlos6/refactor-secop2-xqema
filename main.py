# -*- coding: utf-8 -*-
"""
Punto de entrada del bot RPA - SECOP II
Reemplaza: automatizacion.py
"""
from services.orquestador import OrquestadorRPA

if __name__ == "__main__":
    OrquestadorRPA().ejecutar_flujo_maestro()
