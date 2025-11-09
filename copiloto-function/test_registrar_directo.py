# -*- coding: utf-8 -*-
import os
import json

# Cargar env
try:
    with open("local.settings.json", "r", encoding="utf-8") as f:
        settings = json.load(f)
        for key, value in settings.get("Values", {}).items():
            os.environ[key] = str(value)
    print("[OK] Variables cargadas\n")
except Exception as e:
    print(f"[ERROR] {e}\n")

# Test directo
from registrar_respuesta_semantica import registrar_respuesta_semantica

texto_test = "ANALISIS CONTEXTUAL COMPLETO Patron de Actividad Detectado: Actividad diversificada Metricas de Sesion: Total de interacciones analizadas: 2 Tasa de exito: 100.0% Modo de operacion: general"

print(f"[TEST] Registrando texto de {len(texto_test)} chars")
print(f"[TEXTO] {texto_test[:100]}...\n")

resultado = registrar_respuesta_semantica(
    texto_test,
    "test_session_direct",
    "test_agent",
    "copiloto"
)

print(f"\n[RESULTADO] {resultado}")

if resultado:
    print("[OK] Registro exitoso")
    
    # Verificar en Cosmos
    from services.memory_service import memory_service
    historial = memory_service.get_session_history("test_session_direct", limit=5)
    
    respuestas = [d for d in historial if d.get("event_type") == "respuesta_semantica"]
    print(f"[COSMOS] {len(respuestas)} respuestas semanticas encontradas")
    
    if respuestas:
        print(f"[OK] ID: {respuestas[0].get('id')}")
        print(f"[OK] Texto: {respuestas[0].get('texto_semantico')[:80]}...")
else:
    print("[ERROR] Registro fallo")
