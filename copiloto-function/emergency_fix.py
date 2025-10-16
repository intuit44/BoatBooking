"""
Emergency Fix - Detener bucle infinito de redirecciones
"""

# 1. DESHABILITAR REDIRECCIONES TEMPORALMENTE
def disable_redirections():
    return """
# En function_app.py - COMENTAR estas líneas:

# if detectar_intencion_semantica(req):
#     return redirect_to_correct_endpoint(req)

# REEMPLAZAR con:
# return revisar_correcciones_http(req)
"""

# 2. LIMITAR CONSULTAS COSMOS DB
def limit_cosmos_calls():
    return """
# Agregar cache simple:
_cosmos_cache = {}

def get_cached_memory(session_id):
    if session_id in _cosmos_cache:
        return _cosmos_cache[session_id]
    return None

def cache_memory(session_id, data):
    _cosmos_cache[session_id] = data
"""

# 3. DETENER BUCLE INMEDIATAMENTE
def stop_infinite_loop():
    return """
# En revisar_correcciones - AGREGAR al inicio:

redirect_count = getattr(req, '_redirect_count', 0)
if redirect_count > 2:
    return func.HttpResponse(
        json.dumps({"error": "Too many redirects"}),
        status_code=200,
        mimetype="application/json"
    )
req._redirect_count = redirect_count + 1
"""

if __name__ == "__main__":
    print("EMERGENCY FIX STEPS:")
    print("1. Disable redirections")
    print("2. Add Cosmos cache") 
    print("3. Stop infinite loops")
    print("4. Restart function app")