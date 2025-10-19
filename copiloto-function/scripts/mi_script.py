# -*- coding: utf-8 -*-
# Este es un script de ejemplo

import os

print('Hola, mundo!')

# Bloque de código funcional a inyectar

def funcion_inyectada():
    print('Esta función fue inyectada exitosamente!')

funcion_inyectada()

# Segundo bloque de código a inyectar

def segundo_bloque():
    print('Este es el segundo bloque de código inyectado!')

segundo_bloque()

# Código mal indentado

def mal_indentado():
   print('Este código está mal indentado')

# Bloque de código fusionado

def fusionar_bloques():
    print('Bloques fusionados exitosamente!')

# Bloque Y mejorado

def bloque_y_mejorado():
    print('Este es el bloque Y mejorado!')

mal_indentado()
fusionar_bloques()
bloque_y_mejorado()

# Intento de inyección de bloque mal indentado

def bloque_inyectado_mal_indentado():
    print('Este bloque está mal indentado y debería ser reparado')

# Inyección de función con variable usada antes de ser definida

print(variable_no_definida)
def funcion_con_variable():
    variable_no_definida = 'Esta variable fue usada antes de ser definida'

# Inyección de bloques

def bloque_bien_formado():
    print('Este bloque está bien formado')

# Duplicado eliminado

def bloque_duplicado():
    print('Este bloque es un duplicado')