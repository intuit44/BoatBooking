import re
import sys


def validate_function_app(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Buscar todas las funciones
    pattern = r'@app\.function_name\(name="([^"]+)"\)'
    functions = re.findall(pattern, content)

    print(f"Total de funciones encontradas: {len(functions)}")

    # Verificar duplicados
    seen = {}
    duplicates = []
    for func in functions:
        if func in seen:
            duplicates.append(func)
        else:
            seen[func] = 1

    if duplicates:
        print("❌ FUNCIONES DUPLICADAS:")
        for dup in duplicates:
            print(f"  - {dup}")
        return False

    print("✅ No hay funciones duplicadas")

    # Listar todas las funciones
    print("\n📋 Lista de endpoints:")
    for func in sorted(functions):
        print(f"  - {func}")

    return True


if __name__ == "__main__":
    if validate_function_app("function_app.py"):
        sys.exit(0)
    else:
        sys.exit(1)
