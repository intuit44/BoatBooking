#!/usr/bin/env python3
with open('function_app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar y eliminar líneas 5173-5175
output_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Si encontramos el comentario duplicado, saltar 3 líneas
    if i >= 5172 and i <= 5175 and ('Justo despu' in line or 'consulta_usuario) or {}' in line):
        i += 1
        continue
    
    # Cambiar consulta_usuario por consulta en params
    if 'params={"query": consulta_usuario' in line:
        line = line.replace('consulta_usuario', 'consulta')
    
    output_lines.append(line)
    i += 1

with open('function_app.py', 'w', encoding='utf-8') as f:
    f.writelines(output_lines)

print(f"Procesadas {len(output_lines)} lineas")
