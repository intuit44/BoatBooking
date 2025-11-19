#!/usr/bin/env python3
"""
Fix mínimo v2: Reemplazar solo las asignaciones vacías con lógica condicional simple.
"""

def fix_respuesta_usuario():
    file_path = "function_app.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Línea 4404 (respuesta_struct)
    content = content.replace(
        '            respuesta_struct["mensaje"] = ""\n            # ✅ FIX: Usar respuesta_usuario del backend (ya fusionado en línea 3987 y 5228)',
        '            respuesta_struct["mensaje"] = ""\n            # FIX: Usar respuesta_usuario del backend si no existe\n            if not respuesta_struct.get("respuesta_usuario"):\n                respuesta_struct["respuesta_usuario"] = (\n                    respuesta_struct.get("resumen_automatico")\n                    or (respuesta_struct.get("contexto_inteligente") or {}).get("resumen")\n                    or "Consulta completada"\n                )'
    )
    
    # Fix 2: Línea 4566 (respuesta_struct)
    content = content.replace(
        '                respuesta_struct["mensaje"] = ""\n                # ✅ FIX: Usar respuesta_usuario del backend (ya fusionado en línea 3987 y 5228)',
        '                respuesta_struct["mensaje"] = ""\n                # FIX: Usar respuesta_usuario del backend si no existe\n                if not respuesta_struct.get("respuesta_usuario"):\n                    respuesta_struct["respuesta_usuario"] = (\n                        respuesta_struct.get("resumen_automatico")\n                        or (respuesta_struct.get("contexto_inteligente") or {}).get("resumen")\n                        or "Consulta completada"\n                    )'
    )
    
    # Fix 3: Línea 5108 (respuesta_base)
    content = content.replace(
        '            respuesta_base["texto_semantico"] = texto_semantico\n            # ✅ FIX: Usar respuesta_usuario del backend (ya fusionado en línea 3987 y 5228)',
        '            respuesta_base["texto_semantico"] = texto_semantico\n            # FIX: Usar respuesta_usuario del backend si no existe\n            if not respuesta_base.get("respuesta_usuario"):\n                respuesta_base["respuesta_usuario"] = (\n                    respuesta_base.get("resumen_automatico")\n                    or (respuesta_base.get("contexto_inteligente") or {}).get("resumen")\n                    or "Consulta completada"\n                )'
    )
    
    # Guardar archivo
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("[OK] Fix v2 aplicado en function_app.py")
    print("[INFO] Se reemplazaron 3 ubicaciones donde se sobrescribia respuesta_usuario")

if __name__ == "__main__":
    fix_respuesta_usuario()
