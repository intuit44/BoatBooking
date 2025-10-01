@app.function_name(name="ejecutar_comando_inteligente_http")
@app.route(route="ejecutar-comando-inteligente", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def ejecutar_comando_inteligente_http(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint HTTP para el ejecutor inteligente universal.
    Implementa el flujo: help → validar → ejecutar → autocorregir
    """
    try:
        # Parser ultra-resiliente (igual que modificar-archivo)
        body = {}
        try:
            body = req.get_json() or {}
        except Exception:
            try:
                raw_body = req.get_body()
                if raw_body:
                    body_str = raw_body.decode(errors="ignore")
                    body = json.loads(body_str)
            except Exception:
                body = {}
        
        # Extracción flexible de parámetros
        comando_base = body.get("comando") or body.get("command") or body.get("comando_base") or ""
        intencion = body.get("intencion") or body.get("intention") or body.get("descripcion") or ""
        parametros = body.get("parametros") or body.get("parameters") or body.get("params") or {}
        contexto = body.get("contexto") or body.get("context") or None
        
        # Validación mínima
        if not comando_base:
            return func.HttpResponse(json.dumps({
                "exito": False,
                "error": "Parámetro 'comando' es requerido",
                "ejemplo": {
                    "comando": "az monitor",
                    "intencion": "crear alerta HTTP 500",
                    "parametros": {
                        "resource_group": "mi-grupo",
                        "function_app": "mi-app"
                    }
                }
            }), status_code=400, mimetype="application/json")
        
        if not intencion:
            intencion = "ejecutar comando genérico"
        
        # Importar y ejecutar el comando inteligente
        from ejecutor_inteligente import ejecutar_comando_inteligente
        
        resultado = ejecutar_comando_inteligente(
            comando_base=comando_base,
            intencion=intencion,
            parametros=parametros,
            contexto=contexto
        )
        
        # Enriquecer respuesta
        resultado["endpoint"] = "ejecutar-comando-inteligente"
        resultado["version"] = "1.0-universal"
        resultado["flujo_aplicado"] = "help → validar → ejecutar → autocorregir"
        
        return func.HttpResponse(
            json.dumps(resultado, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        return func.HttpResponse(json.dumps({
            "exito": False,
            "error": f"Error interno: {str(e)}",
            "endpoint": "ejecutar-comando-inteligente",
            "sugerencia": "Verificar formato del request y parámetros"
        }), status_code=500, mimetype="application/json")


@app.function_name(name="crear_alerta_azure_http")
@app.route(route="crear-alerta-azure", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def crear_alerta_azure_http(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint específico para crear alertas de Azure Monitor usando el ejecutor inteligente.
    Ejemplo de cómo usar el wrapper genérico para casos específicos.
    """
    try:
        body = req.get_json() or {}
        
        # Parámetros específicos para Azure Monitor
        resource_group = body.get("resource_group") or "boat-rental-app-group"
        function_app = body.get("function_app") or "copiloto-semantico-func-us2"
        subscription_id = body.get("subscription_id") or "380fa841-83f3-42fe-adc4-582a5ebe139b"
        webhook_url = body.get("webhook_url")
        
        # Usar el wrapper específico
        from ejecutor_inteligente import crear_alerta_azure_monitor
        
        resultado = crear_alerta_azure_monitor(
            resource_group=resource_group,
            function_app=function_app,
            subscription_id=subscription_id,
            webhook_url=webhook_url
        )
        
        # Enriquecer respuesta
        resultado["endpoint"] = "crear-alerta-azure"
        resultado["caso_uso"] = "Azure Monitor Alert para HTTP 500"
        
        return func.HttpResponse(
            json.dumps(resultado, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        return func.HttpResponse(json.dumps({
            "exito": False,
            "error": f"Error: {str(e)}",
            "endpoint": "crear-alerta-azure"
        }), status_code=500, mimetype="application/json")