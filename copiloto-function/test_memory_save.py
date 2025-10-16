#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple para verificar si el sistema de memoria está guardando correctamente
"""

import json
from datetime import datetime
from services.memory_service import memory_service

def test_memory_save():
    """Test básico de guardado en memoria"""
    
    print("Iniciando test de memoria...")
    
    # Datos de prueba
    session_id = "test_session_manual_123"
    agent_id = "TestAgent"
    
    # Simular llamada a endpoint
    llamada_data = {
        "source": "test_manual",
        "endpoint": "/api/copiloto",
        "method": "POST",
        "params": {
            "session_id": session_id,
            "agent_id": agent_id,
            "comando": "test manual"
        },
        "response_data": {"exito": True, "mensaje": "Test manual"},
        "success": True
    }
    
    print(f"Guardando interaccion para session: {session_id}")
    
    # Intentar guardar
    resultado = memory_service.registrar_llamada(
        source="test_manual",
        endpoint="/api/copiloto", 
        method="POST",
        params={
            "session_id": session_id,
            "agent_id": agent_id,
            "comando": "test manual"
        },
        response_data={"exito": True, "mensaje": "Test manual"},
        success=True
    )
    
    print(f"Resultado del guardado: {'OK' if resultado else 'FAIL'}")
    
    # Intentar recuperar
    print(f"Buscando historial para session: {session_id}")
    
    historial = memory_service.get_session_history(session_id, limit=10)
    
    print(f"Historial encontrado: {len(historial)} interacciones")
    
    if historial:
        print("Ultimas interacciones:")
        for i, item in enumerate(historial[:3]):
            print(f"  {i+1}. {item.get('timestamp', 'N/A')} - {item.get('event_type', 'N/A')}")
    else:
        print("No se encontraron interacciones")
    
    return resultado, len(historial)

if __name__ == "__main__":
    resultado_guardado, total_encontrado = test_memory_save()
    
    print(f"\nResumen del test:")
    print(f"   Guardado exitoso: {'OK' if resultado_guardado else 'FAIL'}")
    print(f"   Interacciones encontradas: {total_encontrado}")
    
    if resultado_guardado and total_encontrado > 0:
        print("Sistema de memoria funcionando correctamente!")
    else:
        print("Sistema de memoria tiene problemas")