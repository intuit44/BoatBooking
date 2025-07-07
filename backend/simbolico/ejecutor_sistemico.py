import os
import subprocess
import logging
import json
import time
import tempfile
import shutil
import time

from typing import Dict, Any
from datetime import datetime

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def obtener_timestamp() -> str:
    """Obtiene timestamp de forma segura"""
    try:
        return datetime.now().isoformat()
    except Exception:
        return str(time.time())

def validar_json(contenido: str) -> bool:
    """Valida si el contenido es JSON válido"""
    try:
        json.loads(contenido)
        return True
    except json.JSONDecodeError:
        return False

def crear_archivo_simbolico(data: Dict[str, Any]) -> Dict[str, Any]:
    """Crea un archivo con contenido simbólico estructurado de forma segura"""
    try:
        ruta = data.get("ruta", "")
        contenido = data.get("contenido", "")
        metadatos = data.get("metadatos", {})
        
        if not ruta:
            raise ValueError("La clave 'ruta' no puede estar vacía")
        
        ruta = os.path.normpath(ruta)
        directorio = os.path.dirname(ruta)
        
        # Crear directorio si no existe
        if directorio:
            os.makedirs(directorio, exist_ok=True)
        
        # Estructura simbólica del archivo
        estructura_simbolica = {
            "tipo": "archivo_simbolico",
            "ruta": ruta,
            "contenido_preview": contenido[:100] + "..." if len(contenido) > 100 else contenido,
            "metadatos": metadatos,
            "timestamp": obtener_timestamp()
        }
        
        contenido_convertido = contenido.replace("\\n", "\n")
        
        # Para archivos JSON, validar contenido
        if ruta.endswith('.json'):
            if not validar_json(contenido_convertido):
                logger.warning(f"El contenido no es JSON válido para: {ruta}")
                # Intentar corregir JSON común
                try:
                    contenido_parseado = json.loads(contenido_convertido + "}")
                    contenido_convertido = json.dumps(contenido_parseado, indent=2)
                except:
                    return {"error": "Contenido JSON inválido", "status": "error"}
        
        # Escribir archivo usando archivo temporal para evitar corrupción
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as temp_file:
            if not ruta.endswith('.json'):
                temp_file.write(f"# ARCHIVO SIMBÓLICO\n# {json.dumps(estructura_simbolica, indent=2)}\n\n")
            temp_file.write(contenido_convertido)
            temp_path = temp_file.name
        
        # Mover archivo temporal al destino final
        shutil.move(temp_path, ruta)
        
        logger.info(f"Archivo simbólico creado exitosamente: {ruta}")
        return {"status": "success", "archivo": ruta, "estructura": estructura_simbolica}
        
    except Exception as e:
        logger.error(f"Error al crear archivo simbólico: {str(e)}")
        return {"error": str(e), "status": "error"}

def actualizar_archivo_simbolico(data: Dict[str, Any]) -> Dict[str, Any]:
    """Actualiza un archivo manteniendo su estructura simbólica de forma segura"""
    try:
        ruta = data.get("ruta", "")
        contenido = data.get("contenido", "")
        operacion = data.get("operacion", "reemplazar")
        
        if not ruta:
            raise ValueError("La clave 'ruta' no puede estar vacía")
        
        ruta = os.path.normpath(ruta)
        
        if not os.path.exists(ruta):
            raise FileNotFoundError(f"El archivo no existe: {ruta}")
        
        # Crear backup antes de modificar
        backup_path = ruta + f".backup.{int(time.time())}"
        shutil.copy2(ruta, backup_path)
        
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido_actual = f.read()
            
            contenido_convertido = contenido.replace("\\n", "\n")
            
            # Para archivos JSON, manejar de forma especial
            if ruta.endswith('.json'):
                if operacion == "reemplazar":
                    if not validar_json(contenido_convertido):
                        raise ValueError("El nuevo contenido no es JSON válido")
                    nuevo_contenido = contenido_convertido
                elif operacion == "agregar":
                    # Para JSON, agregar significa fusionar objetos
                    try:
                        json_actual = json.loads(contenido_actual)
                        json_nuevo = json.loads(contenido_convertido)
                        if isinstance(json_actual, dict) and isinstance(json_nuevo, dict):
                            json_actual.update(json_nuevo)
                            nuevo_contenido = json.dumps(json_actual, indent=2)
                        else:
                            raise ValueError("Solo se pueden fusionar objetos JSON")
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Error al parsear JSON: {e}")
                else:
                    raise ValueError(f"Operación '{operacion}' no soportada para archivos JSON")
            else:
                # Para archivos no-JSON, usar lógica original
                if operacion == "reemplazar":
                    nuevo_contenido = contenido_convertido
                elif operacion == "agregar":
                    nuevo_contenido = contenido_actual + "\n" + contenido_convertido
                elif operacion == "insertar":
                    lineas = contenido_actual.split("\n")
                    posicion = data.get("posicion", 0)
                    lineas.insert(posicion, contenido_convertido)
                    nuevo_contenido = "\n".join(lineas)
                else:
                    raise ValueError(f"Operación no soportada: {operacion}")
            
            # Escribir usando archivo temporal
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as temp_file:
                temp_file.write(nuevo_contenido)
                temp_path = temp_file.name
            
            # Mover archivo temporal al destino
            shutil.move(temp_path, ruta)
            
            # Eliminar backup si todo salió bien
            os.remove(backup_path)
            
            logger.info(f"Archivo simbólico actualizado: {ruta}")
            return {"status": "success", "archivo": ruta, "operacion": operacion}
            
        except Exception as e:
            # Restaurar backup en caso de error
            if os.path.exists(backup_path):
                shutil.move(backup_path, ruta)
                logger.info(f"Archivo restaurado desde backup: {ruta}")
            raise e
            
    except Exception as e:
        logger.error(f"Error al actualizar archivo simbólico: {str(e)}")
        return {"error": str(e), "status": "error"}

def ejecutar_comando_simbolico(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ejecuta comandos con contexto simbólico y timeout"""
    try:
        comando = data.get("comando", "")
        contexto = data.get("contexto", {})
        capturar_salida = data.get("capturar_salida", True)
        timeout = data.get("timeout", 30)  # Timeout por defecto de 30 segundos
        
        if not comando:
            raise ValueError("El comando no puede estar vacío")
        
        env = os.environ.copy()
        env.update(contexto.get("variables_entorno", {}))
        
        logger.info(f"Ejecutando comando: {comando}")
        
        resultado = subprocess.run(
            comando, 
            shell=True, 
            capture_output=capturar_salida, 
            text=True, 
            env=env,
            cwd=contexto.get("directorio_trabajo", None),
            timeout=timeout
        )
        
        return {
            "comando": comando,
            "codigo_salida": resultado.returncode,
            "salida": resultado.stdout if capturar_salida else "No capturada",
            "error": resultado.stderr if capturar_salida else "No capturada",
            "status": "success" if resultado.returncode == 0 else "error"
        }
        
    except subprocess.TimeoutExpired:
        logger.error(f"Comando excedió el timeout de {timeout}s: {comando}")
        return {"error": f"Comando excedió timeout de {timeout}s", "status": "timeout"}
    except Exception as e:
        logger.error(f"Error al ejecutar comando simbólico: {str(e)}")
        return {"error": str(e), "status": "error"}

def procesar_accion_simbolica(data: Dict[str, Any]) -> Dict[str, Any]:
    """Procesador principal de acciones simbólicas con validación mejorada"""
    try:
        accion = data.get("accion", "").lower().strip()
        
        # Validar que tenemos una acción
        if not accion:
            raise ValueError("No se especificó ninguna acción")
        
        # Log de la acción que se va a procesar
        logger.info(f"Procesando acción: {accion}")
        
        if "crear" in accion and "archivo" in accion:
            return crear_archivo_simbolico(data)
        elif "actualizar" in accion and "archivo" in accion:
            return actualizar_archivo_simbolico(data)
        elif "ejecutar" in accion and "comando" in accion:
            return ejecutar_comando_simbolico(data)
        else:
            return {"error": f"Acción no reconocida: {accion}", "status": "error", "acciones_disponibles": ["crear archivo", "actualizar archivo", "ejecutar comando"]}
            
    except Exception as e:
        logger.error(f"Error al procesar acción: {str(e)}")
        return {"error": str(e), "status": "error"}

# Funciones adicionales para compatibilidad
def ejecutar_accion(data: Dict[str, Any]) -> Dict[str, Any]:
    """Alias para mantener compatibilidad"""
    return procesar_accion_simbolica(data)

# Función específica para manejar settings.json de VS Code
from typing import Optional

def actualizar_settings_vscode(nuevas_configuraciones: Dict[str, Any], ruta_settings: Optional[str] = None) -> Dict[str, Any]:
    """Función especializada para actualizar settings.json de VS Code de forma segura"""
    try:
        if not ruta_settings:
            # Detectar ruta automáticamente
            home = os.path.expanduser("~")
            ruta_settings = os.path.join(home, "AppData", "Roaming", "Code", "User", "settings.json")
            if not os.path.exists(ruta_settings):
                ruta_settings = os.path.join(home, ".vscode", "settings.json")
        
        # Usar la función de actualización con operación específica para JSON
        data = {
            "ruta": ruta_settings,
            "contenido": json.dumps(nuevas_configuraciones, indent=2),
            "operacion": "agregar"
        }
        
        return actualizar_archivo_simbolico(data)
        
    except Exception as e:
        logger.error(f"Error al actualizar settings de VS Code: {str(e)}")
        return {"error": str(e), "status": "error"}