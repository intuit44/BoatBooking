#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnóstico y Fix para bing_fallback_guard.py
Verifica si está generando payloads incorrectos para ejecutar_cli_http
"""

import os
import json
from pathlib import Path
from datetime import datetime

def verificar_bing_fallback_guard():
    """Verifica si existe bing_fallback_guard.py y analiza su código"""
    print("Verificando bing_fallback_guard.py...")
    
    # Buscar el archivo
    posibles_rutas = [
        Path("bing_fallback_guard.py"),
        Path("services/bing_fallback_guard.py"),
        Path("../bing_fallback_guard.py"),
        Path("copiloto-function/bing_fallback_guard.py")
    ]
    
    archivo_encontrado = None
    for ruta in posibles_rutas:
        if ruta.exists():
            archivo_encontrado = ruta
            break
    
    if not archivo_encontrado:
        print("   bing_fallback_guard.py NO ENCONTRADO")
        print("   Esto podria ser la causa del problema")
        return False
    
    print(f"   Encontrado: {archivo_encontrado}")
    
    # Leer y analizar el contenido
    try:
        contenido = archivo_encontrado.read_text(encoding='utf-8')
        
        # Buscar patrones problemáticos
        problemas = []
        
        if '"intencion"' in contenido:
            problemas.append("Usa campo 'intencion' en lugar de 'comando'")
        
        if 'ejecutar-cli' in contenido or 'ejecutar_cli' in contenido:
            if '"comando"' not in contenido:
                problemas.append("Referencia ejecutar-cli pero no usa campo 'comando'")
        
        if 'buscar en bing' in contenido.lower():
            problemas.append("Contiene texto 'buscar en bing' que puede causar problemas")
        
        if problemas:
            print("   PROBLEMAS DETECTADOS:")
            for problema in problemas:
                print(f"      - {problema}")
            return False
        else:
            print("   No se detectaron problemas obvios")
            return True
            
    except Exception as e:
        print(f"   Error leyendo archivo: {e}")
        return False

def generar_reglas_routing():
    """Genera reglas claras de routing para cada endpoint"""
    print("\nGenerando reglas de routing...")
    
    reglas = {
        "endpoints": {
            "/api/ejecutar-cli": {
                "formato_esperado": {"comando": "az storage account list"},
                "campos_requeridos": ["comando"],
                "campos_prohibidos": ["intencion"],
                "descripcion": "Solo acepta comandos Azure CLI directos"
            },
            "/api/hybrid": {
                "formato_esperado": {"agent_response": "comando o JSON embebido"},
                "campos_requeridos": ["agent_response"],
                "descripcion": "Procesa respuestas de agentes con parsing inteligente"
            },
            "/api/ejecutar": {
                "formato_esperado": {"intencion": "dashboard", "parametros": {}},
                "campos_requeridos": ["intencion"],
                "descripcion": "Procesa intenciones semánticas"
            }
        },
        "reglas_fallback": {
            "si_comando_cli": "usar /api/ejecutar-cli con {comando: 'az ...'}",
            "si_intencion_semantica": "usar /api/ejecutar con {intencion: '...'}",
            "si_respuesta_agente": "usar /api/hybrid con {agent_response: '...'}"
        }
    }
    
    # Guardar reglas
    with open("routing_rules.json", "w", encoding='utf-8') as f:
        json.dump(reglas, f, indent=2, ensure_ascii=False)
    
    print("   Reglas guardadas en routing_rules.json")
    return reglas

def generar_fix_recomendaciones():
    """Genera recomendaciones específicas de fix"""
    print("\nGenerando recomendaciones de fix...")
    
    recomendaciones = [
        {
            "problema": "Payload con 'intencion' enviado a /api/ejecutar-cli",
            "solucion": "Cambiar a {\"comando\": \"az storage account list\"}",
            "codigo_ejemplo": '''
# ❌ INCORRECTO
payload = {"intencion": "buscar en bing"}
requests.post("/api/ejecutar-cli", json=payload)

# ✅ CORRECTO
payload = {"comando": "az storage account list"}
requests.post("/api/ejecutar-cli", json=payload)
'''
        },
        {
            "problema": "bing_fallback_guard.py genera payloads incorrectos",
            "solucion": "Actualizar la lógica de generación de payloads",
            "codigo_ejemplo": '''
# En bing_fallback_guard.py
def generar_payload_cli(comando_azure):
    return {
        "comando": comando_azure,  # ✅ Usar 'comando'
        # "intencion": "..."       # ❌ NO usar 'intencion'
    }
'''
        },
        {
            "problema": "Routing incorrecto de intenciones",
            "solucion": "Usar el endpoint correcto según el tipo de payload",
            "codigo_ejemplo": '''
# Routing correcto
if es_comando_cli(payload):
    endpoint = "/api/ejecutar-cli"
    payload = {"comando": comando}
elif es_intencion_semantica(payload):
    endpoint = "/api/ejecutar"
    payload = {"intencion": intencion}
elif es_respuesta_agente(payload):
    endpoint = "/api/hybrid"
    payload = {"agent_response": respuesta}
'''
        }
    ]
    
    # Guardar recomendaciones
    with open("fix_recomendaciones.json", "w", encoding='utf-8') as f:
        json.dump(recomendaciones, f, indent=2, ensure_ascii=False)
    
    print("   Recomendaciones guardadas en fix_recomendaciones.json")
    
    # Mostrar resumen
    print("\nRECOMENDACIONES PRINCIPALES:")
    for i, rec in enumerate(recomendaciones, 1):
        print(f"   {i}. {rec['problema']}")
        print(f"      -> {rec['solucion']}")
    
    return recomendaciones

def verificar_function_app():
    """Verifica que function_app.py tenga la validación correcta"""
    print("\nVerificando function_app.py...")
    
    try:
        with open("function_app.py", "r", encoding='utf-8') as f:
            contenido = f.read()
        
        # Buscar la función ejecutar_cli_http
        if 'def ejecutar_cli_http' not in contenido:
            print("   funcion ejecutar_cli_http no encontrada")
            return False
        
        # Verificar validaciones críticas
        validaciones = [
            ('body.get("intencion")', "Detecta campo 'intencion'"),
            ('status_code=422', "Devuelve status 422 para intenciones"),
            ('logging.warning(f"[DEBUG] Payload recibido: {body}")', "Logging de debug"),
            ('"Este endpoint no maneja intenciones"', "Mensaje de error claro")
        ]
        
        validaciones_encontradas = 0
        for patron, descripcion in validaciones:
            if patron in contenido:
                print(f"   OK: {descripcion}")
                validaciones_encontradas += 1
            else:
                print(f"   FALTA: {descripcion}")
        
        if validaciones_encontradas == len(validaciones):
            print("   Todas las validaciones estan implementadas")
            return True
        else:
            print(f"   Faltan {len(validaciones) - validaciones_encontradas} validaciones")
            return False
            
    except Exception as e:
        print(f"   Error leyendo function_app.py: {e}")
        return False

def main():
    """Ejecuta el diagnóstico completo"""
    print("=" * 60)
    print("DIAGNOSTICO Y FIX - bing_fallback_guard")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    resultados = {
        "bing_fallback_guard": verificar_bing_fallback_guard(),
        "function_app": verificar_function_app()
    }
    
    # Generar artefactos
    reglas = generar_reglas_routing()
    recomendaciones = generar_fix_recomendaciones()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN DEL DIAGNOSTICO")
    print("=" * 60)
    
    for componente, estado in resultados.items():
        status = "OK" if estado else "PROBLEMA"
        print(f"{componente}: {status}")
    
    if all(resultados.values()):
        print("\nDIAGNOSTICO COMPLETO")
        print("Todos los componentes estan correctos")
    else:
        print("\nPROBLEMAS DETECTADOS")
        print("Revisar los componentes marcados")
    
    print("\nARCHIVOS GENERADOS:")
    print("   - routing_rules.json - Reglas de routing")
    print("   - fix_recomendaciones.json - Recomendaciones de fix")
    
    print("\nPROXIMOS PASOS:")
    print("   1. Ejecutar test_cli_validation.py para validar")
    print("   2. Si hay problemas, aplicar las recomendaciones")
    print("   3. Verificar que bing_fallback_guard use el formato correcto")

if __name__ == "__main__":
    main()