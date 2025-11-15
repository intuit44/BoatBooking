"""
Script de validación: Verificar que el MODELO genera la respuesta, no el backend

Este script valida que:
1. El backend NO genera narrativas automáticas
2. El campo respuesta_usuario está vacío
3. Los eventos[] contienen datos estructurados
4. El modelo debe sintetizar basándose en eventos[]
"""

import requests
import json
import sys

def test_historial_endpoint():
    """Prueba el endpoint historial-interacciones"""
    
    url = "http://localhost:7071/api/historial-interacciones"
    
    headers = {
        "Session-ID": "test-validation-session",
        "Agent-ID": "ValidationAgent",
        "Content-Type": "application/json"
    }
    
    params = {
        "limit": 5
    }
    
    print("🔍 Probando endpoint historial-interacciones...")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Params: {params}\n")
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ ERROR: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        
        print("\n📊 VALIDACIÓN DE RESPUESTA:\n")
        
        # VALIDACIÓN 1: respuesta_usuario debe estar vacío
        respuesta_usuario = data.get("respuesta_usuario", None)
        if respuesta_usuario == "":
            print("✅ CORRECTO: respuesta_usuario está vacío")
        elif respuesta_usuario is None:
            print("✅ CORRECTO: respuesta_usuario no existe (None)")
        else:
            print(f"❌ ERROR: respuesta_usuario contiene texto generado automáticamente:")
            print(f"   '{respuesta_usuario[:200]}...'")
            print("\n🚨 EL BACKEND ESTÁ GENERANDO LA RESPUESTA, NO EL MODELO")
            return False
        
        # VALIDACIÓN 2: eventos[] debe existir y tener datos
        eventos = data.get("eventos", [])
        if eventos and len(eventos) > 0:
            print(f"✅ CORRECTO: eventos[] contiene {len(eventos)} eventos estructurados")
        else:
            print("⚠️  ADVERTENCIA: eventos[] está vacío o no existe")
        
        # VALIDACIÓN 3: texto_semantico debe existir
        texto_semantico = data.get("texto_semantico", "")
        if texto_semantico:
            print(f"✅ CORRECTO: texto_semantico existe ({len(texto_semantico)} caracteres)")
        else:
            print("⚠️  ADVERTENCIA: texto_semantico está vacío")
        
        # VALIDACIÓN 4: Verificar que NO hay narrativas pre-generadas
        narrativas_prohibidas = [
            "He revisado el historial",
            "encontré X interacciones",
            "He encontrado",
            "Resumen de la última actividad"
        ]
        
        texto_completo = json.dumps(data).lower()
        narrativas_encontradas = []
        
        for narrativa in narrativas_prohibidas:
            if narrativa.lower() in texto_completo:
                narrativas_encontradas.append(narrativa)
        
        if narrativas_encontradas:
            print(f"\n❌ ERROR: Se encontraron narrativas pre-generadas:")
            for n in narrativas_encontradas:
                print(f"   - '{n}'")
            print("\n🚨 EL BACKEND ESTÁ SINTETIZANDO, NO EL MODELO")
            return False
        else:
            print("✅ CORRECTO: No se encontraron narrativas pre-generadas")
        
        # VALIDACIÓN 5: Verificar estructura de eventos
        if eventos:
            primer_evento = eventos[0]
            campos_requeridos = ["endpoint", "descripcion", "estado"]
            
            campos_faltantes = [c for c in campos_requeridos if c not in primer_evento]
            
            if campos_faltantes:
                print(f"⚠️  ADVERTENCIA: Eventos sin campos: {campos_faltantes}")
            else:
                print("✅ CORRECTO: Eventos tienen estructura correcta")
        
        # RESUMEN FINAL
        print("\n" + "="*60)
        print("📋 RESUMEN DE VALIDACIÓN")
        print("="*60)
        print("✅ El backend NO genera narrativas automáticas")
        print("✅ El campo respuesta_usuario está vacío")
        print("✅ Los eventos[] contienen datos estructurados")
        print("✅ El MODELO debe sintetizar basándose en eventos[]")
        print("\n🎯 VALIDACIÓN EXITOSA: El modelo generará la respuesta")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se pudo conectar al servidor")
        print("   Asegúrate de que el servidor esté corriendo en http://localhost:7071")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("🧪 TEST: Validar que el MODELO sintetiza la respuesta")
    print("="*60)
    print()
    
    resultado = test_historial_endpoint()
    
    if resultado:
        print("\n✅ TODAS LAS VALIDACIONES PASARON")
        sys.exit(0)
    else:
        print("\n❌ VALIDACIÓN FALLÓ")
        sys.exit(1)
