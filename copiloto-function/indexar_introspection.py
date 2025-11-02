"""
Script para indexar el endpoint de introspección en memoria semántica
Esto permite que el agente lo descubra automáticamente
"""
import requests
import json
from datetime import datetime
import uuid

BASE_URL = "http://localhost:7071"

# Ejemplos de consultas que deben activar introspección
ejemplos_introspection = [
    {
        "id": f"introspection_{uuid.uuid4().hex}",
        "texto_semantico": "Usuario pregunta: ¿Qué validaciones consideras necesarias para autosuficiencia? Respuesta: Consultar /api/introspection para conocer estructura del sistema, endpoints disponibles y capacidades reales.",
        "endpoint": "/api/introspection",
        "tipo": "consulta_estructura",
        "session_id": "training",
        "agent_id": "SystemTrainer"
    },
    {
        "id": f"introspection_{uuid.uuid4().hex}",
        "texto_semantico": "Usuario pregunta: ¿Cómo está conformado el sistema? Respuesta: Usar /api/introspection para obtener inventario completo de endpoints categorizados por función.",
        "endpoint": "/api/introspection",
        "tipo": "consulta_estructura",
        "session_id": "training",
        "agent_id": "SystemTrainer"
    },
    {
        "id": f"introspection_{uuid.uuid4().hex}",
        "texto_semantico": "Usuario pregunta: ¿Qué endpoints existen para monitoreo? Respuesta: Consultar /api/introspection?categoria=monitoreo para listar endpoints de monitoreo disponibles.",
        "endpoint": "/api/introspection",
        "tipo": "consulta_capacidades",
        "session_id": "training",
        "agent_id": "SystemTrainer"
    },
    {
        "id": f"introspection_{uuid.uuid4().hex}",
        "texto_semantico": "Usuario pregunta: ¿Qué capacidades tiene el sistema? Respuesta: Ejecutar /api/introspection para obtener mapa completo de capacidades: diagnóstico, monitoreo, corrección, memoria, configuración.",
        "endpoint": "/api/introspection",
        "tipo": "consulta_capacidades",
        "session_id": "training",
        "agent_id": "SystemTrainer"
    }
]

def indexar_ejemplos():
    """Indexa ejemplos de introspección en Azure AI Search"""
    
    print("🧠 Indexando ejemplos de introspección en memoria semántica...")
    
    url = f"{BASE_URL}/api/indexar-memoria"
    
    payload = {
        "documentos": ejemplos_introspection
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            resultado = response.json()
            print(f"✅ Indexación exitosa: {resultado}")
            return True
        else:
            print(f"❌ Error indexando: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 INDEXANDO ENDPOINT DE INTROSPECCIÓN")
    print("="*70 + "\n")
    
    exito = indexar_ejemplos()
    
    if exito:
        print("\n✅ Introspección indexada correctamente")
        print("El agente ahora puede descubrir /api/introspection automáticamente")
    else:
        print("\n❌ Falló la indexación")
        print("Verifica que el servidor esté corriendo: func start")
