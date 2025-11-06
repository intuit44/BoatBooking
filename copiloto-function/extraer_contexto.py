with open('function_app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Extraer líneas 8770-8790
start = 8770 - 1
end = 8790

with open('contexto_retry.txt', 'w', encoding='utf-8') as out:
    for i in range(start, min(end, len(lines))):
        out.write(f"{i+1}: {lines[i]}")

print("Contexto guardado en contexto_retry.txt")
