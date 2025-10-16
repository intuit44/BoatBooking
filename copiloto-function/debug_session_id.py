#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para detectar dónde se pierde el session_id
"""

import json
import logging
from typing import Dict, Any

def debug_session_flow(req, params: Dict[str, Any], source: str):
    """
    Función de debug para rastrear el flujo del session_id
    """
    
    print(f"\n🔍 DEBUG SESSION FLOW - Source: {source}")
    print("=" * 60)
    
    # 1. Headers del request original
    print("📋 HEADERS ORIGINALES:")
    if hasattr(req, 'headers'):
        for key, value in req.headers.items():
            if 'session' in key.lower() or 'agent' in key.lower():
                print(f"  ✅ {key}: {value}")
        
        session_from_headers = (
            req.headers.get("Session-ID") or
            req.headers.get("X-Session-ID") or
            req.headers.get("x-session-id")
        )
        print(f"  🎯 Session desde headers: {session_from_headers}")
    else:
        print("  ❌ No hay headers disponibles")
    
    # 2. Params del request
    print("\n📋 PARAMS DEL REQUEST:")
    if hasattr(req, 'params'):
        for key, value in req.params.items():
            if 'session' in key.lower() or 'agent' in key.lower():
                print(f"  ✅ {key}: {value}")
        
        session_from_params = (
            req.params.get("Session-ID") or
            req.params.get("session_id")
        )
        print(f"  🎯 Session desde params: {session_from_params}")
    else:
        print("  ❌ No hay params disponibles")
    
    # 3. Params pasados al decorador
    print(f"\n📋 PARAMS PASADOS AL DECORADOR ({len(params)} items):")
    for key, value in params.items():
        if 'session' in key.lower() or 'agent' in key.lower() or 'header' in key.lower():
            print(f"  ✅ {key}: {value}")
    
    session_from_decorator_params = params.get("session_id")
    agent_from_decorator_params = params.get("agent_id")
    
    print(f"  🎯 Session desde decorator params: {session_from_decorator_params}")
    print(f"  🎯 Agent desde decorator params: {agent_from_decorator_params}")
    
    # 4. Atributos internos del request
    print(f"\n📋 ATRIBUTOS INTERNOS DEL REQUEST:")
    if hasattr(req, '__dict__'):
        for key, value in req.__dict__.items():
            if 'session' in key.lower() or 'agent' in key.lower() or 'memoria' in key.lower():
                print(f"  ✅ {key}: {value}")
    
    # 5. Body del request
    print(f"\n📋 BODY DEL REQUEST:")
    try:
        if hasattr(req, 'get_json'):
            body = req.get_json()
            if body:
                for key, value in body.items():
                    if 'session' in key.lower() or 'agent' in key.lower():
                        print(f"  ✅ {key}: {value}")
            else:
                print("  ❌ Body vacío")
        else:
            print("  ❌ No se puede obtener JSON del body")
    except Exception as e:
        print(f"  ❌ Error obteniendo body: {e}")
    
    # 6. Diagnóstico final
    print(f"\n🎯 DIAGNÓSTICO FINAL:")
    
    # Determinar de dónde debería venir el session_id
    expected_session = None
    source_location = "NINGUNA"
    
    if hasattr(req, 'headers') and req.headers.get("Session-ID"):
        expected_session = req.headers.get("Session-ID")
        source_location = "HEADERS"
    elif hasattr(req, 'params') and req.params.get("Session-ID"):
        expected_session = req.params.get("Session-ID")
        source_location = "PARAMS"
    elif params.get("session_id"):
        expected_session = params.get("session_id")
        source_location = "DECORATOR_PARAMS"
    
    print(f"  📍 Session ID esperado: {expected_session}")
    print(f"  📍 Fuente esperada: {source_location}")
    
    if not expected_session:
        print(f"  ❌ PROBLEMA: No se encontró session_id en ninguna fuente")
        print(f"  💡 SUGERENCIA: Verificar que la redirección preserve headers")
    else:
        print(f"  ✅ Session ID disponible desde {source_location}")
    
    print("=" * 60)
    
    return expected_session, source_location

def patch_memory_service_debug():
    """
    Parchea temporalmente memory_service para agregar debug
    """
    
    try:
        from services.memory_service import MemoryService
        
        # Guardar método original
        original_registrar_llamada = MemoryService.registrar_llamada
        
        def debug_registrar_llamada(self, source: str, endpoint: str, method: str, params: Dict[str, Any], response_data: Any, success: bool) -> bool:
            """Versión con debug del registrar_llamada"""
            
            print(f"\n🚨 INTERCEPTADO registrar_llamada - Source: {source}")
            
            # Simular el request desde params si es posible
            class MockRequest:
                def __init__(self, params_dict):
                    self.headers = params_dict.get("headers", {})
                    self.params = params_dict.get("params", {})
                    self.__dict__.update(params_dict)
            
            mock_req = MockRequest(params)
            
            # Ejecutar diagnóstico
            expected_session, source_location = debug_session_flow(mock_req, params, source)
            
            # Llamar método original
            return original_registrar_llamada(self, source, endpoint, method, params, response_data, success)
        
        # Aplicar patch
        MemoryService.registrar_llamada = debug_registrar_llamada
        
        print("✅ Debug patch aplicado a MemoryService.registrar_llamada")
        
    except Exception as e:
        print(f"❌ Error aplicando debug patch: {e}")

if __name__ == "__main__":
    print("🔧 Aplicando debug patch para session_id...")
    patch_memory_service_debug()
    print("✅ Debug patch listo. Ejecuta tu curl ahora.")