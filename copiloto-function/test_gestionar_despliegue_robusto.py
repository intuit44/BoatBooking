#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 SCRIPT DE PRUEBAS PARA EL SISTEMA ROBUSTO DE GESTIÓN DE DESPLIEGUES

Valida que el endpoint /api/gestionar-despliegue sea completamente robusto y adaptativo.
"""

import json
import requests
import time
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:7071"
ENDPOINT = "/api/gestionar-despliegue"
URL = f"{BASE_URL}{ENDPOINT}"

def test_payload(nombre: str, payload: dict, esperado_exito: bool = True):
    """Prueba un payload específico"""
    print(f"\n🧪 Probando: {nombre}")
    print(f"📤 Payload: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        response = requests.post(URL, json=payload, timeout=30)
        
        print(f"📊 Status: {response.status_code}")
        
        try:
            result = response.json()
            print(f"📥 Respuesta: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            exito_real = result.get("exito", False)
            if exito_real == esperado_exito:
                print(f"✅ ÉXITO: Comportamiento esperado")
                return True
            else:
                print(f"❌ FALLO: Esperado exito={esperado_exito}, obtenido={exito_real}")
                return False
                
        except json.JSONDecodeError:
            print(f"📥 Respuesta (texto): {response.text}")
            return response.status_code < 400 if esperado_exito else response.status_code >= 400
            
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        return False

def main():
    """Ejecuta todas las pruebas del sistema robusto"""
    
    print("🚀 INICIANDO PRUEBAS DEL SISTEMA ROBUSTO DE GESTIÓN DE DESPLIEGUES")
    print(f"🎯 Endpoint: {URL}")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    
    pruebas = []
    
    # === PRUEBAS DE ROBUSTEZ BÁSICA ===
    
    # 1. Payload vacío (debe usar defaults)
    pruebas.append(("Payload vacío", {}, True))
    
    # 2. Payload mínimo con acción
    pruebas.append(("Acción detectar", {"accion": "detectar"}, True))
    
    # 3. Alias en inglés
    pruebas.append(("Alias inglés", {"action": "detect"}, True))
    
    # 4. Múltiples sinónimos
    pruebas.append(("Sinónimos múltiples", {"comando": "check"}, True))
    
    # === PRUEBAS DE FORMATOS DE AGENTES ===
    
    # 5. Formato Foundry típico
    pruebas.append(("Formato Foundry", {
        "action": "deploy",
        "version": "v1.2.3",
        "platform": "foundry",
        "agent": "AzureSupervisor"
    }, True))
    
    # 6. Formato CodeGPT típico
    pruebas.append(("Formato CodeGPT", {
        "accion": "desplegar",
        "tag": "v1.2.3",
        "plataforma": "codegpt",
        "agente": "Deploy_Agent",
        "configuracion": {
            "modelo": "gpt-4o-mini",
            "temperatura": 0.2,
            "descripcion": "Agente para tareas DevOps",
            "herramientas": ["leer-archivo", "ejecutar-cli", "deploy"],
            "system_prompt": "Eres un asistente especializado en despliegues automáticos"
        }
    }, True))
    
    # 7. Formato CLI típico
    pruebas.append(("Formato CLI", {
        "command": "deploy",
        "tag": "v1.2.3"
    }, True))
    
    # === PRUEBAS DE CASOS PROBLEMÁTICOS ===
    
    # 8. Acción no reconocida (debe adaptarse)
    pruebas.append(("Acción no reconocida", {
        "accion": "actualizar",
        "plataforma": "foundry",
        "agente": "AzureSupervisor",
        "cambios": {
            "temperatura": 0.35,
            "agregar_herramientas": ["diagnostico-recursos"],
            "remover_herramientas": ["bateria-endpoints"]
        }
    }, True))  # Debe adaptarse, no fallar
    
    # 9. Acción completamente inventada
    pruebas.append(("Acción inventada", {
        "accion": "reiniciar",
        "plataforma": "codegpt",
        "agente": "Deploy_Agent"
    }, True))  # Debe usar detectar por defecto
    
    # 10. Payload con campos extra
    pruebas.append(("Campos extra", {
        "accion": "desplegar",
        "tag": "v1.2.3",
        "campo_extra": "valor_extra",
        "otro_campo": {"nested": "value"},
        "array_campo": [1, 2, 3]
    }, True))
    
    # === PRUEBAS DE VALIDACIÓN ===
    
    # 11. Rollback sin tag_anterior (debe dar error con sugerencias)
    pruebas.append(("Rollback sin tag", {
        "accion": "rollback"
    }, False))  # Debe fallar pero con sugerencias
    
    # 12. Rollback con tag_anterior (debe funcionar)
    pruebas.append(("Rollback válido", {
        "accion": "rollback",
        "tag_anterior": "v1.2.2"
    }, True))
    
    # === PRUEBAS DE DEDUCCIÓN INTELIGENTE ===
    
    # 13. Solo tag (debe deducir desplegar)
    pruebas.append(("Solo tag", {"tag": "v1.2.3"}, True))
    
    # 14. Solo tag_anterior (debe deducir rollback)
    pruebas.append(("Solo tag anterior", {"tag_anterior": "v1.2.2"}, True))
    
    # 15. Campo preparar (debe deducir preparar)
    pruebas.append(("Campo preparar", {"preparar": True}, True))
    
    # === PRUEBAS DE TOLERANCIA A ERRORES ===
    
    # 16. JSON malformado simulado con campos válidos
    pruebas.append(("Campos desordenados", {
        "timeout": 600,
        "forzar": True,
        "accion": "preparar",
        "configuracion": {"test": True},
        "tag": "v1.2.3"
    }, True))
    
    # 17. Mezcla de sinónimos
    pruebas.append(("Mezcla sinónimos", {
        "action": "deploy",  # inglés
        "tag": "v1.2.3",     # español
        "platform": "foundry", # inglés
        "agente": "TestAgent"   # español
    }, True))
    
    # === EJECUTAR TODAS LAS PRUEBAS ===
    
    resultados = []
    total_pruebas = len(pruebas)
    
    for i, (nombre, payload, esperado) in enumerate(pruebas, 1):
        print(f"\n{'='*60}")
        print(f"📋 Prueba {i}/{total_pruebas}")
        
        resultado = test_payload(nombre, payload, esperado)
        resultados.append((nombre, resultado))
        
        # Pausa entre pruebas para no saturar
        time.sleep(0.5)
    
    # === RESUMEN FINAL ===
    
    print(f"\n{'='*60}")
    print("📊 RESUMEN DE PRUEBAS")
    print(f"{'='*60}")
    
    exitosas = sum(1 for _, resultado in resultados if resultado)
    fallidas = total_pruebas - exitosas
    
    print(f"✅ Pruebas exitosas: {exitosas}/{total_pruebas}")
    print(f"❌ Pruebas fallidas: {fallidas}/{total_pruebas}")
    print(f"📈 Tasa de éxito: {(exitosas/total_pruebas)*100:.1f}%")
    
    if fallidas > 0:
        print(f"\n❌ PRUEBAS FALLIDAS:")
        for nombre, resultado in resultados:
            if not resultado:
                print(f"  - {nombre}")
    
    print(f"\n🎯 CONCLUSIÓN:")
    if exitosas == total_pruebas:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON! El sistema es completamente robusto.")
    elif exitosas >= total_pruebas * 0.9:
        print("✅ Sistema muy robusto (>90% de pruebas exitosas)")
    elif exitosas >= total_pruebas * 0.8:
        print("⚠️ Sistema robusto con algunas mejoras necesarias (>80% de pruebas exitosas)")
    else:
        print("❌ Sistema necesita mejoras significativas (<80% de pruebas exitosas)")
    
    print(f"\n⏰ Pruebas completadas: {datetime.now().isoformat()}")
    
    return exitosas == total_pruebas

if __name__ == "__main__":
    try:
        exito = main()
        exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Pruebas interrumpidas por el usuario")
        exit(1)
    except Exception as e:
        print(f"\n\n💥 Error crítico en las pruebas: {str(e)}")
        exit(1)