#!/usr/bin/env python3
"""
Fix para garantizar que /api/copiloto siempre retorne una respuesta válida.
"""

import re

def fix_copiloto_endpoint():
    """Agrega un return por defecto al final de la función copiloto"""
    
    file_path = "function_app.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar la función copiloto
    pattern = r'(@app\.function_name\(name="copiloto"\).*?@app\.route.*?def copiloto\(req: func\.HttpRequest\) -> func\.HttpResponse:)'
    
    # Verificar si ya tiene un return por defecto al final
    if 'return func.HttpResponse' not in content[content.find('def copiloto'):]:
        print("⚠️ La función copiloto no tiene un return explícito al final")
        
        # Buscar el final de la función (antes de la siguiente definición de función o decorador)
        copiloto_start = content.find('def copiloto(req: func.HttpRequest)')
        if copiloto_start == -1:
            print("❌ No se encontró la función copiloto")
            return False
        
        # Buscar la siguiente función después de copiloto
        next_func = content.find('\n@app.', copiloto_start + 100)
        if next_func == -1:
            next_func = content.find('\ndef ', copiloto_start + 100)
        
        if next_func == -1:
            print("❌ No se pudo determinar el final de la función")
            return False
        
        # Insertar return por defecto antes de la siguiente función
        default_return = '''
    # 🔥 FALLBACK: Garantizar que siempre se retorne una respuesta
    logging.warning("⚠️ copiloto: Llegó al final sin retornar respuesta explícita")
    return func.HttpResponse(
        json.dumps({
            "exito": False,
            "error": "Endpoint no generó respuesta válida",
            "mensaje": "El procesamiento no completó correctamente",
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False),
        mimetype="application/json",
        status_code=500
    )

'''
        
        new_content = content[:next_func] + default_return + content[next_func:]
        
        # Guardar backup
        with open(file_path + '.backup_copiloto_fix', 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Guardar archivo modificado
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Fix aplicado: Se agregó return por defecto al final de copiloto()")
        print(f"📦 Backup guardado en: {file_path}.backup_copiloto_fix")
        return True
    else:
        print("✅ La función copiloto ya tiene returns explícitos")
        return True

if __name__ == "__main__":
    fix_copiloto_endpoint()
