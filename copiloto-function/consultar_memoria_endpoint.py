# Endpoint para consultar memoria
@app.function_name(name="consultar_memoria_http")
@app.route(route="consultar-memoria", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def consultar_memoria_http(req: func.HttpRequest) -> func.HttpResponse:
    """Consulta memoria de Cosmos para claves específicas"""
    try:
        body = req.get_json()
        claves = body.get("claves", []) if body else []
        
        if not claves:
            return func.HttpResponse(
                json.dumps({"exito": False, "error": "Parámetro 'claves' requerido"}),
                mimetype="application/json",
                status_code=400
            )
        
        resultados = {}
        for clave in claves:
            valor = _buscar_en_memoria(clave)
            resultados[clave] = valor
        
        return func.HttpResponse(
            json.dumps({
                "exito": True,
                "memoria": resultados,
                "claves_encontradas": [k for k, v in resultados.items() if v],
                "timestamp": datetime.now().isoformat()
            }),
            mimetype="application/json"
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(e)}),
            mimetype="application/json",
            status_code=500
        )