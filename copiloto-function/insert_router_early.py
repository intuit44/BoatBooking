#!/usr/bin/env python3
with open('function_app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Insertar router en línea 5042 (después de definir consulta_usuario)
router_code = '''
        # ROUTER SEMANTICO DINAMICO - EJECUTAR PRIMERO
        from intelligent_intent_detector import analizar_intencion_semantica
        clasificacion_router = analizar_intencion_semantica(consulta_usuario) or {}
        endpoint_sugerido_router = clasificacion_router.get("endpoint_sugerido")
        
        if endpoint_sugerido_router:
            logging.info(f"ROUTER EARLY: Redirigiendo a {endpoint_sugerido_router}")
            
            resultado_router = invocar_endpoint_directo_seguro(
                endpoint=endpoint_sugerido_router,
                method="GET",
                params={"query": consulta_usuario, "session_id": session_id}
            )
            
            if resultado_router.get("exito"):
                logging.info(f"ROUTER EARLY: Redireccion exitosa")
                return func.HttpResponse(
                    json.dumps(resultado_router.get("data", resultado_router), ensure_ascii=False),
                    mimetype="application/json",
                    status_code=200
                )

'''

lines.insert(5042, router_code)

with open('function_app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Router insertado en linea 5042")
