#!/usr/bin/env python3
"""
Test completo simulando payload de Foundry para validar:
- RecuperaciÃ³n de memoria (Cosmos DB + AI Search)
- Generador semÃ¡ntico enriquecido
- Guardado de interacciones
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(__file__))

# Cargar variables
try:
    with open('local.settings.json', 'r') as f:
        settings = json.load(f)
        for key, value in settings.get('Values', {}).items():
            if key not in os.environ:
                os.environ[key] = value
except Exception:
    pass

import azure.functions as func
from function_app import app

print("\n" + "=" * 80)
print("TEST FOUNDRY: SimulaciÃ³n completa de memoria")
print("=" * 80)

# === TEST 1: historial-interacciones ===
print("\n[TEST 1] Endpoint: historial-interacciones")
print("-" * 80)

func_obj = None
for f in app.get_functions():
    if f.get_function_name() == "historial_interacciones":
        func_obj = f
        break

if not func_obj:
    print("âŒ FunciÃ³n historial_interacciones no encontrada")
    sys.exit(1)

# Simular payload de Foundry
req1 = func.HttpRequest(
    method="GET",
    url="http://localhost:7071/api/historial-interacciones",
    headers={
        "Session-ID": "assistant",
        "Agent-ID": "assistant"
    },
    params={},
    body=b""
)

print("ðŸ“¤ Request simulado:")
print(f"   Headers: Session-ID=assistant, Agent-ID=assistant")
print(f"   Method: GET")

response1 = func_obj.get_user_function()(req1)

if response1:
    data1 = json.loads(response1.get_body().decode())
    print(f"\nðŸ“¥ Response recibido:")
    print(f"   Status: {response1.status_code}")
    print(f"   Exito: {data1.get('exito')}")
    print(f"   Total interacciones: {data1.get('total')}")
    print(f"   Tiene respuesta_usuario: {'respuesta_usuario' in data1}")
    
    if 'respuesta_usuario' in data1:
        resp = data1['respuesta_usuario']
        print(f"   Longitud respuesta_usuario: {len(resp)} chars")
        
    
    # Verificar metadata
    metadata = data1.get('metadata', {})
    print(f"\nðŸ” Metadata:")
    print(f"   memoria_aplicada: {metadata.get('memoria_aplicada')}")
    print(f"   interacciones_previas: {metadata.get('interacciones_previas')}")
    print(f"   docs_vectoriales: {metadata.get('docs_vectoriales')}")
    
    # Verificar contexto inteligente
    ctx = data1.get('contexto_inteligente', {})
    print(f"\nðŸ§  Contexto Inteligente:")
    print(f"   tiene_memoria: {ctx.get('tiene_memoria')}")
    print(f"   total_interacciones: {ctx.get('total_interacciones')}")
    print(f"   documentos_relevantes: {ctx.get('documentos_relevantes')}")
    print(f"   fuente_datos: {ctx.get('fuente_datos')}")
else:
    print("âŒ Response es None")

# === TEST 2: memoria-global ===
print("\n" + "=" * 80)
print("[TEST 2] Endpoint: memoria-global")
print("-" * 80)

func_obj2 = None
for f in app.get_functions():
    if f.get_function_name() == "memoria_global":
        func_obj2 = f
        break

if not func_obj2:
    print("âŒ FunciÃ³n memoria_global no encontrada")
else:
    req2 = func.HttpRequest(
        method="GET",
        url="http://localhost:7071/api/memoria-global",
        headers={},
        params={"limite": "5"},
        body=b""
    )
    
    print("ðŸ“¤ Request simulado:")
    print(f"   Params: limite=5")
    print(f"   Method: GET")
    
    response2 = func_obj2.get_user_function()(req2)
    
    if response2:
        data2 = json.loads(response2.get_body().decode())
        print(f"\nðŸ“¥ Response recibido:")
        print(f"   Status: {response2.status_code}")
        print(f"   Exito: {data2.get('exito')}")
        
        resumen = data2.get('resumen', {})
        print(f"\nðŸ“Š Resumen:")
        print(f"   total_interacciones: {resumen.get('total_interacciones')}")
        print(f"   interacciones_unicas: {resumen.get('interacciones_unicas')}")
        print(f"   sesiones_activas: {resumen.get('sesiones_activas')}")
        
        # Verificar calidad de texto_semantico
        interacciones = data2.get('interacciones', [])
        print(f"\nðŸ§  AnÃ¡lisis de texto_semantico:")
        for i, interaccion in enumerate(interacciones[:3], 1):
            texto = interaccion.get('texto_semantico', '')
            print(f"\n   [{i}] ID: {interaccion.get('id', 'N/A')}")
            print(f"       Longitud: {len(texto)} chars")
            
            
            # Verificar si es texto rico o genÃ©rico
            es_generico = "InteracciÃ³n en" in texto and "Ã‰xito:" in texto and len(texto) < 100
            es_rico = any(emoji in texto for emoji in ['ðŸ“', 'ðŸ§ ', 'ðŸ“Š', 'ðŸ”¢', 'ðŸ’¾', 'ðŸ“„', 'ðŸŽ¯', 'âœ…'])
            
            print(f"       Tipo: {'âŒ GenÃ©rico' if es_generico else 'âœ… Rico' if es_rico else 'âš ï¸ Intermedio'}")
    else:
        print("âŒ Response es None")

# === TEST 3: Verificar guardado con generador semÃ¡ntico ===
print("\n" + "=" * 80)
print("[TEST 3] Verificar guardado con generador semÃ¡ntico")
print("-" * 80)

from services.memory_service import memory_service

# Simular guardado de una interacciÃ³n rica
test_response = {
    "exito": True,
    "mensaje": "Sistema de memoria semÃ¡ntica funcionando correctamente",
    "interpretacion_semantica": "Test de validaciÃ³n del generador semÃ¡ntico enriquecido",
    "contexto_inteligente": {
        "resumen_inteligente": "Validando que el texto semÃ¡ntico se construya correctamente",
        "tiene_memoria": True
    },
    "total": 5,
    "documentos_relevantes": 10,
    "acciones_sugeridas": ["validar", "verificar", "confirmar"]
}

print("ðŸ“¤ Guardando interacciÃ³n de prueba...")
result = memory_service.registrar_llamada(
    source="test_foundry",
    endpoint="/api/test-memoria",
    method="POST",
    params={"session_id": "test_foundry_session", "agent_id": "test_agent"},
    response_data=test_response,
    success=True
)

print(f"   Resultado: {'âœ… Guardado' if result else 'âŒ FallÃ³'}")

# Recuperar y verificar
print("\nðŸ“¥ Recuperando interacciÃ³n guardada...")
historial = memory_service.get_session_history("test_foundry_session", limit=1)

if historial:
    evento = historial[0]
    texto_guardado = evento.get('texto_semantico', '')
    print(f"   âœ… Recuperado: {evento.get('id')}")
    print(f"   Longitud texto_semantico: {len(texto_guardado)} chars")
    
    
    # Verificar que sea rico
    tiene_emojis = any(emoji in texto_guardado for emoji in ['ðŸ“', 'ðŸ§ ', 'ðŸ“Š', 'ðŸ”¢', 'ðŸ’¾', 'ðŸ“„', 'ðŸŽ¯', 'âœ…'])
    tiene_estructura = '\n' in texto_guardado or '|' in texto_guardado
    
    print(f"\n   AnÃ¡lisis de calidad:")
    print(f"   - Tiene emojis contextuales: {'âœ…' if tiene_emojis else 'âŒ'}")
    print(f"   - Tiene estructura: {'âœ…' if tiene_estructura else 'âŒ'}")
    print(f"   - Longitud adecuada: {'âœ…' if len(texto_guardado) > 100 else 'âŒ'}")
else:
    print("   âŒ No se pudo recuperar")

print("\n" + "=" * 80)
print("TEST COMPLETADO")
print("=" * 80)


