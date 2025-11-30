"""
Endpoint: /api/ejecutar-cli
Endpoint UNIVERSAL para ejecutar comandos CLI
"""
from function_app import _resolver_placeholders_dinamico, app
import logging
import json
import os
import sys
import subprocess
import platform
import shutil
import re
from pathlib import Path
from datetime import datetime
import azure.functions as func
from typing import Optional, Dict, Any, List, Tuple, Union, TypeVar, Type
import time
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


def ejecutar_comando_sistema(comando: str, tipo: str) -> Dict[str, Any]:
    """Ejecuta comando del sistema según su tipo de manera dinámica y adaptable"""

    start_time = time.time()

    try:
        # 🔥 APLICAR AUTO-FIXES ANTES DE CUALQUIER EJECUCIÓN
        try:
            from command_fixers.auto_fixers import apply_auto_fixes
            comando = apply_auto_fixes(comando, tipo)
            logging.info(f"Auto-fixes aplicados: {comando}")
        except ImportError:
            logging.warning("auto_fixers no disponible")

        # Configurar entorno
        env = os.environ.copy()
        shell = False
        cmd_args = []

        # Detección dinámica y configuración por tipo
        if tipo == "python":
            # Detectar si es pip, python script, o código inline
            if comando.startswith("pip "):
                # Comando pip directo
                cmd_args = comando.split()
                shell = True
            elif comando.startswith("python "):
                # Comando python con argumentos
                cmd_args = comando.split()
                shell = False
            elif any(keyword in comando for keyword in ["import ", "print(", "def ", "class "]):
                # Código Python inline
                cmd_args = ["python", "-c", comando]
                shell = False
            else:
                # Script Python o comando genérico
                cmd_args = ["python"] + comando.split()
                shell = False

            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUNBUFFERED'] = '1'

        elif tipo == "powershell":
            # 🔥 SOLUCIÓN: Envolver comando en & { } para ejecutar dentro de PowerShell
            comando_wrapped = f"& {{ {comando} }}"

            # PowerShell con detección de cmdlets
            if any(comando.startswith(prefix) for prefix in ["Get-", "Set-", "New-", "Remove-", "Invoke-"]):
                # Cmdlet nativo
                cmd_args = ["powershell", "-NoProfile",
                            "-Command", comando_wrapped]
            else:
                # Comando o script PowerShell
                cmd_args = ["powershell", "-NoProfile",
                            "-ExecutionPolicy", "Bypass", "-Command", comando_wrapped]

            env['POWERSHELL_TELEMETRY_OPTOUT'] = '1'
            shell = False

        elif tipo == "bash":
            # Bash con detección de comandos Unix
            bash_path = shutil.which("bash") or "/bin/bash"
            cmd_args = [bash_path, "-c", comando]
            shell = False

        elif tipo == "npm":
            # NPM con detección de subcomandos
            if comando.startswith("npm "):
                cmd_args = comando.split()
            else:
                cmd_args = ["npm"] + comando.split()
            shell = True

        elif tipo == "docker":
            # Docker con detección de subcomandos
            if comando.startswith("docker "):
                cmd_args = comando.split()
            else:
                cmd_args = ["docker"] + comando.split()
            shell = False

        elif tipo == "azure_cli":
            # Azure CLI
            if comando.startswith("az "):
                cmd_args = comando.split()
            else:
                cmd_args = ["az"] + comando.split()
            shell = False

        else:
            # Comando genérico - ejecutar tal como está
            if " " in comando:
                cmd_args = comando.split()
            else:
                cmd_args = [comando]
            shell = True

        # EJECUCIÓN ROBUSTA: Detección dinámica de método óptimo
        import shlex

        # Detectar si el comando tiene rutas con espacios o caracteres especiales
        has_spaces_in_paths = ' ' in comando and (
            '\\' in comando or '/' in comando)
        has_quotes = '"' in comando or "'" in comando
        has_pipes = any(char in comando for char in [
                        '|', '&&', '||', '>', '<'])

        # Normalizar rutas de Windows con espacios
        if has_spaces_in_paths and not has_quotes and tipo == "python":
            # Detectar rutas de Windows y agregar comillas si es necesario
            # Buscar patrones como "C:\path with spaces\file.py"
            path_pattern = r'([A-Za-z]:\\[^"]*\s[^"]*\.[a-zA-Z]+)'
            matches = re.findall(path_pattern, comando)

            for match in matches:
                if '"' not in match:  # Solo si no tiene comillas ya
                    comando = comando.replace(match, f'"{match}"')
                    logging.info(f"Ruta normalizada: {match} -> \"{match}\"")

        # Decidir método de ejecución dinámicamente
        # 🔥 FIX: Si es PowerShell, SIEMPRE usar powershell.exe, nunca cmd.exe
        if tipo == "powershell":
            # PowerShell SIEMPRE debe ejecutarse con powershell.exe
            execution_method = "powershell_native"
            logging.info(
                f"Ejecutando PowerShell con powershell.exe: {cmd_args}")

            result = subprocess.run(
                # Ya contiene ["powershell", "-NoProfile", "-Command", comando]
                cmd_args,
                capture_output=True,
                text=True,
                timeout=60,
                encoding='utf-8',
                errors='replace',
                env=env,
                shell=False  # NUNCA usar shell=True para PowerShell
            )
        elif has_spaces_in_paths or has_quotes or has_pipes or shell:
            # Usar shell para comandos complejos
            execution_method = "shell"

            # 🔥 LIMPIEZA FINAL: Eliminar comillas duplicadas/mal escapadas
            from command_cleaner import limpiar_comillas_comando
            comando_limpio = limpiar_comillas_comando(comando)
            logging.info(f"Comando original: {comando}")
            logging.info(f"Comando limpio: {comando_limpio}")
            logging.info(f"Ejecutando {tipo} con shell")

            result = subprocess.run(
                comando_limpio,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                encoding='utf-8',
                errors='replace',
                env=env
            )
        else:
            # Intentar con lista de argumentos primero
            execution_method = "args_list"
            try:
                if cmd_args:
                    # Usar shlex para parsing inteligente
                    if isinstance(cmd_args, list) and len(cmd_args) > 1:
                        final_args = cmd_args
                    else:
                        try:
                            final_args = shlex.split(comando) if isinstance(
                                comando, str) else cmd_args
                        except ValueError:
                            # Si shlex falla, usar split simple como fallback
                            final_args = comando.split() if isinstance(comando, str) else cmd_args

                    logging.info(f"Ejecutando {tipo} con args: {final_args}")

                    result = subprocess.run(
                        final_args,
                        capture_output=True,
                        text=True,
                        timeout=60,
                        encoding='utf-8',
                        errors='replace',
                        env=env
                    )
                else:
                    raise ValueError("No hay argumentos para ejecutar")

            except (ValueError, FileNotFoundError) as e:
                # Fallback a shell si falla el método de argumentos
                execution_method = "shell_fallback"
                logging.info(f"Fallback a shell para {tipo}: {e}")

                result = subprocess.run(
                    comando,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    encoding='utf-8',
                    errors='replace',
                    env=env
                )

        duration = time.time() - start_time

        # --- NORMALIZADOR DE SALIDA POWERSHELL CON RE-EJECUCIÓN AUTOMÁTICA ---
        if tipo == "powershell" and result.returncode == 0:
            stdout_limpio = result.stdout.strip()
            if stdout_limpio and "Perfil de PowerShell cargado" in stdout_limpio:
                stdout_limpio = ""

            if not stdout_limpio:
                logging.info(
                    "PowerShell: stdout vacío, re-ejecutando con | Out-String")
                comando_con_outstring = f"{comando} | Out-String" if '| Out-String' not in comando else comando
                comando_retry_wrapped = f"& {{ {comando_con_outstring} }}"

                try:
                    result_retry = subprocess.run(
                        cmd_args[:-1] + [comando_retry_wrapped],
                        capture_output=True,
                        text=True,
                        timeout=60,
                        encoding='utf-8',
                        errors='replace',
                        env=env
                    )

                    if result_retry.returncode == 0 and result_retry.stdout.strip():
                        logging.info(
                            f"PowerShell: Re-ejecución exitosa, {len(result_retry.stdout)} chars")
                        object.__setattr__(
                            result, 'stdout', result_retry.stdout)
                    else:
                        decoded = f"⚠️ PowerShell sin salida visible. Comando: {comando[:100]}..."
                        object.__setattr__(result, 'stdout', decoded)
                except Exception as e:
                    logging.warning(f"PowerShell re-ejecución falló: {e}")
                    object.__setattr__(result, 'stdout', f"⚠️ Error: {str(e)}")

            # 🔥 DETECCIÓN DE VARIABLES: Si hay $ y stdout vacío, forzar salida
            if "$" in comando and result.returncode == 0 and not result.stdout.strip():
                logging.info(
                    "PowerShell: Variable detectada sin salida, aplicando auto-fixes")

                # 🧠 APLICAR AUTO-FIXES INTELIGENTES
                try:
                    from command_fixers.auto_fixers import apply_auto_fixes
                    comando = apply_auto_fixes(comando, tipo)
                except ImportError:
                    logging.warning(
                        "auto_fixers no disponible, usando fallback")

                comando_con_variable = f"& {{ {comando} | Out-String }}"
                try:
                    result_var = subprocess.run(
                        cmd_args[:-1] + [comando_con_variable],
                        capture_output=True,
                        text=True,
                        timeout=60,
                        encoding='utf-8',
                        errors='replace',
                        env=env
                    )
                    if result_var.returncode == 0 and result_var.stdout.strip():
                        logging.info(
                            f"PowerShell: Variable forzada exitosa, {len(result_var.stdout)} chars")
                        object.__setattr__(result, 'stdout', result_var.stdout)
                except Exception as e:
                    logging.warning(f"PowerShell variable forzada falló: {e}")
        # --- FIN NORMALIZADOR ---

        # ✅ MEJORADO: Más información de debugging
        resultado = {
            "exito": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.stderr else None,
            "return_code": result.returncode,
            "duration": f"{duration:.2f}s",
            "comando_ejecutado": comando,
            "tipo_comando": tipo,
            "metodo_ejecucion": execution_method,
            "deteccion_automatica": {
                "rutas_con_espacios": has_spaces_in_paths,
                "tiene_comillas": has_quotes,
                "tiene_pipes": has_pipes
            },
            "timestamp": datetime.now().isoformat()
        }

        # ✅ AGREGAR: Información adicional si falla
        if result.returncode != 0:
            resultado["diagnostico_error"] = {
                "archivo_no_encontrado": "No such file or directory" in (result.stderr or ""),
                "permisos_denegados": "Permission denied" in (result.stderr or ""),
                "comando_no_reconocido": any(phrase in (result.stderr or "").lower() for phrase in [
                    "not recognized", "command not found", "no se reconoce"
                ]),
                "sintaxis_incorrecta": "syntax error" in (result.stderr or "").lower(),
                "ruta_no_existe": "cannot find the path" in (result.stderr or "").lower()
            }

            # Sugerencias basadas en el tipo de error
            sugerencias = []
            if resultado["diagnostico_error"]["archivo_no_encontrado"]:
                sugerencias.append(
                    "Verificar que el archivo existe en la ruta especificada")
            if resultado["diagnostico_error"]["permisos_denegados"]:
                sugerencias.append(
                    "Ejecutar con permisos de administrador o verificar permisos del archivo")
            if resultado["diagnostico_error"]["comando_no_reconocido"]:
                sugerencias.append(
                    f"Verificar que {tipo} esté instalado y en el PATH")
            if resultado["diagnostico_error"]["sintaxis_incorrecta"]:
                sugerencias.append("Revisar la sintaxis del comando")
            if resultado["diagnostico_error"]["ruta_no_existe"]:
                sugerencias.append(
                    "Verificar que la ruta del directorio existe")

            if not sugerencias:
                sugerencias.append(
                    "Revisar el mensaje de error para más detalles")

            resultado["sugerencias_solucion"] = sugerencias

        return resultado

    except subprocess.TimeoutExpired:
        return {
            "exito": False,
            "error": "Comando excedió tiempo límite (60s)",
            "return_code": -1,
            "duration": "timeout",
            "comando_ejecutado": comando,
            "tipo_comando": tipo,
            "diagnostico_error": {
                "tipo_error": "timeout",
                "timeout_segundos": 60,
                "posibles_causas": [
                    "Comando muy lento o colgado",
                    "Problemas de conectividad",
                    "Proceso esperando entrada del usuario"
                ]
            },
            "sugerencias_solucion": [
                "Verificar que el comando no requiera interacción",
                "Simplificar el comando si es muy complejo",
                "Verificar conectividad de red si aplica"
            ],
            "timestamp": datetime.now().isoformat()
        }
    except FileNotFoundError as e:
        return {
            "exito": False,
            "error": f"Comando o programa no encontrado: {str(e)}",
            "return_code": -1,
            "duration": f"{time.time() - start_time:.2f}s",
            "comando_ejecutado": comando,
            "tipo_comando": tipo,
            "diagnostico_error": {
                "tipo_error": "programa_no_encontrado",
                "programa_buscado": tipo,
                "error_detallado": str(e),
                "verificar_instalacion": True
            },
            "sugerencias_solucion": [
                f"Instalar {tipo} si no está instalado",
                f"Verificar que {tipo} esté en el PATH del sistema",
                "Reiniciar terminal después de la instalación",
                "Usar ruta completa al ejecutable si es necesario"
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "exito": False,
            "error": f"Error ejecutando comando: {str(e)}",
            "return_code": -1,
            "duration": f"{time.time() - start_time:.2f}s",
            "comando_ejecutado": comando,
            "tipo_comando": tipo,
            "diagnostico_error": {
                "tipo_error": "excepcion_inesperada",
                "tipo_excepcion": type(e).__name__,
                "mensaje_completo": str(e),
                "requiere_investigacion": True
            },
            "sugerencias_debug": [
                "Verificar formato y sintaxis del comando",
                "Comprobar permisos del usuario",
                "Revisar logs del sistema",
                "Reportar este error si persiste"
            ],
            "timestamp": datetime.now().isoformat()
        }


def _normalizar_findstr(comando: str) -> str:
    """
    Convierte comandos findstr con múltiples /C: a forma segura usando pipe con type.
    Evita el error 'No se puede abrir /C:return' y conserva las comillas correctamente.
    """
    import re

    try:
        if comando.lower().startswith("findstr") and comando.count("/C:") > 1:
            # Captura archivo con o sin comillas
            match = re.search(
                r'([\w]:[\\/].+?\.(?:py|txt|json|yml|yaml))', comando)
            if not match:
                return comando  # no se encontró archivo

            archivo = match.group(1).strip('"')
            # Extraer todo lo que no sea el archivo (los patrones)
            patrones = comando.split("findstr", 1)[
                1].replace(archivo, "").strip()

            # Construir comando final
            nuevo = f'type "{archivo}" | findstr {patrones}'
            return nuevo
        return comando
    except Exception as e:
        import logging
        logging.warning(f"_normalizar_findstr error: {e}")
        return comando


def _normalizar_type(comando: str) -> str:
    """
    Normaliza comandos type para manejar rutas con espacios.
    """
    try:
        # type "archivo con espacios"
        parts = comando.split()
        if len(parts) >= 2:
            file_arg = ' '.join(parts[1:])  # Todo después de 'type'
            if ' ' in file_arg and not (file_arg.startswith('"') and file_arg.endswith('"')):
                return f'{parts[0]} "{file_arg}"'

        return comando

    except Exception:
        return comando


def _detectar_argumento_faltante(comando: str, error_msg: str) -> Optional[dict]:
    """
    Detecta argumentos faltantes en comandos Azure CLI y sugiere soluciones.
    Usa la misma lógica de detección de intención para inferir valores faltantes.
    """
    try:
        error_lower = error_msg.lower()
        comando_lower = comando.lower()

        # Patrones de detección de argumentos faltantes
        missing_patterns = {
            "--resource-group": {
                "patterns": ["resource group", "--resource-group", "-g", "resource-group is required"],
                "argumento": "--resource-group",
                "descripcion": "Este comando requiere especificar el grupo de recursos",
                "comando_listar": "az group list --output table",
                "sugerencia": "¿Quieres que liste los grupos de recursos disponibles?",
                "valores_comunes": ["boat-rental-app-group", "boat-rental-app-group", "DefaultResourceGroup-EUS2"]
            },
            "--account-name": {
                "patterns": ["account name", "--account-name", "storage account", "account-name is required"],
                "argumento": "--account-name",
                "descripcion": "Este comando requiere el nombre de la cuenta de almacenamiento",
                "comando_listar": "az storage account list --output table",
                "sugerencia": "¿Quieres que liste las cuentas de almacenamiento disponibles?",
                "valores_comunes": ["boatrentalstorage", "copilotostorage"]
            },
            "--name": {
                "patterns": ["function app name", "--name", "app name", "name is required"],
                "argumento": "--name",
                "descripcion": "Este comando requiere el nombre de la aplicación",
                "comando_listar": "az functionapp list --output table" if "functionapp" in comando_lower else "az webapp list --output table",
                "sugerencia": "¿Quieres que liste las aplicaciones disponibles?",
                "valores_comunes": ["copiloto-semantico-func-us2", "boat-rental-app"]
            },
            "--subscription": {
                "patterns": ["subscription", "--subscription", "subscription id"],
                "argumento": "--subscription",
                "descripcion": "Este comando requiere especificar la suscripción",
                "comando_listar": "az account list --output table",
                "sugerencia": "¿Quieres que liste las suscripciones disponibles?",
                "valores_comunes": []
            },
            "--location": {
                "patterns": ["location", "--location", "region"],
                "argumento": "--location",
                "descripcion": "Este comando requiere especificar la ubicación/región",
                "comando_listar": "az account list-locations --output table",
                "sugerencia": "¿Quieres que liste las ubicaciones disponibles?",
                "valores_comunes": ["eastus", "eastus2", "westus2", "centralus"]
            }
        }

        # Buscar patrones en el mensaje de error
        for arg_name, info in missing_patterns.items():
            for pattern in info["patterns"]:
                if pattern in error_lower:
                    # Verificar que el argumento no esté ya en el comando
                    if arg_name not in comando_lower:
                        logging.info(
                            f"🔍 Argumento faltante detectado: {arg_name}")
                        return info

        # Detección específica para Cosmos DB
        if "cosmosdb" in comando_lower and any(pattern in error_lower for pattern in ["account-name", "account name"]):
            return {
                "argumento": "--account-name",
                "descripcion": "Este comando de Cosmos DB requiere el nombre de la cuenta",
                "comando_listar": "az cosmosdb list --output table",
                "sugerencia": "¿Quieres que liste las cuentas de Cosmos DB disponibles?",
                "valores_comunes": ["copiloto-cosmos", "boat-rental-cosmos"]
            }

        # Detección para contenedores de storage
        if "storage" in comando_lower and "container" in comando_lower and any(pattern in error_lower for pattern in ["container-name", "container name"]):
            return {
                "argumento": "--container-name",
                "descripcion": "Este comando requiere el nombre del contenedor de almacenamiento",
                "comando_listar": "az storage container list --account-name <account-name> --output table",
                "sugerencia": "¿Quieres que liste los contenedores disponibles?",
                "valores_comunes": ["boat-rental-project", "scripts", "backups"]
            }

        return None

    except Exception as e:
        logging.warning(f"Error detectando argumento faltante: {e}")
        return None
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "error": str(e),
                "tipo_error": type(e).__name__,
                "comando": comando or "desconocido"
            }),
            mimetype="application/json",
            status_code=500
        )


def _verificar_archivos_en_comando(comando: str) -> dict:
    """
    Verifica si el comando referencia archivos que deben existir antes de ejecutar.
    IGNORA patrones glob y wildcards usados en comandos de búsqueda.
    """
    try:
        from pathlib import Path
        from function_app import PROJECT_ROOT, _locate_file_in_root

        # 🔥 DETECTAR COMANDOS DE BÚSQUEDA QUE USAN PATRONES GLOB
        comandos_busqueda = ['Get-ChildItem', 'gci', 'ls', 'dir',
                             'find', 'grep', 'findstr', '-Include', '-Filter', '-Recurse']
        if any(cmd in comando for cmd in comandos_busqueda):
            logging.info(
                f"✅ Comando de búsqueda detectado, saltando validación de archivos: {comando}")
            return {"exito": True, "mensaje": "Comando de búsqueda - validación de archivos omitida"}

        # Patrones para detectar referencias a archivos (incluye rutas absolutas de Windows)
        extensions = r'(?:py|sh|ps1|bat)'
        file_pattern = re.compile(
            rf'"(?P<double>[^"]+\.{extensions})"|'
            rf"'(?P<single>[^']+\.{extensions})'|"
            rf'(?P<abs_win>[a-zA-Z]:[\\/][^\\s"\'|]+\.{extensions})|'
            rf'(?P<rel>[a-zA-Z0-9_\-./\\]+\.{extensions})',
            re.IGNORECASE
        )

        archivos_referenciados = []
        for match in file_pattern.finditer(comando):
            archivo = match.group('double') or match.group(
                'single') or match.group('abs_win') or match.group('rel')
            if not archivo:
                continue

            # 🔥 IGNORAR PATRONES GLOB Y WILDCARDS
            if any(char in archivo for char in ['*', '?', '[', ']']):
                logging.info(f"⏭️ Ignorando patrón glob: {archivo}")
                continue

            archivos_referenciados.append(archivo)

        if not archivos_referenciados:
            return {"exito": True, "mensaje": "No se detectaron referencias a archivos"}

        # Verificar existencia de cada archivo
        archivos_faltantes = []
        archivos_encontrados = []

        for archivo in archivos_referenciados:
            ruta_encontrada = _locate_file_in_root(archivo, PROJECT_ROOT)

            if ruta_encontrada:
                archivos_encontrados.append({
                    "archivo": archivo,
                    "ruta_completa": str(ruta_encontrada),
                    "tamaño": ruta_encontrada.stat().st_size
                })
            else:
                archivos_faltantes.append({
                    "archivo": archivo,
                    "rutas_verificadas": ["Búsqueda recursiva en " + str(PROJECT_ROOT)]
                })

        if archivos_faltantes:
            return {
                "exito": False,
                "error": f"Archivos no encontrados: {', '.join([a['archivo'] for a in archivos_faltantes])}",
                "diagnostico": {
                    "tipo_error": "archivos_faltantes",
                    "comando_original": comando,
                    "archivos_faltantes": archivos_faltantes,
                    "archivos_encontrados": archivos_encontrados
                },
                "sugerencias_solucion": [
                    "Crear los archivos faltantes antes de ejecutar el comando",
                    "Verificar la ruta correcta de los archivos",
                    "Usar rutas absolutas si es necesario",
                    f"Crear archivo con: /api/escribir-archivo-local"
                ],
                "timestamp": datetime.now().isoformat()
            }

        return {
            "exito": True,
            "mensaje": f"Todos los archivos verificados: {', '.join([a['archivo'] for a in archivos_encontrados])}",
            "archivos_verificados": archivos_encontrados
        }

    except Exception as e:
        logging.warning(f"Error verificando archivos: {e}")
        return {"exito": True, "mensaje": "Verificación de archivos omitida por error"}


@app.function_name(name="ejecutar_cli_http")
@app.route(route="ejecutar-cli", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def ejecutar_cli_http(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint UNIVERSAL - Ejecuta CUALQUIER comando sin validaciones previas"""
    from function_app import PROJECT_ROOT, _auto_resolve_file_paths, IS_AZURE, _locate_file_in_root, _locate_file_in_root
    from memory_manual import aplicar_memoria_manual
    from cosmos_memory_direct import consultar_memoria_cosmos_directo, aplicar_memoria_cosmos_directo
    from services.memory_service import memory_service

    # 🧠 CONSULTAR MEMORIA COSMOS DB DIRECTAMENTE
    memoria_previa = consultar_memoria_cosmos_directo(req)
    if memoria_previa and memoria_previa.get("tiene_historial"):
        logging.info(
            f"🧠 Modificar-archivo: {memoria_previa['total_interacciones']} interacciones encontradas")
        logging.info(
            f"📝 Historial: {memoria_previa.get('resumen_conversacion', '')[:100]}...")
    advertencias = []

    """Endpoint UNIVERSAL para ejecutar comandos - NUNCA falla con HTTP 400"""
    comando = None
    az_paths = []
    try:
        body = req.get_json()
        logging.warning(f"[DEBUG] Payload recibido: {body}")

        # 🔥 EXTRACCIÓN AUTOMÁTICA DE session_id Y agent_id
        _extraer_ids_de_comando(body, req)

        if not body:
            # ✅ CAMBIO: HTTP 200 con mensaje explicativo
            resultado = {
                "exito": False,
                "error": "Request body must be valid JSON",
                "ejemplo": {"comando": "storage account list"},
                "accion_requerida": "Proporciona un comando válido en el campo 'comando'"
            }
            # Aplicar memoria Cosmos y memoria manual
            resultado = aplicar_memoria_cosmos_directo(req, resultado)
            resultado = aplicar_memoria_manual(req, resultado)

            # REGISTRAR LLAMADA PARA TEXTO SEMANTICO
            logging.info(
                f"💾 Registering call for ejecutar_cli: success={resultado.get('exito', False)}, endpoint=/api/ejecutar-cli")
            memory_service.registrar_llamada(
                source="ejecutar_cli",
                endpoint="/api/ejecutar-cli",
                method=req.method,
                params={"session_id": req.headers.get(
                    "Session-ID"), "agent_id": req.headers.get("Agent-ID")},
                response_data=resultado,
                success=resultado.get("exito", False)
            )
            return func.HttpResponse(
                json.dumps(resultado),
                status_code=200,  # ✅ SIEMPRE 200
                mimetype="application/json"
            )

        comando = body.get("comando")

        # 🔥 DECODIFICAR HTML ENTITIES (corrige &#39; -> ')
        if comando:
            import html
            comando_original = comando
            comando = html.unescape(comando)
            if comando != comando_original:
                logging.info(
                    f"🔧 HTML entities decodificadas: {comando_original} -> {comando}")

        # 🔥 DETECCIÓN AUTOMÁTICA DE TIPO DE COMANDO
        tipo_comando = "generic"
        if comando:
            # Detectar comandos PowerShell
            powershell_cmdlets = ['Get-', 'Set-', 'New-', 'Remove-', 'Invoke-', 'Add-', 'Clear-',
                                  'Copy-', 'Export-', 'Import-', 'Move-', 'Select-', 'Test-', 'Where-', 'ForEach-']
            if any(comando.startswith(cmdlet) for cmdlet in powershell_cmdlets):
                tipo_comando = "powershell"
                logging.info(f"✅ Comando PowerShell detectado: {comando}")
            # Detectar comandos Python
            elif comando.startswith('python ') or comando.startswith('pip '):
                tipo_comando = "python"
            # Detectar comandos Azure CLI
            elif comando.startswith('az '):
                tipo_comando = "azure_cli"
            # Detectar comandos Docker
            elif comando.startswith('docker '):
                tipo_comando = "docker"
            # Detectar comandos NPM
            elif comando.startswith('npm '):
                tipo_comando = "npm"

        # 🔥 NORMALIZAR COMANDOS AWK AUTOMÁTICAMENTE
        if comando and 'awk' in comando.lower():
            from validate_awk_command import suggest_awk_fix
            comando_original = comando
            comando = suggest_awk_fix(comando)
            if comando != comando_original:
                logging.info(
                    f"✅ AWK normalizado: {comando_original} -> {comando}")

        # 🔍 AUTO-RESOLVER RUTAS DE ARCHIVOS EN EL COMANDO (ANTES DE CUALQUIER VALIDACIÓN)
        if comando:
            comando = _auto_resolve_file_paths(comando)
            logging.info(f"✅ Comando con rutas resueltas: {comando}")

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
                # Aplicar memoria Cosmos y memoria manual
                resultado = aplicar_memoria_cosmos_directo(req, resultado)
                resultado = aplicar_memoria_manual(req, resultado)

                # REGISTRAR LLAMADA PARA TEXTO SEMANTICO
                logging.info(
                    f"💾 Registering call for ejecutar_cli: success={resultado.get('exito', False)}, endpoint=/api/ejecutar-cli")
                memory_service.registrar_llamada(
                    source="ejecutar_cli",
                    endpoint="/api/ejecutar-cli",
                    method=req.method,
                    params={"session_id": req.headers.get(
                        "Session-ID"), "agent_id": req.headers.get("Agent-ID")},
                    response_data=resultado,
                    success=resultado.get("exito", False)
                )
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
            # Aplicar memoria Cosmos y memoria manual
            resultado = aplicar_memoria_cosmos_directo(req, resultado)
            resultado = aplicar_memoria_manual(req, resultado)

            # REGISTRAR LLAMADA PARA TEXTO SEMANTICO
            logging.info(
                f"💾 Registering call for ejecutar_cli: success={resultado.get('exito', False)}, endpoint=/api/ejecutar-cli")
            memory_service.registrar_llamada(
                source="ejecutar_cli",
                endpoint="/api/ejecutar-cli",
                method=req.method,
                params={"session_id": req.headers.get(
                    "Session-ID"), "agent_id": req.headers.get("Agent-ID")},
                response_data=resultado,
                success=resultado.get("exito", False)
            )
            return func.HttpResponse(
                json.dumps(resultado),
                status_code=200,  # ✅ SIEMPRE 200
                mimetype="application/json"
            )

        # 🔧 Forzar cwd real al del proyecto
        project_root = os.path.dirname(os.path.abspath(__file__))
        os.chdir(project_root)

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
            resultado = {
                "exito": False,
                "error": "Azure CLI no está instalado o no está disponible en el PATH",
                "diagnostico": {
                    "paths_verificados": [p for p in az_paths if p],
                    "sugerencia": "Instalar Azure CLI o verificar PATH",
                    "ambiente": "Azure" if IS_AZURE else "Local"
                }
            }
            # Aplicar memoria Cosmos y memoria manual
            resultado = aplicar_memoria_cosmos_directo(req, resultado)
            resultado = aplicar_memoria_manual(req, resultado)

            # REGISTRAR LLAMADA PARA TEXTO SEMANTICO
            logging.info(
                f"💾 Registering call for ejecutar_cli: success={resultado.get('exito', False)}, endpoint=/api/ejecutar-cli")
            memory_service.registrar_llamada(
                source="ejecutar_cli",
                endpoint="/api/ejecutar-cli",
                method=req.method,
                params={"session_id": req.headers.get(
                    "Session-ID"), "agent_id": req.headers.get("Agent-ID")},
                response_data=resultado,
                success=resultado.get("exito", False)
            )
            return func.HttpResponse(
                json.dumps(resultado),
                status_code=503,
                mimetype="application/json"
            )

        # ✅ VERIFICACIÓN PREVIA: Comprobar existencia de archivos si el comando los referencia
        archivo_verificado = _verificar_archivos_en_comando(comando)
        if not archivo_verificado["exito"]:
            # Aplicar memoria Cosmos y memoria manual
            archivo_verificado = aplicar_memoria_cosmos_directo(
                req, archivo_verificado)
            archivo_verificado = aplicar_memoria_manual(
                req, archivo_verificado)

            # REGISTRAR LLAMADA PARA TEXTO SEMANTICO
            logging.info(
                f"💾 Registering call for ejecutar_cli: success={archivo_verificado.get('exito', False)}, endpoint=/api/ejecutar-cli")
            memory_service.registrar_llamada(
                source="ejecutar_cli",
                endpoint="/api/ejecutar-cli",
                method=req.method,
                params={"session_id": req.headers.get(
                    "Session-ID"), "agent_id": req.headers.get("Agent-ID")},
                response_data=archivo_verificado,
                success=archivo_verificado.get("exito", False)
            )
            return func.HttpResponse(
                json.dumps(archivo_verificado, ensure_ascii=False),
                mimetype="application/json",
                status_code=200  # 200 para que Foundry pueda procesar el error
            )

        # REDIRECCIÓN AUTOMÁTICA: Si no es comando Azure CLI, redirigir a ejecutor genérico
        try:
            from command_type_detector import detect_and_normalize_command

            # Detectar tipo de comando dinámicamente
            detection = detect_and_normalize_command(comando)
            command_type = detection.get("type", "generic")

            logging.info(f"Comando detectado como: {command_type}")

            # Si NO es comando Azure CLI, redirigir automáticamente
            if command_type != "azure_cli":
                logging.info(
                    f"Redirigiendo comando {command_type} a ejecutor genérico")

                # 🔧 NORMALIZACIÓN ROBUSTA para comandos no-Azure CLI
                comando_normalizado = comando  # NO normalizar
                logging.info(f"Comando normalizado: {comando_normalizado}")

                # Usar la función ejecutar_comando_sistema directamente
                resultado = ejecutar_comando_sistema(
                    comando_normalizado, command_type)
                # Aplicar memoria Cosmos y memoria manual
                resultado = aplicar_memoria_cosmos_directo(req, resultado)
                resultado = aplicar_memoria_manual(req, resultado)

                # REGISTRAR LLAMADA PARA TEXTO SEMANTICO
                logging.info(
                    f"💾 Registering call for ejecutar_cli: success={resultado.get('exito', False)}, endpoint=/api/ejecutar-cli")
                memory_service.registrar_llamada(
                    source="ejecutar_cli",
                    endpoint="/api/ejecutar-cli",
                    method=req.method,
                    params={"session_id": req.headers.get(
                        "Session-ID"), "agent_id": req.headers.get("Agent-ID")},
                    response_data=resultado,
                    success=resultado.get("exito", False)
                )
                return func.HttpResponse(
                    json.dumps(resultado, ensure_ascii=False),
                    mimetype="application/json",
                    status_code=200  # ✅ CAMBIO: Siempre 200
                )

            # Normalizar comando Azure CLI
            comando = detection.get("normalized_command", comando)

        except ImportError as e:
            logging.warning(f"No se pudo importar command_type_detector: {e}")
            # Fallback: si no parece Azure CLI, ejecutar como comando genérico
            if not (comando.startswith("az ") or any(keyword in comando.lower() for keyword in ["storage", "group", "functionapp", "webapp", "cosmosdb"])):
                logging.info(
                    "Ejecutando comando no-Azure con fallback genérico")
                # 🔧 NORMALIZACIÓN ROBUSTA para fallback genérico
                comando_normalizado = comando  # NO normalizar
                logging.info(
                    f"Comando fallback normalizado: {comando_normalizado}")
                # Usar la función ejecutar_comando_sistema directamente
                resultado = ejecutar_comando_sistema(
                    comando_normalizado, tipo_comando)
                # Aplicar memoria Cosmos y memoria manual
                resultado = aplicar_memoria_cosmos_directo(req, resultado)
                resultado = aplicar_memoria_manual(req, resultado)

                # REGISTRAR LLAMADA PARA TEXTO SEMANTICO
                logging.info(
                    f"💾 Registering call for ejecutar_cli: success={resultado.get('exito', False)}, endpoint=/api/ejecutar-cli")
                memory_service.registrar_llamada(
                    source="ejecutar_cli",
                    endpoint="/api/ejecutar-cli",
                    method=req.method,
                    params={"session_id": req.headers.get(
                        "Session-ID"), "agent_id": req.headers.get("Agent-ID")},
                    response_data=resultado,
                    success=resultado.get("exito", False)
                )
                return func.HttpResponse(
                    json.dumps(resultado, ensure_ascii=False),
                    mimetype="application/json",
                    status_code=200 if resultado.get("exito") else 500
                )

            # Agregar prefijo az si no lo tiene (se mantiene)
            if not comando.startswith("az "):
                comando = f"az {comando}"

        # 🔧 NORMALIZACIÓN ROBUSTA: Manejar rutas con espacios y caracteres especiales
        comando = comando  # NO normalizar

        # --- Nuevo bloque dinámico: reemplazo automático de placeholders ---
        # Recuperar memoria del agente (si ya tienes contexto cargado)
        memoria = memoria_previa or getattr(req, "_memoria_contexto", {}) or {}
        # Ejemplo explícito si quieres forzar un valor de memoria conocido:
        if not memoria.get("app_insights_name"):
            memoria.setdefault("app_insights_name",
                               "copiloto-semantico-func-us2")
        try:
            comando = _resolver_placeholders_dinamico(comando, memoria)
        except Exception as e:
            logging.warning(f"Falló resolver_placeholders_dinamico: {e}")
        # --- Fin bloque dinámico ---

        # --- BLOQUE ADICIONAL: Ampliar contexto para cat/grep o extraer función completa con awk ---
        try:
            import shlex
            import re

            # Solo aplicar heurística para comandos que usan grep/cat y apuntan a archivos .py
            lower_cmd = comando.lower()
            if ("grep" in lower_cmd or "cat " in lower_cmd) and (".py" in comando or "function_app.py" in comando):
                tokens = shlex.split(comando)
                # intentar localizar archivo y patrón
                file_token = None
                pattern = None
                # file token is likely the last token or explicit .py token
                for t in reversed(tokens):
                    if t.endswith(".py"):
                        file_token = t
                        break
                # pattern: token after grep or quoted regex
                if "grep" in tokens:
                    try:
                        idx = tokens.index("grep")
                        if idx + 1 < len(tokens):
                            pattern = tokens[idx + 1].strip("'\"")
                    except ValueError:
                        pattern = None
                if not pattern:
                    m = re.search(
                        r"grep\s+(?:-n\s+)?['\"]([^'\"]+)['\"]", comando, re.IGNORECASE)
                    if m:
                        pattern = m.group(1)

                # resolver ruta local si es relativa al proyecto
                if file_token:
                    fpath = file_token
                    if not os.path.isabs(fpath):
                        fpath = os.path.join(project_root, fpath)
                    if os.path.exists(fpath) and pattern:
                        # leer archivo y localizar coincidencia
                        try:
                            with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                                lines = fh.read().splitlines()
                        except Exception:
                            lines = []
                        # buscar primer match por substring o regex
                        match_index = None
                        for i, ln in enumerate(lines):
                            if pattern in ln or (re.search(pattern, ln) if re.search(pattern, ln) else False):
                                match_index = i
                                break
                        if match_index is not None:
                            line = lines[match_index]
                            # si la línea es un decorator o contiene def, extraer nombre de la función completa usando awk
                            if "@" in line or "def " in line or line.strip().startswith("def "):
                                # si la línea contiene 'def', extraer nombre directamente; si es decorator, buscar siguiente def
                                fname = None
                                if "def " in line:
                                    m2 = re.search(
                                        r"\bdef\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", line)
                                    if m2:
                                        fname = m2.group(1)
                                else:
                                    # buscar la siguiente def en el archivo
                                    for j in range(match_index, min(match_index + 200, len(lines))):
                                        if "def " in lines[j]:
                                            m3 = re.search(
                                                r"\bdef\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", lines[j])
                                            if m3:
                                                fname = m3.group(1)
                                                break
                                if fname:
                                    # construir awk para extraer desde def hasta línea en blanco siguiente (heurística)
                                    awk_cmd = f"awk '/^def {fname}\\b/,/^$/' \"{fpath}\""
                                    logging.info(
                                        f"🔧 Rewriting grep/cat pipeline to awk to extract full function: {awk_cmd}")
                                    comando = awk_cmd
                                else:
                                    # fallback: ampliar contexto de grep agregando -A/-B si no existen
                                    if "-A" not in comando and "-B" not in comando:
                                        comando = comando.replace(
                                            "grep ", "grep -A 40 -B 5 ", 1)
                                        logging.info(
                                            f"🔧 Ampliado contexto grep: {comando}")
                            else:
                                # Si la línea encontrada no es decorator/def, ampliar contexto igualmente
                                if "-A" not in comando and "-B" not in comando:
                                    comando = comando.replace(
                                        "grep ", "grep -A 40 -B 5 ", 1)
                                    logging.info(
                                        f"🔧 Ampliado contexto grep (no def/decorator): {comando}")
        except Exception as e:
            logging.warning(f"Error optimizando grep/cat/awk extraction: {e}")
        # --- FIN BLOQUE ADICIONAL ---

        # Manejar conflictos de output
        if "-o table" in comando and "--output json" not in comando:
            pass
        elif "--output" not in comando and "-o" not in comando:
            comando += " --output json"

        logging.info(f"Ejecutando: {comando} con binary: {az_binary}")

        # EJECUCIÓN ROBUSTA: Manejar rutas con espacios y comandos complejos
        import shlex

        try:
            # Método 1: Usar shlex para parsing inteligente
            if az_binary != "az":
                # Reemplazar 'az' con ruta completa manteniendo estructura
                if comando.startswith("az "):
                    comando_final = comando.replace(
                        "az ", f'"{az_binary}" ', 1)
                else:
                    comando_final = f'"{az_binary}" {comando}'
            else:
                comando_final = comando

            # Detectar si necesita shell=True (rutas con espacios, pipes, etc.)
            needs_shell = any(char in comando_final for char in [
                              ' && ', ' || ', '|', '>', '<', '"', "'"])

            if needs_shell:
                # Usar shell para comandos complejos
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
                # Usar lista de argumentos para comandos simples
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
                    # Fallback a shell si shlex falla
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
            # Último fallback: shell simple
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

        if result.returncode == 0:
            # Intentar parsear JSON solo si no es tabla
            if "-o table" not in comando:
                try:
                    output_json = json.loads(
                        result.stdout) if result.stdout else []
                    resultado_temp = {
                        "exito": True,
                        "comando": comando,
                        "resultado": output_json,
                        "codigo_salida": result.returncode
                    }
                    # Aplicar memoria Cosmos y memoria manual
                    resultado_temp = aplicar_memoria_cosmos_directo(
                        req, resultado_temp)
                    resultado_temp = aplicar_memoria_manual(
                        req, resultado_temp)

                    # REGISTRAR LLAMADA PARA TEXTO SEMANTICO
                    logging.info(
                        f"💾 Registering call for ejecutar_cli: success={resultado_temp.get('exito', False)}, endpoint=/api/ejecutar-cli")
                    memory_service.registrar_llamada(
                        source="ejecutar_cli",
                        endpoint="/api/ejecutar-cli",
                        method=req.method,
                        params={"session_id": req.headers.get(
                            "Session-ID"), "agent_id": req.headers.get("Agent-ID")},
                        response_data=resultado_temp,
                        success=resultado_temp.get("exito", False)
                    )
                    return func.HttpResponse(
                        json.dumps(resultado_temp),
                        mimetype="application/json",
                        status_code=200
                    )
                except json.JSONDecodeError:
                    pass

            # Devolver como texto si no es JSON válido
            resultado_temp = {
                "exito": True,
                "comando": comando,
                "resultado": result.stdout,
                "codigo_salida": result.returncode,
                "formato": "texto"
            }
            # Aplicar memoria Cosmos y memoria manual
            resultado_temp = aplicar_memoria_cosmos_directo(
                req, resultado_temp)
            resultado_temp = aplicar_memoria_manual(req, resultado_temp)

            # REGISTRAR LLAMADA PARA TEXTO SEMANTICO
            logging.info(
                f"💾 Registering call for ejecutar_cli: success={resultado_temp.get('exito', False)}, endpoint=/api/ejecutar-cli")
            memory_service.registrar_llamada(
                source="ejecutar_cli",
                endpoint="/api/ejecutar-cli",
                method=req.method,
                params={"session_id": req.headers.get(
                    "Session-ID"), "agent_id": req.headers.get("Agent-ID")},
                response_data=resultado_temp,
                success=resultado_temp.get("exito", False)
            )
            return func.HttpResponse(
                json.dumps(resultado_temp),
                mimetype="application/json",
                status_code=200
            )
        else:
            # 🔍 DETECCIÓN DE ARGUMENTOS FALTANTES
            error_msg = result.stderr or "Comando falló sin mensaje de error"

            # Detectar argumentos faltantes comunes
            missing_arg_info = _detectar_argumento_faltante(comando, error_msg)

            if missing_arg_info:
                # 🧠 AUTOCORRECCIÓN CON MEMORIA
                logging.info(
                    f"🔍 Argumento faltante detectado: --{missing_arg_info['argumento']}")

                # Intentar autocorrección con memoria
                try:
                    from memory_helpers_autocorrection import buscar_parametro_en_memoria, obtener_memoria_request

                    memoria_contexto = obtener_memoria_request(req)
                    if memoria_contexto and memoria_contexto.get("tiene_historial"):
                        valor_memoria = buscar_parametro_en_memoria(
                            memoria_contexto,
                            missing_arg_info["argumento"],
                            comando
                        )

                        if valor_memoria:
                            # ✅ REEJECUTAR COMANDO AUTOCORREGIDO
                            comando_corregido = f"{comando} --{missing_arg_info['argumento']} {valor_memoria}"
                            logging.info(
                                f"🧠 Reejecutando con memoria: {comando_corregido}")

                            # Ejecutar comando corregido
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
                                try:
                                    output_json = json.loads(
                                        result_corregido.stdout) if result_corregido.stdout else []
                                except json.JSONDecodeError:
                                    output_json = result_corregido.stdout

                                resultado_temp = {
                                    "exito": True,
                                    "comando_original": comando,
                                    "comando_ejecutado": comando_corregido,
                                    "resultado": output_json,
                                    "codigo_salida": result_corregido.returncode,
                                    "autocorreccion": {
                                        "aplicada": True,
                                        "argumento_corregido": missing_arg_info["argumento"],
                                        "valor_usado": valor_memoria,
                                        "fuente": "memoria_sesion"
                                    },
                                    "mensaje": f"✅ Comando autocorregido usando memoria: --{missing_arg_info['argumento']} {valor_memoria}"
                                }
                                # Aplicar memoria Cosmos y memoria manual
                                resultado_temp = aplicar_memoria_cosmos_directo(
                                    req, resultado_temp)
                                resultado_temp = aplicar_memoria_manual(
                                    req, resultado_temp)

                                # REGISTRAR LLAMADA PARA TEXTO SEMANTICO
                                logging.info(
                                    f"💾 Registering call for ejecutar_cli: success={resultado_temp.get('exito', False)}, endpoint=/api/ejecutar-cli")
                                memory_service.registrar_llamada(
                                    source="ejecutar_cli",
                                    endpoint="/api/ejecutar-cli",
                                    method=req.method,
                                    params={"session_id": req.headers.get(
                                        "Session-ID"), "agent_id": req.headers.get("Agent-ID")},
                                    response_data=resultado_temp,
                                    success=resultado_temp.get("exito", False)
                                )
                                return func.HttpResponse(
                                    json.dumps(resultado_temp),
                                    mimetype="application/json",
                                    status_code=200
                                )
                except Exception as e:
                    logging.warning(f"Error en autocorrección: {e}")

                # ✅ NO SE PUDO AUTOCORREGIR - SOLICITAR AL USUARIO (HTTP 200)
                resultado_temp = {
                    "exito": False,
                    "comando": comando,
                    "error": f"Falta el argumento --{missing_arg_info['argumento']}",
                    "accion_requerida": f"¿Puedes indicarme el valor para --{missing_arg_info['argumento']}?",
                    "diagnostico": {
                        "argumento_faltante": missing_arg_info["argumento"],
                        "descripcion": missing_arg_info["descripcion"],
                        "sugerencia_automatica": missing_arg_info["sugerencia"],
                        "comando_para_listar": missing_arg_info.get("comando_listar"),
                        "valores_comunes": missing_arg_info.get("valores_comunes", []),
                        "memoria_consultada": True,
                        "valor_encontrado_en_memoria": False
                    },
                    "sugerencias": [
                        f"Ejecutar: {missing_arg_info.get('comando_listar', 'az --help')} para ver valores disponibles",
                        f"Proporcionar --{missing_arg_info['argumento']} <valor> en el comando",
                        "El sistema recordará el valor para futuros comandos"
                    ],
                    "ejemplo_corregido": f"{comando} --{missing_arg_info['argumento']} <valor>"
                }
                # Aplicar memoria Cosmos y memoria manual
                resultado_temp = aplicar_memoria_cosmos_directo(
                    req, resultado_temp)
                resultado_temp = aplicar_memoria_manual(req, resultado_temp)

                # REGISTRAR LLAMADA PARA TEXTO SEMANTICO
                logging.info(
                    f"💾 Registering call for ejecutar_cli: success={resultado_temp.get('exito', False)}, endpoint=/api/ejecutar-cli")
                memory_service.registrar_llamada(
                    source="ejecutar_cli",
                    endpoint="/api/ejecutar-cli",
                    method=req.method,
                    params={"session_id": req.headers.get(
                        "Session-ID"), "agent_id": req.headers.get("Agent-ID")},
                    response_data=resultado_temp,
                    success=resultado_temp.get("exito", False)
                )
                return func.HttpResponse(
                    json.dumps(resultado_temp),
                    mimetype="application/json",
                    status_code=200  # ✅ SIEMPRE 200, NUNCA 400
                )

            # Error normal sin argumentos faltantes detectados - MEJORADO
            error_result = {
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
            # Aplicar memoria Cosmos y memoria manual
            error_result = aplicar_memoria_cosmos_directo(req, error_result)
            error_result = aplicar_memoria_manual(req, error_result)

            # REGISTRAR LLAMADA PARA TEXTO SEMANTICO
            logging.info(
                f"💾 Registering call for ejecutar_cli: success={error_result.get('exito', False)}, endpoint=/api/ejecutar-cli")
            memory_service.registrar_llamada(
                source="ejecutar_cli",
                endpoint="/api/ejecutar-cli",
                method=req.method,
                params={"session_id": req.headers.get(
                    "Session-ID"), "agent_id": req.headers.get("Agent-ID")},
                response_data=error_result,
                success=error_result.get("exito", False)
            )
            return func.HttpResponse(
                json.dumps(error_result),
                mimetype="application/json",
                status_code=200  # ✅ CAMBIO: Siempre 200 para que Foundry pueda procesar
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
        # Aplicar memoria Cosmos y memoria manual
        resultado = aplicar_memoria_cosmos_directo(req, resultado)
        resultado = aplicar_memoria_manual(req, resultado)

        # REGISTRAR LLAMADA PARA TEXTO SEMANTICO
        logging.info(
            f"💾 Registering call for ejecutar_cli: success={resultado.get('exito', False)}, endpoint=/api/ejecutar-cli")
        memory_service.registrar_llamada(
            source="ejecutar_cli",
            endpoint="/api/ejecutar-cli",
            method=req.method,
            params={"session_id": req.headers.get(
                "Session-ID"), "agent_id": req.headers.get("Agent-ID")},
            response_data=resultado,
            success=resultado.get("exito", False)
        )
        return func.HttpResponse(
            json.dumps(resultado),
            mimetype="application/json",
            status_code=200  # ✅ CAMBIO: 200 en lugar de 500
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
        # Aplicar memoria Cosmos y memoria manual
        resultado = aplicar_memoria_cosmos_directo(req, resultado)
        resultado = aplicar_memoria_manual(req, resultado)

        # REGISTRAR LLAMADA PARA TEXTO SEMANTICO
        logging.info(
            f"💾 Registering call for ejecutar_cli: success={resultado.get('exito', False)}, endpoint=/api/ejecutar-cli")
        memory_service.registrar_llamada(
            source="ejecutar_cli",
            endpoint="/api/ejecutar-cli",
            method=req.method,
            params={"session_id": req.headers.get(
                "Session-ID"), "agent_id": req.headers.get("Agent-ID")},
            response_data=resultado,
            success=resultado.get("exito", False)
        )
        return func.HttpResponse(
            json.dumps(resultado),
            mimetype="application/json",
            status_code=200  # ✅ CAMBIO: 200 en lugar de 503
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
        # Aplicar memoria Cosmos y memoria manual
        resultado = aplicar_memoria_cosmos_directo(req, resultado)
        resultado = aplicar_memoria_manual(req, resultado)

        # REGISTRAR LLAMADA PARA TEXTO SEMANTICO
        logging.info(
            f"💾 Registering call for ejecutar_cli: success={resultado.get('exito', False)}, endpoint=/api/ejecutar-cli")
        memory_service.registrar_llamada(
            source="ejecutar_cli",
            endpoint="/api/ejecutar-cli",
            method=req.method,
            params={"session_id": req.headers.get(
                "Session-ID"), "agent_id": req.headers.get("Agent-ID")},
            response_data=resultado,
            success=resultado.get("exito", False)
        )
        return func.HttpResponse(
            json.dumps(resultado),
            mimetype="application/json",
            status_code=200  # ✅ CAMBIO: 200 en lugar de 500
        )


def _extraer_ids_de_comando(body: dict, req: func.HttpRequest) -> None:
    """Extrae session_id y agent_id del body o headers y los agrega al body"""
    if not body.get("session_id"):
        body["session_id"] = req.headers.get(
            "Session-ID") or req.headers.get("X-Session-ID")
    if not body.get("agent_id"):
        body["agent_id"] = req.headers.get(
            "Agent-ID") or req.headers.get("X-Agent-ID")
