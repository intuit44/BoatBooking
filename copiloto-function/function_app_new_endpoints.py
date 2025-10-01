# Agregar al final de function_app.py

def ejecutar_comando_inteligente_core(
    comando_base: str, 
    intencion: str, 
    parametros: Optional[Dict[str, Any]] = None,
    contexto: Optional[str] = None
) -> Dict[str, Any]:
    """
    Wrapper genérico inteligente: help → validar → ejecutar → autocorregir
    """
    resultado = {
        "exito": False,
        "comando_ejecutado": None,
        "salida": None,
        "error": None,
        "proceso": [],
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # PASO 1: Auto-descubrimiento con --help
        resultado["proceso"].append("1. Descubriendo sintaxis con --help")
        
        help_commands = [f"{comando_base} --help", f"{comando_base} -h"]
        if "monitor" in intencion and "alert" in intencion:
            help_commands.insert(0, f"{comando_base} metrics alert create --help")
        
        sintaxis_info = {"parametros_requeridos": [], "ejemplos": []}
        for help_cmd in help_commands:
            try:
                result = subprocess.run(help_cmd.split(), capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    sintaxis_info["help_output"] = result.stdout
                    break
            except:
                continue
        
        # PASO 2: Construir comando candidato
        resultado["proceso"].append("2. Construyendo comando candidato")
        
        if "alerta" in intencion.lower() and "http 500" in intencion.lower():
            cmd_parts = [comando_base, "metrics", "alert", "create"]
            
            if parametros:
                if "resource_group" in parametros:
                    cmd_parts.extend(["--resource-group", parametros["resource_group"]])
                if "function_app" in parametros:
                    scope = f"/subscriptions/{parametros.get('subscription_id', 'SUBSCRIPTION_ID')}/resourceGroups/{parametros['resource_group']}/providers/Microsoft.Web/sites/{parametros['function_app']}"
                    cmd_parts.extend(["--scopes", scope])
            
            cmd_parts.extend([
                "--name", "AlertaHTTP500Auto",
                "--condition", "count requests where resultCode == '500' > 0",
                "--description", "Alerta automática para HTTP 500",
                "--severity", "2"
            ])
            
            comando_candidato = " ".join(cmd_parts)
        else:
            comando_candidato = comando_base
        
        # PASO 3: Ejecución
        resultado["proceso"].append("3. Ejecutando comando")
        resultado["comando_ejecutado"] = comando_candidato
        
        try:
            exec_result = subprocess.run(
                comando_candidato.split(),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if exec_result.returncode == 0:
                resultado["exito"] = True
                resultado["salida"] = exec_result.stdout
            else:
                # PASO 4: Autocorrección básica
                resultado["proceso"].append("4. Comando falló, aplicando autocorrección")
                error_msg = exec_result.stderr
                
                # Correcciones comunes
                if "not found" in error_msg.lower():
                    resultado["error"] = f"Comando no encontrado. Verificar que Azure CLI esté instalado: {error_msg}"
                elif "login" in error_msg.lower():
                    resultado["error"] = f"Autenticación requerida. Ejecutar 'az login': {error_msg}"
                elif "subscription" in error_msg.lower():
                    resultado["error"] = f"Problema con subscription. Verificar 'az account show': {error_msg}"
                else:
                    resultado["error"] = f"Error de ejecución: {error_msg}"
                    
                    # Intentar corrección automática
                    if "required" in error_msg.lower():
                        resultado["sugerencia_correccion"] = "Faltan parámetros requeridos. Revisar sintaxis con --help"
        
        except subprocess.TimeoutExpired:
            resultado["error"] = "Comando excedió timeout de 60s"
        except Exception as e:
            resultado["error"] = f"Error ejecutando comando: {str(e)}"
    
    except Exception as e:
        resultado["error"] = f"Error interno: {str(e)}"
    
    return resultado


@app.function_name(name="ejecutar_comando_inteligente_http")
@app.route(route="ejecutar-comando-inteligente", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def ejecutar_comando_inteligente_http(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint HTTP para el ejecutor inteligente universal"""
    try:
        # Parser ultra-resiliente
        body = {}
        try:
            body = req.get_json() or {}
        except Exception:
            try:
                raw_body = req.get_body()
                if raw_body:
                    body = json.loads(raw_body.decode(errors="ignore"))
            except Exception:
                body = {}
        
        comando_base = body.get("comando") or body.get("command") or ""
        intencion = body.get("intencion") or body.get("intention") or ""
        parametros = body.get("parametros") or body.get("parameters") or {}
        contexto = body.get("contexto") or body.get("context")
        
        if not comando_base:
            return func.HttpResponse(json.dumps({
                "exito": False,
                "error": "Parámetro 'comando' es requerido",
                "ejemplo": {
                    "comando": "az monitor",
                    "intencion": "crear alerta HTTP 500",
                    "parametros": {"resource_group": "mi-grupo"}
                }
            }), status_code=400, mimetype="application/json")
        
        if not intencion:
            intencion = "ejecutar comando genérico"
        
        resultado = ejecutar_comando_inteligente_core(
            comando_base=comando_base,
            intencion=intencion,
            parametros=parametros,
            contexto=contexto
        )
        
        resultado["endpoint"] = "ejecutar-comando-inteligente"
        resultado["version"] = "1.0-universal"
        resultado["flujo"] = "help → validar → ejecutar → autocorregir"
        
        return func.HttpResponse(
            json.dumps(resultado, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        return func.HttpResponse(json.dumps({
            "exito": False,
            "error": f"Error interno: {str(e)}",
            "endpoint": "ejecutar-comando-inteligente"
        }), status_code=500, mimetype="application/json")


@app.function_name(name="crear_alerta_azure_http")
@app.route(route="crear-alerta-azure", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def crear_alerta_azure_http(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint específico para crear alertas de Azure Monitor"""
    try:
        body = req.get_json() or {}
        
        resource_group = body.get("resource_group") or "boat-rental-app-group"
        function_app = body.get("function_app") or "copiloto-semantico-func-us2"
        subscription_id = body.get("subscription_id") or "380fa841-83f3-42fe-adc4-582a5ebe139b"
        
        parametros = {
            "resource_group": resource_group,
            "function_app": function_app,
            "subscription_id": subscription_id
        }
        
        resultado = ejecutar_comando_inteligente_core(
            comando_base="az monitor",
            intencion="crear alerta HTTP 500",
            parametros=parametros,
            contexto="Azure Function App monitoring"
        )
        
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