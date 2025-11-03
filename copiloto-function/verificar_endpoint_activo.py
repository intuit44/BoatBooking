#!/usr/bin/env python3
"""
Verifica qué endpoint de Azure Search está usando la Function App en ejecución
"""

import os
import sys

# Cargar variables de entorno desde local.settings.json
try:
    import json
    with open("local.settings.json", "r") as f:
        config = json.load(f)
        for key, value in config.get("Values", {}).items():
            if key not in os.environ:
                os.environ[key] = str(value)
except Exception as e:
    print(f"Error cargando local.settings.json: {e}")

# Verificar endpoint configurado
endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
key = os.environ.get("AZURE_SEARCH_KEY")

print("=" * 60)
print("VERIFICACION DE AZURE SEARCH ENDPOINT")
print("=" * 60)

if not endpoint:
    print("ERROR: AZURE_SEARCH_ENDPOINT no configurado")
    sys.exit(1)

print(f"\nEndpoint configurado: {endpoint}")
print(f"Key configurada: {'Si' if key else 'No'}")

# Determinar servicio
if "boatrentalfoundrysearch-s1" in endpoint:
    print("\nServicio: Standard S1 (CORRECTO)")
    print("Capacidad: 25GB")
    print("Estado: Deberia funcionar sin errores de quota")
elif "boatrentalfoundrysearch" in endpoint:
    print("\nServicio: Free (INCORRECTO - LLENO)")
    print("Capacidad: 50MB")
    print("Estado: ERROR - Storage quota exceeded")
    print("\nACCION REQUERIDA: Reiniciar Function App")
else:
    print(f"\nServicio: Desconocido")

# Test de conexión
print("\n" + "=" * 60)
print("TEST DE CONEXION")
print("=" * 60)

try:
    from services.azure_search_client import AzureSearchService
    
    service = AzureSearchService()
    print(f"\nCliente inicializado correctamente")
    print(f"Endpoint activo: {service.endpoint}")
    
    # Intentar una búsqueda simple
    result = service.search(query="test", top=1)
    
    if result.get("exito"):
        print(f"Conexion exitosa")
        print(f"Documentos encontrados: {result.get('total', 0)}")
    else:
        print(f"Error en busqueda: {result.get('error')}")
        
except Exception as e:
    print(f"\nERROR: {e}")
    print("\nPosibles causas:")
    print("1. Function App no reiniciada")
    print("2. Variables de entorno no cargadas")
    print("3. Servicio de busqueda no disponible")

print("\n" + "=" * 60)
