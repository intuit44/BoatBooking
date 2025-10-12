# -*- coding: utf-8 -*-
import sys

def buscar_funcion(archivo, funcion):
    with open(archivo, 'r', encoding='utf-8') as f:
        for num_linea, linea in enumerate(f, 1):
            if funcion in linea:
                print(f"Línea {num_linea}: {linea.strip()}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python buscar_funcion.py <ruta_del_archivo> <función_a_buscar>")
    else:
        buscar_funcion(sys.argv[1], sys.argv[2])