with open('function_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Extraer desde la posición encontrada
start = 350000
end = 351500

seccion = content[start:end]

# Guardar en archivo
with open('seccion_reintento.txt', 'w', encoding='utf-8') as f:
    f.write(seccion)

print("Sección guardada en seccion_reintento.txt")
print(f"Longitud: {len(seccion)} caracteres")
