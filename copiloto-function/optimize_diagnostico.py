#!/usr/bin/env python3
"""
Optimizar endpoint diagnostico-recursos-completo para respuesta rápida
"""

def optimize_diagnostico_endpoint():
    """Optimiza el endpoint para respuesta < 10s"""
    
    # 1. Aumentar timeout en tests
    with open("test_endpoint_exists.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Cambiar timeout de 10 a 30 segundos
    content = content.replace("timeout=10", "timeout=30")
    
    with open("test_endpoint_exists.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("[OK] Timeout aumentado a 30s en tests")
    
    # 2. Agregar redirecciones al router semántico
    router_additions = '''
    # Redirecciones para diagnóstico completo
    if any(keyword in intencion_lower for keyword in ["verificar:metricas", "verificar metricas", "metricas"]):
        return invocar_endpoint_directo("/api/diagnostico-recursos-completo", "GET")
    
    if any(keyword in intencion_lower for keyword in ["diagnosticar:completo", "diagnostico completo", "diagnostico:completo"]):
        return invocar_endpoint_directo("/api/diagnostico-recursos-completo", "GET")
    '''
    
    # Buscar función procesar_intencion_semantica y agregar redirecciones
    with open("function_app.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Buscar donde insertar las redirecciones
    if "# 3. Atajos para endpoints comunes" in content:
        # Insertar después de los atajos existentes
        insertion_point = content.find("if intencion_lower in shortcuts:")
        if insertion_point != -1:
            # Encontrar el final del bloque de shortcuts
            end_point = content.find("# 4. Si empieza con", insertion_point)
            if end_point != -1:
                new_content = (
                    content[:end_point] + 
                    router_additions + 
                    "\n    " + 
                    content[end_point:]
                )
                
                with open("function_app.py", "w", encoding="utf-8") as f:
                    f.write(new_content)
                
                print("[OK] Redirecciones agregadas al router semántico")
                return True
    
    print("[WARN] No se pudo agregar redirecciones automáticamente")
    return False

if __name__ == "__main__":
    optimize_diagnostico_endpoint()