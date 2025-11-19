#!/usr/bin/env python3
"""
Fix mínimo: Reemplazar asignaciones de respuesta_usuario="" con lógica que use el campo del backend.
"""

def fix_respuesta_usuario():
    file_path = "function_app.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Líneas a modificar (índice 0-based)
    lines_to_fix = [4403, 4565, 4701, 5107]  # líneas 4404, 4566, 4702, 5108 en editor (1-based)
    
    replacement = '''# ✅ FIX: Usar respuesta_usuario del backend (ya fusionado en línea 3987 y 5228)
            if not respuesta_struct.get("respuesta_usuario") if "respuesta_struct" in locals() else not respuesta_base.get("respuesta_usuario"):
                target = respuesta_struct if "respuesta_struct" in locals() else respuesta_base
                target["respuesta_usuario"] = (
                    target.get("resumen_automatico")
                    or (target.get("contexto_inteligente") or {}).get("resumen")
                    or "Consulta completada"
                )
'''
    
    # Aplicar fix en cada línea
    for idx in lines_to_fix:
        if idx < len(lines) and 'respuesta_usuario"] = ""' in lines[idx]:
            # Reemplazar la línea completa
            indent = len(lines[idx]) - len(lines[idx].lstrip())
            lines[idx] = ' ' * indent + replacement.lstrip()
            print(f"[OK] Linea {idx+1} corregida")
    
    # Guardar archivo
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"\n[OK] Fix aplicado en {file_path}")
    print("[INFO] Lineas modificadas:", [l+1 for l in lines_to_fix])

if __name__ == "__main__":
    fix_respuesta_usuario()
