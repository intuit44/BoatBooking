with open('function_app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('lineas_encontradas.txt', 'w', encoding='utf-8') as out:
    for i, line in enumerate(lines):
        if 'comando_retry' in line or ('Out-String' in line and 'PowerShell' in line):
            out.write(f"Linea {i+1}: {line}")

print("Resultados guardados en lineas_encontradas.txt")
