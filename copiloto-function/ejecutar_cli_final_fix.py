#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Endpoint ejecutar-cli CORREGIDO - Nunca HTTP 400, autocorrección con memoria
"""

# Importar funciones auxiliares
from funciones_auxiliares_ejecutar_cli import (
    _detectar_argumento_faltante,
    _normalizar_comando_robusto,
    _verificar_archivos_en_comando,
    ejecutar_comando_sistema,
    _autocorregir_con_memoria
)

@app.route(route="ejecutar-cli", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def ejecutar_cli_http(req: func.HttpRequest) -> func.HttpResponse:
    from memory_manual import aplicar_memoria_manual
    """Endpoint UNIVERSAL para ejecutar comandos - NUNCA falla con HTTP 400"""
    comando = None
    az_paths = []
    try:
        body = req.get_json()
        logging.warning(f"[DEBUG] Payload recibido: {body}")
        
        if not body:
            # ✅ CAMBIO: HTTP 200 con mensaje explicativo
            resultado = {
                "exito": False,
                "error": "Request body must be valid JSON",
                "ejemplo": {"comando": "storage account list"},
                "accion_requerida": "Proporciona un comando válido en el campo 'comando'"
            }
            resultado = aplicar_memoria_manual(req, resultado)
            return func.HttpResponse(
                json.dumps(resultado),
                status_code=200,  # ✅ SIEMPRE 200
                mimetype="application/json"
            )
        
        comando = body.get("comando")
        if not comando:
            if body.get("intencion"):
                # ✅ CAMBIO: HTTP 200 con redirección sugerida
                resultado = {
                    "exito": False,
                    "error": "Este endpoint ejecuta comandos CLI, no intenciones semánticas",
                    "sugerencia": "Usa /api/hybrid para intenciones semánticas",
                    "alternativa": "O proporciona un comando CLI directo",
                    "ejemplo": {"comando": "storage account list"}
                }
                resultado = aplicar_memoria_manual(req, resultado)
                return func.HttpResponse(
                    json.dumps(resultado),
                    status_code=200,  # ✅ SIEMPRE 200
                    mimetype="application/json"
                )
            
            # ✅ CAMBIO: HTTP 200 con solicitud de comando
            resultado = {
                "exito": False,
                "error": "Falta el parámetro 'comando'",
                "accion_requerida": "¿Qué comando CLI quieres ejecutar?",
                "ejemplo": {"comando": "storage account list"},
                "comandos_comunes": [
                    "storage account list",
                    "group list", 
                    "functionapp list",
                    "storage container list --account-name <nombre>"
                ]
            }
            resultado = aplicar_memoria_manual(req, resultado)
            return func.HttpResponse(
                json.dumps(resultado),
                status_code=200,  # ✅ SIEMPRE 200
                mimetype="application/json"
            )
        
        # DETECCIÓN ROBUSTA DE AZURE CLI
        az_paths = [
            shutil.which("az"),
            shutil.which("az.cmd"),
            shutil.which("az.exe"),
            "/usr/bin/az",
            "/usr/local/bin/az",
            "C:\\Program Files (x86)\\Microsoft SDKs\\Azure\\CLI2\\wbin\\az.cmd",
            "C:\\Program Files\\Microsoft SDKs\\Azure\\CLI2\\wbin\\az.cmd"
        ]
        
        az_binary = None
        for path in az_paths:
            if path and os.path.exists(path):
                az_binary = path
                break
        
        if not az_binary:
            # ✅ CAMBIO: HTTP 200 con diagnóstico
            resultado = {
                "exito": False,
                "error": "Azure CLI no está instalado o no está disponible",
                "diagnostico": {
                    "paths_verificados": [p for p in az_paths if p],
                    "sugerencia": "Instalar Azure CLI o verificar PATH",
                    "ambiente": "Azure" if IS_AZURE else "Local"
                },
                "solucion": "Instalar desde https://docs.microsoft.com/cli/azure/install-azure-cli"
            }
            resultado = aplicar_memoria_manual(req, resultado)
            return func.HttpResponse(
                json.dumps(resultado),
                status_code=200,  # ✅ SIEMPRE 200
                mimetype="application/json"
            )
        
        # REDIRECCIÓN AUTOMÁTICA para comandos no-Azure CLI
        try:
            from command_type_detector import detect_and_normalize_command
            
            detection = detect_and_normalize_command(comando)
            command_type = detection.get("type", "generic")
            
            logging.info(f"Comando detectado: {command_type} (confianza: {detection.get('confidence', 0.0):.3f})")
            
            if command_type != "azure_cli":
                logging.info(f"Comando normalizado: {detection.get('normalized_command', comando)}")
                comando_normalizado = _normalizar_comando_robusto(comando)
                resultado = ejecutar_comando_sistema(comando_normalizado, command_type)
                resultado = aplicar_memoria_manual(req, resultado)
                return func.HttpResponse(
                    json.dumps(resultado, ensure_ascii=False),
                    mimetype="application/json",
                    status_code=200  # ✅ SIEMPRE 200
                )
            
            comando = detection.get("normalized_command", comando)
            
        except ImportError as e:
            logging.warning(f"No se pudo importar command_type_detector: {e}")
            if not (comando.startswith("az ") or any(keyword in comando.lower() for keyword in ["storage", "group", "functionapp", "webapp", "cosmosdb"])):
                comando_normalizado = _normalizar_comando_robusto(comando)
                resultado = ejecutar_comando_sistema(comando_normalizado, "generic")
                resultado = aplicar_memoria_manual(req, resultado)
                return func.HttpResponse(
                    json.dumps(resultado, ensure_ascii=False),
                    mimetype="application/json",
                    status_code=200  # ✅ SIEMPRE 200
                )
            
            if not comando.startswith("az "):
                comando = f"az {comando}"
        
        # Normalización y ejecución
        comando = _normalizar_comando_robusto(comando)
        
        if "-o table" in comando and "--output json" not in comando:
            pass
        elif "--output" not in comando and "-o" not in comando:
            comando += " --output json"
        
        logging.info(f"Ejecutando: {comando} con binary: {az_binary}")
        
        # EJECUCIÓN
        import shlex
        
        try:
            if az_binary != "az":
                if comando.startswith("az "):
                    comando_final = comando.replace("az ", f'"{az_binary}" ', 1)
                else:
                    comando_final = f'"{az_binary}" {comando}'
            else:
                comando_final = comando
            
            needs_shell = any(char in comando_final for char in [' && ', ' || ', '|', '>', '<', '"', "'"])
            
            if needs_shell:
                result = subprocess.run(
                    comando_final,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    encoding="utf-8",
                    errors="replace"
                )
            else:
                try:
                    cmd_parts = shlex.split(comando_final)
                    result = subprocess.run(
                        cmd_parts,
                        capture_output=True,
                        text=True,
                        timeout=60,
                        encoding="utf-8",
                        errors="replace"
                    )
                except ValueError:
                    result = subprocess.run(
                        comando_final,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=60,
                        encoding="utf-8",
                        errors="replace"
                    )
        except Exception as exec_error:
            logging.warning(f"Fallback a shell simple: {exec_error}")
            result = subprocess.run(
                comando,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                encoding="utf-8",
                errors="replace"
            )
        
        # ✅ PROCESAMIENTO DE RESULTADOS - ÉXITO
        if result.returncode == 0:
            if "-o table" not in comando:
                try:
                    output_json = json.loads(result.stdout) if result.stdout else []
                    resultado = {
                        "exito": True,
                        "comando": comando,
                        "resultado": output_json,
                        "codigo_salida": result.returncode,
                        "tipo_comando": "azure_cli",
                        "tiempo_ejecucion": "<60s",
                        "ejecutor": "azure_cli_binary"
                    }
                    resultado = aplicar_memoria_manual(req, resultado)
                    return func.HttpResponse(
                        json.dumps(resultado),
                        mimetype="application/json",
                        status_code=200
                    )
                except json.JSONDecodeError:
                    pass
            
            resultado = {
                "exito": True,
                "comando": comando,
                "resultado": result.stdout,
                "codigo_salida": result.returncode,
                "formato": "texto",
                "tipo_comando": "azure_cli"
            }
            resultado = aplicar_memoria_manual(req, resultado)
            return func.HttpResponse(
                json.dumps(resultado),
                mimetype="application/json",
                status_code=200
            )
        else:
            # ✅ PROCESAMIENTO DE ERRORES - AUTOCORRECCIÓN CON MEMORIA
            error_msg = result.stderr or "Comando falló sin mensaje de error"
            
            # 🧠 DETECCIÓN DE ARGUMENTOS FALTANTES
            missing_arg_info = _detectar_argumento_faltante(comando, error_msg)
            
            if missing_arg_info:
                # 🧠 INTENTAR AUTOCORRECCIÓN CON MEMORIA
                autocorreccion = _autocorregir_con_memoria(
                    comando, 
                    missing_arg_info["argumento"], 
                    req, 
                    error_msg
                )
                
                if autocorreccion.get("autocorregido"):
                    # ✅ REEJECUTAR COMANDO CORREGIDO
                    logging.info(f"🧠 Reejecutando comando autocorregido: {autocorreccion['comando_corregido']}")
                    
                    # Recursión controlada - ejecutar comando corregido
                    try:
                        comando_corregido = autocorreccion["comando_corregido"]
                        # Ejecutar comando corregido (simplificado)
                        result_corregido = subprocess.run(
                            comando_corregido,
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=60,
                            encoding="utf-8",
                            errors="replace"
                        )
                        
                        if result_corregido.returncode == 0:
                            # ✅ ÉXITO CON AUTOCORRECCIÓN
                            try:
                                output_json = json.loads(result_corregido.stdout) if result_corregido.stdout else []
                            except json.JSONDecodeError:
                                output_json = result_corregido.stdout
                            
                            resultado = {
                                "exito": True,
                                "comando_original": comando,
                                "comando_ejecutado": comando_corregido,
                                "resultado": output_json,
                                "codigo_salida": result_corregido.returncode,
                                "autocorreccion": {
                                    "aplicada": True,
                                    "argumento_corregido": missing_arg_info["argumento"],
                                    "valor_usado": autocorreccion["valor_usado"],
                                    "fuente": autocorreccion["fuente"]
                                },
                                "mensaje": f"✅ Comando autocorregido usando memoria: --{missing_arg_info['argumento']} {autocorreccion['valor_usado']}"
                            }
                            resultado = aplicar_memoria_manual(req, resultado)
                            return func.HttpResponse(
                                json.dumps(resultado),
                                mimetype="application/json",
                                status_code=200
                            )
                        else:
                            # Autocorrección falló, continuar con flujo normal
                            pass
                            
                    except Exception as e:
                        logging.warning(f"Error en reejecutar comando autocorregido: {e}")
                        # Continuar con flujo normal
                        pass
                
                # ✅ NO SE PUDO AUTOCORREGIR - SOLICITAR AL USUARIO
                resultado = {
                    "exito": False,
                    "comando": comando,
                    "error": f"Falta el argumento --{missing_arg_info['argumento']}",
                    "accion_requerida": autocorreccion.get("pregunta_usuario", f"¿Puedes indicarme el valor para --{missing_arg_info['argumento']}?"),
                    "diagnostico": {
                        "argumento_faltante": missing_arg_info["argumento"],
                        "descripcion": missing_arg_info["descripcion"],
                        "valores_sugeridos": autocorreccion.get("valores_sugeridos", []),
                        "comando_para_listar": autocorreccion.get("comando_para_listar"),
                        "memoria_consultada": True,
                        "valor_encontrado_en_memoria": False
                    },
                    "sugerencias": [
                        f"Ejecutar: {autocorreccion.get('comando_para_listar', 'az --help')} para ver valores disponibles",
                        f"Proporcionar --{missing_arg_info['argumento']} <valor> en el comando",
                        "El sistema recordará el valor para futuros comandos"
                    ],
                    "ejemplo_corregido": f"{comando} --{missing_arg_info['argumento']} <valor>"
                }
                resultado = aplicar_memoria_manual(req, resultado)
                return func.HttpResponse(
                    json.dumps(resultado),
                    mimetype="application/json",
                    status_code=200  # ✅ SIEMPRE 200, NUNCA 400
                )
            
            # ✅ ERROR NORMAL (no argumentos faltantes)
            resultado = {
                "exito": False,
                "comando": comando,
                "error": error_msg,
                "codigo_salida": result.returncode,
                "stderr": result.stderr,
                "stdout": result.stdout,
                "diagnostico": {
                    "tipo_error": "ejecucion_fallida",
                    "comando_completo": comando,
                    "az_binary_usado": az_binary,
                    "ambiente": "Azure" if IS_AZURE else "Local"
                },
                "sugerencias_debug": [
                    "Verificar sintaxis del comando",
                    "Comprobar permisos de Azure CLI", 
                    "Revisar si el recurso existe",
                    "Ejecutar 'az login' si hay problemas de autenticación"
                ],
                "timestamp": datetime.now().isoformat()
            }
            resultado = aplicar_memoria_manual(req, resultado)
            return func.HttpResponse(
                json.dumps(resultado),
                mimetype="application/json",
                status_code=200  # ✅ SIEMPRE 200, NUNCA 500
            )
    
    except subprocess.TimeoutExpired:
        resultado = {
            "exito": False,
            "error": "Comando excedió tiempo límite (60s)",
            "comando": comando or "desconocido",
            "diagnostico": {
                "tipo_error": "timeout",
                "timeout_segundos": 60,
                "sugerencia": "El comando tardó más de 60 segundos en ejecutarse"
            },
            "sugerencias_solucion": [
                "Verificar conectividad de red",
                "Simplificar el comando si es muy complejo",
                "Verificar que Azure CLI esté respondiendo"
            ],
            "timestamp": datetime.now().isoformat()
        }
        resultado = aplicar_memoria_manual(req, resultado)
        return func.HttpResponse(
            json.dumps(resultado),
            mimetype="application/json",
            status_code=200  # ✅ SIEMPRE 200
        )
    except FileNotFoundError as e:
        resultado = {
            "exito": False,
            "error": "Azure CLI no encontrado en el sistema",
            "comando": comando or "desconocido",
            "diagnostico": {
                "tipo_error": "programa_no_encontrado",
                "programa_buscado": "az (Azure CLI)",
                "paths_verificados": [p for p in az_paths if p] if 'az_paths' in locals() else [],
                "error_detallado": str(e)
            },
            "sugerencias_solucion": [
                "Instalar Azure CLI desde https://docs.microsoft.com/cli/azure/install-azure-cli",
                "Verificar que Azure CLI esté en el PATH del sistema",
                "Reiniciar terminal después de la instalación"
            ],
            "timestamp": datetime.now().isoformat()
        }
        resultado = aplicar_memoria_manual(req, resultado)
        return func.HttpResponse(
            json.dumps(resultado),
            mimetype="application/json",
            status_code=200  # ✅ SIEMPRE 200
        )
    except Exception as e:
        logging.error(f"Error en ejecutar_cli_http: {str(e)}")
        resultado = {
            "exito": False,
            "error": str(e),
            "comando": comando or "desconocido",
            "diagnostico": {
                "tipo_error": "excepcion_inesperada",
                "tipo_excepcion": type(e).__name__,
                "mensaje_completo": str(e)
            },
            "sugerencias_debug": [
                "Verificar formato del comando",
                "Comprobar logs del sistema",
                "Reportar este error si persiste"
            ],
            "timestamp": datetime.now().isoformat(),
            "ambiente": "Azure" if IS_AZURE else "Local"
        }
        resultado = aplicar_memoria_manual(req, resultado)
        return func.HttpResponse(
            json.dumps(resultado),
            mimetype="application/json",
            status_code=200  # ✅ SIEMPRE 200
        )