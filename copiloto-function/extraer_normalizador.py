with open('function_app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('normalizador_completo.txt', 'w', encoding='utf-8') as out:
    for i in range(8795, 8810):
        if i < len(lines):
            out.write(f"{i+1}: {lines[i]}")

print("Guardado en normalizador_completo.txt")
