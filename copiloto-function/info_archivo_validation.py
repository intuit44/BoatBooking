# Validación robusta para endpoint /api/info-archivo
# Agregar esta validación al inicio de info_archivo_http

def validate_info_archivo_params(req, run_id, CONTAINER_NAME, IS_AZURE, get_blob_client, PROJECT_ROOT, COPILOT_ROOT, Path, datetime, json, func, logging, os):
    """
    Validación robusta de parámetros y existencia física del archivo para info_archivo_http
    """
    try:
        # ✅ VALIDACIÓN CRÍTICA: Verificar que ruta venga con archivo válido
        ruta_raw = (req.params.get("ruta") or req.params.get("path") or 
                   req.params.get("archivo") or req.params.get("blob") or "").strip()
        
        if not ruta_raw:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "Parámetro 'ruta' es requerido para obtener información del archivo",
                    "error_code": "MISSING_REQUIRED_PARAMETER",
                    "parametros_aceptados": {
                        "ruta": "Ruta del archivo (requerido)",
                        "path": "Alias para 'ruta'",
                        "archivo": "Alias para 'ruta'",
                        "blob": "Alias para 'ruta'"
                    },
                    "ejemplos_validos": [
                        "?ruta=README.md",
                        "?ruta=package.json",
                        "?path=mobile-app/src/App.tsx",
                        "?archivo=docs/API.md"
                    ],
                    "run_id": run_id,
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=400
            )
        
        # ✅ VALIDACIÓN ADICIONAL: Formato de ruta válido
        if ruta_raw.startswith("//") or ".." in ruta_raw or len(ruta_raw.strip()) < 1:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "Formato de ruta inválido o inseguro",
                    "error_code": "INVALID_PATH_FORMAT",
                    "ruta_recibida": ruta_raw,
                    "problema": "Contiene caracteres no permitidos o está vacía",
                    "formatos_validos": [
                        "archivo.txt",
                        "carpeta/archivo.txt",
                        "docs/readme.md"
                    ],
                    "run_id": run_id
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=400
            )
        
        # ✅ VERIFICACIÓN FÍSICA: Comprobar que el archivo existe antes de procesar
        container = req.params.get("container", CONTAINER_NAME)
        archivo_existe = False
        error_existencia = None
        
        # Verificar existencia en Azure Blob Storage
        if IS_AZURE:
            try:
                client = get_blob_client()
                if client:
                    container_client = client.get_container_client(container)
                    if container_client.exists():
                        ruta_normalizada = ruta_raw.replace('\\', '/').lstrip('/')
                        blob_client = container_client.get_blob_client(ruta_normalizada)
                        archivo_existe = blob_client.exists()
                        if not archivo_existe:
                            error_existencia = f"El archivo '{ruta_raw}' no existe en el contenedor '{container}'"
                    else:
                        error_existencia = f"El contenedor '{container}' no existe"
                else:
                    error_existencia = "Cliente de Blob Storage no disponible"
            except Exception as e:
                error_existencia = f"Error verificando existencia en Blob Storage: {str(e)}"
        else:
            # Verificar existencia local
            posibles_rutas = [
                PROJECT_ROOT / ruta_raw,
                COPILOT_ROOT / ruta_raw if 'COPILOT_ROOT' in globals() else None,
                Path(ruta_raw) if Path(ruta_raw).is_absolute() else None
            ]
            
            for ruta_completa in filter(None, posibles_rutas):
                if ruta_completa and ruta_completa.exists() and ruta_completa.is_file():
                    archivo_existe = True
                    break
            
            if not archivo_existe:
                error_existencia = f"El archivo '{ruta_raw}' no existe en el sistema local"
        
        # ✅ RESPUESTA DE ERROR SI NO EXISTE
        if not archivo_existe:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": error_existencia or f"El archivo '{ruta_raw}' no existe",
                    "error_code": "FILE_NOT_FOUND",
                    "archivo_solicitado": {
                        "ruta_recibida": ruta_raw,
                        "container": container,
                        "ambiente": "Azure" if IS_AZURE else "Local"
                    },
                    "acciones_recomendadas": [
                        "Verificar que el archivo existe en la ubicación especificada",
                        "Comprobar permisos de acceso al archivo",
                        f"Listar archivos disponibles en el contenedor '{container}'"
                    ],
                    "run_id": run_id,
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=404
            )
        
        logging.info(f"[{run_id}] Archivo verificado y existe: {ruta_raw}")
        
        # Retornar None si todo está bien para continuar con el procesamiento normal
        return None
        
    except Exception as e:
        logging.exception(f"[{run_id}] Error en validación de info_archivo: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "error": f"Error interno en validación: {str(e)}",
                "error_code": "VALIDATION_ERROR",
                "tipo_error": type(e).__name__,
                "run_id": run_id,
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False),
            mimetype="application/json",
            status_code=500
        )

# INSTRUCCIONES DE USO:
# 1. Importar esta función en function_app.py
# 2. Al inicio de info_archivo_http, agregar:
#    validation_result = validate_info_archivo_params(req, run_id, CONTAINER_NAME, IS_AZURE, get_blob_client, PROJECT_ROOT, COPILOT_ROOT, Path, datetime, json, func, logging, os)
#    if validation_result is not None:
#        return validation_result
# 3. Continuar con el procesamiento normal del archivo