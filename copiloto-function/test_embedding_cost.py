# -*- coding: utf-8 -*-
"""
Test para validar si extra_body reduce costos de embeddings
"""
import os
import json
import time

# Cargar variables de entorno ANTES de importar
try:
    with open("local.settings.json", "r", encoding="utf-8") as f:
        settings = json.load(f)
        for key, value in settings.get("Values", {}).items():
            os.environ[key] = str(value)
    print("[OK] Variables de entorno cargadas\n")
except Exception as e:
    print(f"[ERROR] {e}\n")

# Importar DESPUES de cargar variables
from embedding_generator import generar_embedding

# Texto de prueba
texto_prueba = "Este es un texto de prueba para validar si extra_body funciona correctamente y reduce los costos de evaluacion de contenido en Azure OpenAI."

print("="*80)
print("TEST: Validacion de extra_body en generar_embedding()")
print("="*80)
print(f"\n[INPUT] Texto: {texto_prueba}")
print(f"[INPUT] Longitud: {len(texto_prueba)} caracteres\n")

# Generar embedding
print("[EJECUTANDO] Generando embedding con extra_body...")
start_time = time.time()

try:
    embedding = generar_embedding(texto_prueba)
    elapsed = time.time() - start_time
    
    if embedding:
        print(f"\n[OK] Embedding generado exitosamente")
        print(f"[INFO] Dimensiones: {len(embedding)}")
        print(f"[INFO] Primeros 5 valores: {embedding[:5]}")
        print(f"[INFO] Tiempo: {elapsed:.2f}s")
        print(f"\n[VALIDACION] Si extra_body funciona:")
        print("  - NO deberia haber errores")
        print("  - El embedding deberia generarse normalmente")
        print("  - En Azure Portal, verifica que NO aparezcan 'Evaluation Input Tokens'")
        print("\n[SIGUIENTE PASO]:")
        print("  1. Ejecuta este script varias veces")
        print("  2. Ve a Azure Portal > Cost Management")
        print("  3. Filtra por 'text-embedding-3-large'")
        print("  4. Verifica si aparecen 'Evaluation Input Tokens'")
        print("  5. Si NO aparecen, extra_body funciona correctamente")
    else:
        print(f"\n[ERROR] No se pudo generar embedding")
        print("[INFO] Revisa los logs para ver el error")
        
except Exception as e:
    print(f"\n[ERROR] Excepcion: {e}")
    print("\n[DIAGNOSTICO]:")
    print("  - Si el error menciona 'content_filter_policy', extra_body NO es soportado")
    print("  - Si el error es diferente, puede ser un problema de configuracion")
    
print("\n" + "="*80)
print("TEST COMPLETADO")
print("="*80)
