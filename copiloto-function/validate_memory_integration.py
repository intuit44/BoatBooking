#!/usr/bin/env python3
"""
Script de validación de integración de memoria en endpoints
Verifica que todos los endpoints críticos tengan memoria pre-check implementada
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List

# Configuración
BASE_URL = "http://localhost:7071"  # Cambiar si es necesario
ENDPOINTS_TO_TEST = [
    {
        "name": "copiloto",
        "url": "/api/copiloto", 
        "method": "POST",
        "body": {"consulta": "¿Qué puedes hacer?"},
        "expected_memory": True
    },
    {
        "name": "status", 
        "url": "/api/status",
        "method": "GET", 
        "body": None,
        "expected_memory": True
    },
    {
        "name": "ejecutar",
        "url": "/api/ejecutar",
        "method": "POST",
        "body": {"comando": "echo 'test'"},
        "expected_memory": True
    },
    {
        "name": "hybrid",
        "url": "/api/hybrid", 
        "method": "POST",
        "body": {"consulta": "test hybrid"},
        "expected_memory": True
    },
    {
        "name": "escribir-archivo",
        "url": "/api/escribir-archivo",
        "method": "POST", 
        "body": {"ruta": "test.txt", "contenido": "test content"},
        "expected_memory": True
    },
    {
        "name": "leer-archivo",
        "url": "/api/leer-archivo",
        "method": "GET",
        "body": None,
        "params": {"ruta": "README.md"},
        "expected_memory": True
    },
    {
        "name": "modificar-archivo", 
        "url": "/api/modificar-archivo",
        "method": "POST",
        "body": {"ruta": "test.txt", "operacion": "agregar_final", "contenido": "test"},
        "expected_memory": True
    }
]

def test_endpoint_memory_integration(endpoint: Dict) -> Dict:
    """Prueba un endpoint específico para validar integración de memoria"""
    
    print(f"\n🧪 Probando {endpoint['name']}...")
    
    try:
        url = f"{BASE_URL}{endpoint['url']}"
        
        # Preparar request
        kwargs = {
            "timeout": 30,
            "headers": {"Content-Type": "application/json"}
        }
        
        if endpoint["method"] == "POST" and endpoint["body"]:
            kwargs["json"] = endpoint["body"]
        elif endpoint.get("params"):
            kwargs["params"] = endpoint["params"]
        
        # Ejecutar request
        start_time = time.time()
        
        if endpoint["method"] == "GET":
            response = requests.get(url, **kwargs)
        elif endpoint["method"] == "POST":
            response = requests.post(url, **kwargs)
        else:
            return {"error": f"Método {endpoint['method']} no soportado"}
        
        duration = time.time() - start_time
        
        # Analizar respuesta
        result = {
            "endpoint": endpoint["name"],
            "url": endpoint["url"],
            "status_code": response.status_code,
            "duration": f"{duration:.2f}s",
            "success": response.status_code == 200
        }
        
        if response.status_code == 200:
            try:
                data = response.json()
                result["response_data"] = data
                
                # Verificar indicadores de memoria
                memory_indicators = check_memory_indicators(data)
                result.update(memory_indicators)
                
                print(f"  ✅ Status: {response.status_code}")
                print(f"  ⏱️  Tiempo: {duration:.2f}s")
                print(f"  🧠 Memoria: {'✅' if memory_indicators['has_memory_integration'] else '❌'}")
                
            except json.JSONDecodeError:
                result["error"] = "Respuesta no es JSON válido"
                result["response_text"] = response.text[:200]
                print(f"  ❌ Error: Respuesta no JSON")
        else:
            result["error"] = f"HTTP {response.status_code}"
            result["response_text"] = response.text[:200]
            print(f"  ❌ Error: HTTP {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        result = {
            "endpoint": endpoint["name"],
            "error": "No se pudo conectar al servidor",
            "suggestion": "Verifica que Azure Functions esté ejecutándose en localhost:7071"
        }
        print(f"  ❌ Error: No se pudo conectar")
        
    except Exception as e:
        result = {
            "endpoint": endpoint["name"], 
            "error": str(e),
            "type": type(e).__name__
        }
        print(f"  ❌ Error: {str(e)}")
    
    return result

def check_memory_indicators(data: Dict) -> Dict:
    """Verifica indicadores de que la memoria está integrada"""
    
    indicators = {
        "has_memory_integration": False,
        "memory_fields_found": [],
        "memory_score": 0
    }
    
    # Buscar campos que indican integración de memoria
    memory_fields = [
        "memoria_aplicada", "contexto_recuperado", "interacciones_previas",
        "sesion_id", "memoria_previa", "contexto_semantico", 
        "memoria_enriquecida", "continuidad_sesion"
    ]
    
    def search_nested(obj, path=""):
        """Busca campos de memoria en objetos anidados"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Verificar si la clave indica memoria
                if any(field in key.lower() for field in ["memoria", "memory", "contexto", "context", "sesion", "session"]):
                    indicators["memory_fields_found"].append(current_path)
                    indicators["memory_score"] += 1
                
                # Buscar recursivamente
                search_nested(value, current_path)
                
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                search_nested(item, f"{path}[{i}]")
    
    # Buscar en toda la respuesta
    search_nested(data)
    
    # Verificar campos específicos conocidos
    for field in memory_fields:
        if field in str(data).lower():
            if field not in [f.split('.')[-1] for f in indicators["memory_fields_found"]]:
                indicators["memory_fields_found"].append(field)
                indicators["memory_score"] += 1
    
    # Determinar si tiene integración
    indicators["has_memory_integration"] = indicators["memory_score"] > 0
    
    return indicators

def generate_report(results: List[Dict]) -> str:
    """Genera reporte de validación"""
    
    report = f"""
# 📊 REPORTE DE VALIDACIÓN DE MEMORIA
**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Endpoints probados:** {len(results)}

## 📈 Resumen General
"""
    
    successful = sum(1 for r in results if r.get("success", False))
    with_memory = sum(1 for r in results if r.get("has_memory_integration", False))
    
    report += f"""
- ✅ **Endpoints funcionando:** {successful}/{len(results)}
- 🧠 **Con integración de memoria:** {with_memory}/{len(results)}
- 📊 **Tasa de éxito:** {(successful/len(results)*100):.1f}%
- 🎯 **Memoria integrada:** {(with_memory/len(results)*100):.1f}%

## 📋 Detalle por Endpoint
"""
    
    for result in results:
        name = result.get("endpoint", "Unknown")
        status = "✅" if result.get("success") else "❌"
        memory = "🧠" if result.get("has_memory_integration") else "🚫"
        duration = result.get("duration", "N/A")
        
        report += f"""
### {status} {name}
- **URL:** {result.get('url', 'N/A')}
- **Status:** {result.get('status_code', 'N/A')}
- **Tiempo:** {duration}
- **Memoria:** {memory} {'Integrada' if result.get('has_memory_integration') else 'No detectada'}
"""
        
        if result.get("memory_fields_found"):
            report += f"- **Campos encontrados:** {', '.join(result['memory_fields_found'])}\n"
        
        if result.get("error"):
            report += f"- **Error:** {result['error']}\n"
    
    # Recomendaciones
    report += f"""
## 🔧 Recomendaciones

"""
    
    if with_memory < len(results):
        missing = len(results) - with_memory
        report += f"- ⚠️  **{missing} endpoints** necesitan integración de memoria\n"
    
    if successful < len(results):
        failing = len(results) - successful  
        report += f"- 🚨 **{failing} endpoints** no están respondiendo correctamente\n"
    
    if with_memory == len(results) and successful == len(results):
        report += "- 🎉 **¡Excelente!** Todos los endpoints tienen memoria integrada y funcionan correctamente\n"
    
    return report

def main():
    """Función principal de validación"""
    
    print("🚀 INICIANDO VALIDACIÓN DE INTEGRACIÓN DE MEMORIA")
    print("=" * 60)
    
    results = []
    
    for endpoint in ENDPOINTS_TO_TEST:
        result = test_endpoint_memory_integration(endpoint)
        results.append(result)
        time.sleep(1)  # Pausa entre requests
    
    # Generar reporte
    report = generate_report(results)
    
    # Guardar reporte
    report_file = f"memory_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\n" + "=" * 60)
    print(f"📄 Reporte guardado en: {report_file}")
    print("\n" + report)
    
    # Resumen final
    successful = sum(1 for r in results if r.get("success", False))
    with_memory = sum(1 for r in results if r.get("has_memory_integration", False))
    
    if with_memory == len(results) and successful == len(results):
        print("\n🎉 ¡VALIDACIÓN EXITOSA! Todos los endpoints funcionan con memoria integrada.")
        return True
    else:
        print(f"\n⚠️  VALIDACIÓN PARCIAL: {with_memory}/{len(results)} con memoria, {successful}/{len(results)} funcionando")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)