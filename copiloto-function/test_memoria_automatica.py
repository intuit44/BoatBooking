#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de memoria automática - Verifica que TODOS los endpoints usen memoria automáticamente
"""

import json
import requests
import time
import uuid

def test_endpoints_criticos():
    """
    Prueba endpoints críticos para verificar que usen memoria automáticamente
    """
    
    session_id = f"test_auto_{uuid.uuid4().hex[:8]}"
    agent_id = "AzureSupervisor"
    base_url = "http://localhost:7071"
    
    print(f"🧪 Probando memoria automática en endpoints críticos")
    print(f"📋 Session ID: {session_id}")
    print("=" * 70)
    
    # Endpoints críticos a probar
    endpoints_criticos = [
        {
            "name": "ejecutar-cli",
            "endpoint": "/api/ejecutar-cli", 
            "method": "POST",
            "payload": {
                "comando": "storage account list",
                "session_id": session_id,
                "agent_id": agent_id
            }
        },
        {
            "name": "diagnostico-recursos",
            "endpoint": "/api/diagnostico-recursos",
            "method": "GET",
            "params": {
                "session_id": session_id,
                "agent_id": agent_id
            }
        },
        {
            "name": "gestionar-despliegue", 
            "endpoint": "/api/gestionar-despliegue",
            "method": "POST",
            "payload": {
                "accion": "detectar",
                "session_id": session_id,
                "agent_id": agent_id
            }
        },
        {
            "name": "configurar-app-settings",
            "endpoint": "/api/configurar-app-settings",
            "method": "POST", 
            "payload": {
                "function_app": "test-app",
                "resource_group": "test-rg",
                "settings": {"TEST": "value"},
                "session_id": session_id,
                "agent_id": agent_id
            }
        },
        {
            "name": "bateria-endpoints",
            "endpoint": "/api/bateria-endpoints",
            "method": "GET",
            "params": {
                "session_id": session_id,
                "agent_id": agent_id
            }
        }
    ]
    
    resultados = []
    
    for i, config in enumerate(endpoints_criticos, 1):
        print(f"\n📤 Test {i}: {config['name']}")
        print("-" * 40)
        
        try:
            url = f"{base_url}{config['endpoint']}"
            
            if config["method"] == "GET":
                response = requests.get(url, params=config.get("params", {}), timeout=30)
            else:
                response = requests.post(url, json=config.get("payload", {}), timeout=30)
            
            print(f"📥 Status: {response.status_code}")
            
            # Verificar si la respuesta incluye información de memoria
            try:
                data = response.json()
                memoria_detectada = verificar_memoria_en_respuesta(data)
                
                resultados.append({
                    "endpoint": config["name"],
                    "status": response.status_code,
                    "memoria_detectada": memoria_detectada,
                    "exito": response.status_code < 400
                })
                
                print(f"🧠 Memoria detectada: {'✅' if memoria_detectada else '❌'}")
                
                if memoria_detectada:
                    print(f"📊 Detalles: {extraer_info_memoria(data)}")
                
            except json.JSONDecodeError:
                print("❌ Respuesta no es JSON válido")
                resultados.append({
                    "endpoint": config["name"],
                    "status": response.status_code,
                    "memoria_detectada": False,
                    "exito": False
                })
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            resultados.append({
                "endpoint": config["name"],
                "status": 0,
                "memoria_detectada": False,
                "exito": False,
                "error": str(e)
            })
        
        time.sleep(1)  # Pausa entre llamadas
    
    # Resumen final
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE RESULTADOS")
    print("-" * 30)
    
    total = len(resultados)
    exitosos = sum(1 for r in resultados if r["exito"])
    con_memoria = sum(1 for r in resultados if r["memoria_detectada"])
    
    print(f"Total endpoints probados: {total}")
    print(f"Endpoints exitosos: {exitosos}/{total}")
    print(f"Endpoints con memoria: {con_memoria}/{total}")
    
    print(f"\n📋 Detalle por endpoint:")
    for resultado in resultados:
        status_icon = "✅" if resultado["exito"] else "❌"
        memoria_icon = "🧠" if resultado["memoria_detectada"] else "🚫"
        print(f"  {status_icon} {memoria_icon} {resultado['endpoint']}")
    
    # Verificación de progresión de memoria
    if con_memoria > 0:
        print(f"\n🎯 VERIFICACIÓN DE MEMORIA AUTOMÁTICA:")
        print(f"✅ {con_memoria} endpoints están usando memoria automáticamente")
        print(f"✅ El wrapper automático está funcionando correctamente")
    else:
        print(f"\n⚠️ PROBLEMA DETECTADO:")
        print(f"❌ Ningún endpoint está usando memoria automáticamente")
        print(f"💡 Verificar configuración del memory wrapper")
    
    return resultados

def verificar_memoria_en_respuesta(data: dict) -> bool:
    """
    Verifica si una respuesta contiene indicadores de memoria
    """
    if not isinstance(data, dict):
        return False
    
    # Buscar indicadores de memoria en diferentes ubicaciones
    indicadores = [
        # Metadata de memoria
        data.get("metadata", {}).get("memoria_disponible"),
        data.get("metadata", {}).get("memoria_sesion"),
        data.get("metadata", {}).get("session_info"),
        
        # Contexto de memoria
        data.get("contexto_memoria"),
        
        # Headers de memoria (si están en la respuesta)
        data.get("_memoria_contexto"),
        data.get("_memoria_prompt"),
        
        # Cualquier campo que contenga "session" o "memoria"
        any("session" in str(k).lower() or "memoria" in str(k).lower() 
            for k in data.keys()),
    ]
    
    return any(indicadores)

def extraer_info_memoria(data: dict) -> str:
    """
    Extrae información relevante de memoria de la respuesta
    """
    info_parts = []
    
    metadata = data.get("metadata", {})
    
    if metadata.get("session_info", {}).get("session_id"):
        info_parts.append(f"Session: {metadata['session_info']['session_id'][:8]}...")
    
    if metadata.get("memoria_disponible"):
        info_parts.append("Memoria: Disponible")
    
    memoria_sesion = metadata.get("memoria_sesion", {})
    if memoria_sesion.get("interacciones_previas"):
        info_parts.append(f"Interacciones: {memoria_sesion['interacciones_previas']}")
    
    if data.get("contexto_memoria"):
        info_parts.append("Contexto: Presente")
    
    return " | ".join(info_parts) if info_parts else "Memoria detectada"

if __name__ == "__main__":
    print("🚀 Iniciando verificación de memoria automática en endpoints críticos")
    print("=" * 80)
    
    try:
        resultados = test_endpoints_criticos()
        
        print("\n" + "=" * 80)
        print("🏁 Verificación completada")
        
        # Determinar si el sistema funciona correctamente
        con_memoria = sum(1 for r in resultados if r["memoria_detectada"])
        total = len(resultados)
        
        if con_memoria >= total * 0.8:  # 80% o más con memoria
            print("🎉 ¡ÉXITO! El sistema de memoria automática funciona correctamente")
        elif con_memoria > 0:
            print("⚠️ PARCIAL: Algunos endpoints usan memoria, otros no")
        else:
            print("❌ FALLO: Ningún endpoint está usando memoria automáticamente")
        
        print(f"\n💡 Para verificar un endpoint específico:")
        print(f"   curl -X POST http://localhost:7071/api/ejecutar-cli \\")
        print(f"        -H 'Content-Type: application/json' \\")
        print(f"        -d '{{\"comando\":\"status\",\"session_id\":\"test_123\",\"agent_id\":\"TestAgent\"}}'")
        
    except Exception as e:
        print(f"\n💥 Error ejecutando verificación: {e}")
        print("💡 Verificar que la Function App esté ejecutándose")