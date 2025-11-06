#!/usr/bin/env python3
"""
Mover el router semántico al inicio del endpoint copiloto
"""

with open('function_app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar la línea donde se define consulta_usuario (línea ~5034)
# Insertar el router INMEDIATAMENTE después

insert_position = None
for i in range(5030, 5050):
    if i < len(lines) and 'consulta_usuario = (' in lines[i]:
        # Buscar el cierre del paréntesis
        for j in range(i, i+10):
            if ')' in lines[j] and 'en qu' in lines[j]:
                insert_position = j + 1
                break
        break

if insert_position:
    router_code = '''
    # ROUTER SEMANTICO DINAMICO - PRIORIDAD MAXIMA
    from intelligent_intent_detector import analizar_intencion_semantica
    clasificacion_router = analizar_intencion_semantica(consulta_usuario) or {}
    endpoint_sugerido = clasificacion_router.get("endpoint_sugerido")
    
    if endpoint_sugerido:
        logging.info(f"ROUTER: Redirigiendo a {endpoint_sugerido} (confianza: {clasificacion_router.get('confianza', 0)})")
        
        resultado_router = invocar_endpoint_directo_seguro(
            endpoint=endpoint_sugerido,
            method="GET",
            params={"query": consulta_usuario, "session_id": session_id}
        )
        
        if resultado_router.get("exito"):
            logging.info(f"ROUTER: Redireccion exitosa a {endpoint_sugerido}")
            return func.HttpResponse(
                json.dumps(resultado_router.get("data", resultado_router), ensure_ascii=False),
                mimetype="application/json",
                status_code=200
            )
        else:
            logging.warning(f"ROUTER: Redireccion fallo, continuando con flujo normal")

'''
    
    lines.insert(insert_position, router_code)
    
    with open('function_app.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"Router insertado en posicion {insert_position}")
else:
    print("No se encontro la posicion de insercion")
