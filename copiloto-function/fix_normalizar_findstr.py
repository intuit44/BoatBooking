#!/usr/bin/env python3
with open('function_app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Nueva función
new_lines = [
    'def _normalizar_findstr(comando: str) -> str:\n',
    '    """Convierte findstr con multiples /C: a pipe con type"""\n',
    '    try:\n',
    '        import re\n',
    '        if comando.count("/C:") > 1:\n',
    '            match = re.search(r"findstr\\s+(.+?)\\s+([\\w:\\\\\\\\/.]+\\.py)", comando)\n',
    '            if match:\n',
    '                patterns = match.group(1)\n',
    '                archivo = match.group(2)\n',
    '                return f\'type "{archivo}" | findstr {patterns}\'\n',
    '        return comando\n',
    '    except:\n',
    '        return comando\n',
    '\n',
    '\n'
]

# Buscar inicio de _normalizar_findstr
for i, line in enumerate(lines):
    if 'def _normalizar_findstr' in line:
        # Buscar fin (siguiente def)
        end = i + 1
        for j in range(i+1, len(lines)):
            if lines[j].startswith('def '):
                end = j
                break
        
        # Reemplazar
        lines[i:end] = new_lines
        print(f'Reemplazado desde linea {i} hasta {end}')
        break

with open('function_app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Funcion actualizada')
