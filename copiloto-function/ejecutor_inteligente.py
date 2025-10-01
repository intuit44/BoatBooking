import subprocess
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

def ejecutar_comando_inteligente(
    comando_base: str, 
    intencion: str, 
    parametros: Optional[Dict[str, Any]] = None,
    contexto: Optional[str] = None
) -> Dict[str, Any]:
    """
    Wrapper genérico inteligente que implementa el flujo universal:
    help → validar → ejecutar → autocorregir
    
    Args:
        comando_base: Comando base (ej: "az monitor", "kubectl", "git")
        intencion: Lo que quiere hacer (ej: "crear alerta HTTP 500")
        parametros: Parámetros específicos del contexto
        contexto: Contexto adicional (resource group, namespace, etc.)
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
        sintaxis = _descubrir_sintaxis(comando_base, intencion)
        
        if not sintaxis["exito"]:
            resultado["error"] = f"No se pudo descubrir sintaxis: {sintaxis['error']}"
            return resultado
        
        # PASO 2: Construir comando candidato
        resultado["proceso"].append("2. Construyendo comando candidato")
        comando_candidato = _construir_comando(
            comando_base, intencion, parametros, sintaxis["info"], contexto
        )
        
        # PASO 3: Validación previa (dry-run si está disponible)
        resultado["proceso"].append("3. Validando comando")
        validacion = _validar_comando(comando_candidato, comando_base)
        
        if validacion["tiene_dry_run"] and not validacion["valido"]:
            resultado["proceso"].append("3a. Dry-run falló, ajustando comando")
            comando_candidato = _ajustar_comando(comando_candidato, validacion["error"])
        
        # PASO 4: Ejecución
        resultado["proceso"].append("4. Ejecutando comando")
        resultado["comando_ejecutado"] = comando_candidato
        
        ejecucion = _ejecutar_comando_seguro(comando_candidato)
        
        if ejecucion["exito"]:
            resultado["exito"] = True
            resultado["salida"] = ejecucion["salida"]
        else:
            # PASO 5: Autocorrección
            resultado["proceso"].append("5. Comando falló, iniciando autocorrección")
            correccion = _autocorregir_comando(
                comando_candidato, ejecucion["error"], sintaxis["info"]
            )
            
            if correccion["comando_corregido"]:
                resultado["proceso"].append("5a. Reintentando con comando corregido")
                resultado["comando_ejecutado"] = correccion["comando_corregido"]
                
                reintentar = _ejecutar_comando_seguro(correccion["comando_corregido"])
                if reintentar["exito"]:
                    resultado["exito"] = True
                    resultado["salida"] = reintentar["salida"]
                    resultado["autocorregido"] = True
                else:
                    resultado["error"] = f"Falló incluso después de autocorrección: {reintentar['error']}"
            else:
                resultado["error"] = f"No se pudo autocorregir: {ejecucion['error']}"
    
    except Exception as e:
        resultado["error"] = f"Error interno: {str(e)}"
    
    return resultado

def _descubrir_sintaxis(comando_base: str, intencion: str) -> Dict[str, Any]:
    """Descubre la sintaxis real usando --help"""
    try:
        # Intentar diferentes variantes de help
        help_commands = [
            f"{comando_base} --help",
            f"{comando_base} -h",
            f"{comando_base} help"
        ]
        
        # Para comandos específicos, intentar help del subcomando
        if "monitor" in intencion and "alert" in intencion:
            help_commands.insert(0, f"{comando_base} metrics alert create --help")
        elif "kubectl" in comando_base and "create" in intencion:
            help_commands.insert(0, f"{comando_base} create --help")
        
        for help_cmd in help_commands:
            try:
                result = subprocess.run(
                    help_cmd.split(),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 and result.stdout:
                    return {
                        "exito": True,
                        "info": _parsear_help_output(result.stdout, intencion),
                        "help_usado": help_cmd
                    }
            except:
                continue
        
        return {"exito": False, "error": "No se pudo obtener help"}
        
    except Exception as e:
        return {"exito": False, "error": str(e)}

def _parsear_help_output(help_text: str, intencion: str) -> Dict[str, Any]:
    """Parsea el output del --help para extraer sintaxis relevante"""
    info = {
        "parametros_requeridos": [],
        "parametros_opcionales": [],
        "ejemplos": [],
        "sintaxis_base": None
    }
    
    lines = help_text.split('\n')
    
    # Buscar sintaxis base (Usage: o similar)
    for line in lines:
        if line.strip().startswith(('Usage:', 'usage:', 'USAGE:')):
            info["sintaxis_base"] = line.strip()
            break
    
    # Buscar parámetros requeridos y opcionales
    in_options = False
    for line in lines:
        line = line.strip()
        
        if line.lower().startswith(('options:', 'arguments:', 'parameters:')):
            in_options = True
            continue
            
        if in_options and line.startswith('-'):
            # Parsear línea de opción
            if line.startswith('--'):
                param_match = re.match(r'--(\w+)', line)
                if param_match:
                    param_name = param_match.group(1)
                    is_required = '[required]' in line.lower() or '<' in line
                    
                    if is_required:
                        info["parametros_requeridos"].append(param_name)
                    else:
                        info["parametros_opcionales"].append(param_name)
    
    # Buscar ejemplos
    in_examples = False
    for line in lines:
        if line.lower().startswith(('examples:', 'example:')):
            in_examples = True
            continue
        
        if in_examples and line.strip():
            if line.strip().startswith(comando_base.split()[0]):
                info["ejemplos"].append(line.strip())
    
    return info

def _construir_comando(
    comando_base: str, 
    intencion: str, 
    parametros: Optional[Dict[str, Any]], 
    sintaxis_info: Dict[str, Any],
    contexto: Optional[str]
) -> str:
    """Construye el comando usando la sintaxis descubierta y la intención"""
    
    # Mapeo inteligente basado en la intención
    if "alerta" in intencion.lower() and "http 500" in intencion.lower():
        # Caso específico: alerta Azure Monitor
        cmd_parts = [comando_base, "metrics", "alert", "create"]
        
        # Parámetros básicos inferidos de la intención
        if parametros:
            if "resource_group" in parametros:
                cmd_parts.extend(["--resource-group", parametros["resource_group"]])
            if "function_app" in parametros:
                cmd_parts.extend(["--scopes", f"/subscriptions/{parametros.get('subscription_id', 'SUBSCRIPTION_ID')}/resourceGroups/{parametros['resource_group']}/providers/Microsoft.Web/sites/{parametros['function_app']}"])
        
        cmd_parts.extend([
            "--name", "AlertaHTTP500Auto",
            "--condition", "count requests where resultCode == '500' > 0",
            "--description", "Alerta automática para HTTP 500",
            "--severity", "2"
        ])
        
        return " ".join(cmd_parts)
    
    # Construcción genérica basada en sintaxis descubierta
    cmd_parts = comando_base.split()
    
    # Agregar parámetros requeridos si están disponibles
    for param_req in sintaxis_info.get("parametros_requeridos", []):
        if parametros and param_req in parametros:
            cmd_parts.extend([f"--{param_req}", str(parametros[param_req])])
    
    return " ".join(cmd_parts)

def _validar_comando(comando: str, comando_base: str) -> Dict[str, Any]:
    """Valida el comando usando dry-run si está disponible"""
    
    # Comandos que soportan dry-run
    dry_run_support = {
        "kubectl": "--dry-run=client",
        "az deployment": "validate",
        "terraform": "plan"
    }
    
    tiene_dry_run = False
    for cmd_pattern, dry_flag in dry_run_support.items():
        if cmd_pattern in comando:
            tiene_dry_run = True
            try:
                # Construir comando de validación
                if "validate" in dry_flag:
                    cmd_validacion = comando.replace("create", "validate")
                else:
                    cmd_validacion = f"{comando} {dry_flag}"
                
                result = subprocess.run(
                    cmd_validacion.split(),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                return {
                    "tiene_dry_run": True,
                    "valido": result.returncode == 0,
                    "error": result.stderr if result.returncode != 0 else None
                }
            except:
                pass
            break
    
    return {"tiene_dry_run": False, "valido": True}

def _ajustar_comando(comando: str, error_validacion: str) -> str:
    """Ajusta el comando basado en el error de validación"""
    
    # Ajustes comunes basados en errores típicos
    if "required" in error_validacion.lower():
        # Extraer parámetro faltante
        required_match = re.search(r"'([^']+)' is required", error_validacion)
        if required_match:
            param_faltante = required_match.group(1)
            # Agregar parámetro con valor placeholder
            comando += f" --{param_faltante} PLACEHOLDER_{param_faltante.upper()}"
    
    if "invalid" in error_validacion.lower() and "format" in error_validacion.lower():
        # Ajustar formato de parámetros
        comando = comando.replace("'", '"')
    
    return comando

def _ejecutar_comando_seguro(comando: str) -> Dict[str, Any]:
    """Ejecuta el comando de forma segura con timeout"""
    try:
        result = subprocess.run(
            comando.split(),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return {
            "exito": result.returncode == 0,
            "salida": result.stdout,
            "error": result.stderr,
            "codigo_salida": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"exito": False, "error": "Comando excedió timeout de 60s"}
    except Exception as e:
        return {"exito": False, "error": str(e)}

def _autocorregir_comando(comando: str, error: str, sintaxis_info: Dict[str, Any]) -> Dict[str, Any]:
    """Autocorrige el comando basado en el error y la sintaxis conocida"""
    
    comando_corregido = comando
    correcciones_aplicadas = []
    
    # Correcciones basadas en errores comunes
    if "not found" in error.lower():
        correcciones_aplicadas.append("Comando no encontrado - verificar instalación")
        return {"comando_corregido": None, "correcciones": correcciones_aplicadas}
    
    if "permission denied" in error.lower():
        # Intentar con sudo si es apropiado
        if not comando.startswith("sudo"):
            comando_corregido = f"sudo {comando}"
            correcciones_aplicadas.append("Agregado sudo para permisos")
    
    if "invalid argument" in error.lower():
        # Buscar argumentos inválidos y corregir formato
        if "'" in comando and '"' not in comando:
            comando_corregido = comando.replace("'", '"')
            correcciones_aplicadas.append("Cambiado comillas simples por dobles")
    
    if "resource group" in error.lower() and "not found" in error.lower():
        # Sugerir verificar resource group
        correcciones_aplicadas.append("Resource group no encontrado - verificar nombre")
    
    return {
        "comando_corregido": comando_corregido if correcciones_aplicadas else None,
        "correcciones": correcciones_aplicadas
    }

# Función de conveniencia para casos específicos
def crear_alerta_azure_monitor(
    resource_group: str,
    function_app: str,
    subscription_id: str,
    webhook_url: Optional[str] = None
) -> Dict[str, Any]:
    """Wrapper específico para crear alertas de Azure Monitor"""
    
    parametros = {
        "resource_group": resource_group,
        "function_app": function_app,
        "subscription_id": subscription_id
    }
    
    if webhook_url:
        parametros["webhook_url"] = webhook_url
    
    return ejecutar_comando_inteligente(
        comando_base="az monitor",
        intencion="crear alerta HTTP 500",
        parametros=parametros,
        contexto="Azure Function App monitoring"
    )