#!/usr/bin/env python3
"""
Fix v3: Limpiar líneas duplicadas y dejar solo el fix correcto.
"""

def fix_respuesta_usuario():
    file_path = "function_app.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Eliminar líneas duplicadas incorrectas (las que tienen locals() check)
    lines_to_remove = []
    for i, line in enumerate(lines):
        if 'if not respuesta_struct.get("respuesta_usuario") if "respuesta_struct" in locals()' in line:
            # Marcar esta línea y las siguientes 4 para eliminación
            lines_to_remove.extend([i, i+1, i+2, i+3, i+4])
    
    # Eliminar líneas marcadas (en orden inverso para no afectar índices)
    for idx in sorted(set(lines_to_remove), reverse=True):
        if idx < len(lines):
            del lines[idx]
    
    # Guardar archivo limpio
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"[OK] Fix v3 aplicado - eliminadas {len(set(lines_to_remove))} lineas duplicadas")

if __name__ == "__main__":
    fix_respuesta_usuario()
