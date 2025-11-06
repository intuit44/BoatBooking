with open('function_app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar el bloque del normalizador PowerShell (después de la ejecución)
for i in range(8790, 8810):
    if i < len(lines):
        print(f"{i+1}: {lines[i].rstrip()}")
