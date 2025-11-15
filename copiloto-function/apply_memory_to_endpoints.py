#!/usr/bin/env python3
"""
Script to apply memory integration to all critical endpoints
"""

import re

# List of critical endpoints that need memory integration
CRITICAL_ENDPOINTS = [
    "autocorregir_http",
    "consultar_memoria_http", 
    "conocimiento_cognitivo_http",
    "contexto_agente_http",
    "copiar_archivo_http",
    "descargar_archivo_http",
    "desplegar_funcion_http",
    "diagnostico_configurar_http",
    "diagnostico_eliminar_http", 
    "diagnostico_listar_http",
    "diagnostico_recursos_completo_http",
    "diagnostico_recursos_http",
    "ejecutar_script_http",
    "ejecutar_script_local_http",
    "escalar_plan_http",
    "gestionar_despliegue_http",
    "info_archivo_http",
    "interpretar_intencion_http",
    "mover_archivo_http",
    "preparar_script_http",
    "promover_http",
    "promocion_reporte_http",
    "proxy_local_http",
    "render_error_http",
    "revisar_correcciones",
    "rollback_correccion",
    "verificar_app_insights",
    "verificar_cosmos",
    "verificar_estado_sistema",
    "verificar_script_http"
]

def apply_memory_to_function_app():
    """Apply memory integration to all critical endpoints"""
    
    # Read the function_app.py file
    with open("function_app.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Track changes made
    changes_made = []
    
    for endpoint in CRITICAL_ENDPOINTS:
        # Pattern to find function definition
        pattern = rf"(@app\.function_name\(name=\"{endpoint}\"\)\s*@app\.route\([^)]+\)\s*def {endpoint}\([^)]+\) -> func\.HttpResponse:)"
        
        # Check if function exists and doesn't already have memory import
        if re.search(pattern, content):
            # Check if it already has memory import
            func_start = re.search(pattern, content).end()
            func_content = content[func_start:func_start+500]  # Look at first 500 chars of function
            
            if "from memory_manual import aplicar_memoria_manual" not in func_content:
                # Add memory import after function definition
                replacement = r"\1\n    from memory_manual import aplicar_memoria_manual"
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"Added memory import to {endpoint}")
    
    # Write back the modified content
    with open("function_app.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Applied memory integration to {len(changes_made)} endpoints:")
    for change in changes_made:
        print(f"  - {change}")

if __name__ == "__main__":
    apply_memory_to_function_app()
