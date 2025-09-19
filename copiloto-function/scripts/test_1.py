#!/usr/bin/env python3
"""
Script de prueba para el endpoint ejecutar-script
"""

import sys
import datetime


def main():
    """Función principal del script de prueba"""
    print("Test script ejecutado correctamente")
    print(f"Fecha y hora: {datetime.datetime.now().isoformat()}")

    # Imprimir argumentos si fueron proporcionados
    if len(sys.argv) > 1:
        print(f"Argumentos recibidos: {sys.argv[1:]}")

    # Código exitoso
    return 0


if __name__ == "__main__":
    sys.exit(main())
