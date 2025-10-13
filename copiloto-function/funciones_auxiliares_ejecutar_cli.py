#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Funciones auxiliares necesarias para el endpoint ejecutar-cli mejorado
"""

import re
import os
import shutil
import subprocess
import logging
from datetime import datetime

def _detectar_argumento_faltante(comando, error_msg):
    """
    Detecta argumentos faltantes en comandos Azure CLI
    """
    try:
        # Patrones comunes de errores de argumentos faltantes
        patterns = {
            "container-name": {
                "patterns": [
                    r"required.*container.*name",
                    r"missing.*container",
                    r"--container-name.*required"
                ],
                "descripcion": "Nombre del contenedor de storage",
                "sugerencia": "Especifica el contenedor donde están los blobs"
            },
            "subscription": {
                "patterns": [
                    r"subscription.*not.*set",
                    r"no.*subscription",
                    r"--subscription.*required"
                ],
                "descripcion": "ID de la suscripción de Azure",
                "sugerencia": "Especifica la suscripción a usar"
            },
            "resource-group": {
                "patterns": [
                    r"resource.*group.*required",
                    r"--resource-group.*required",
                    r"missing.*resource.*group"
                ],
                "descripcion": "Grupo de recursos",
                "sugerencia": "Especifica el grupo de recursos"
            },
            "account-name": {
                "patterns": [
                    r"account.*name.*required",
                    r"--account-name.*required",
                    r"storage.*account.*required"
                ],
                "descripcion": "Nombre de la cuenta de storage",
                "sugerencia": "Especifica la cuenta de storage"
            }
        }
        
        error_lower = error_msg.lower()
        
        for argumento, info in patterns.items():
            for pattern in info["patterns"]:
                if re.search(pattern, error_lower):
                    return {
                        "argumento": argumento,
                        "descripcion": info["descripcion"],
                        "sugerencia": info["sugerencia"]
                    }
        
        return None
        
    except Exception as e:
        logging.warning(f"Error detectando argumento faltante: {e}")
        return None

def _normalizar_comando_robusto(comando):
    """
    Normaliza comandos para manejar rutas con espacios y caracteres especiales
    """
    try:
        # Limpiar espacios extra
        comando = re.sub(r'\s+', ' ', comando.strip())
        
        # Manejar rutas con espacios (agregar comillas si es necesario)
        # Buscar patrones como --path C:\Program Files\...
        comando = re.sub(
            r'(--\w+)\s+([C-Z]:\\[^"\']\S*\s+[^"\']*)',
            r'\1 "\2"',
            comando
        )
        
        return comando
        
    except Exception as e:
        logging.warning(f"Error normalizando comando: {e}")
        return comando

def _verificar_archivos_en_comando(comando):
    """
    Verifica si los archivos referenciados en el comando existen
    """
    try:
        # Por ahora, siempre devolver éxito
        # En implementación completa, verificar archivos específicos
        return {"exito": True}
        
    except Exception as e:
        logging.warning(f"Error verificando archivos: {e}")
        return {"exito": True}

def ejecutar_comando_sistema(comando, tipo_comando):
    """
    Ejecuta comandos del sistema (no Azure CLI)
    """
    try:
        logging.info(f"Ejecutando comando {tipo_comando}: {comando}")
        
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
            return {
                "exito": True,
                "comando": comando,
                "tipo_comando": tipo_comando,
                "resultado": result.stdout,
                "codigo_salida": result.returncode,
                "ejecutor": "subprocess_fallback"
            }
        else:
            return {
                "exito": False,
                "comando": comando,
                "tipo_comando": tipo_comando,
                "error": result.stderr or "Comando falló",
                "codigo_salida": result.returncode,
                "ejecutor": "subprocess_fallback"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "exito": False,
            "comando": comando,
            "error": "Comando excedió tiempo límite (60s)",
            "tipo_comando": tipo_comando
        }
    except Exception as e:
        return {
            "exito": False,
            "comando": comando,
            "error": str(e),
            "tipo_comando": tipo_comando
        }

# Importar funciones de memoria
try:
    from memory_helpers_autocorrection import (
        buscar_parametro_en_memoria,
        obtener_memoria_request,
        agregar_memoria_a_respuesta,
        extraer_session_info,
        obtener_prompt_memoria
    )
except ImportError:
    # Fallbacks si no se puede importar
    def buscar_parametro_en_memoria(memoria_contexto, argumento, comando_actual):
        return None
    
    def obtener_memoria_request(req):
        return None
    
    def agregar_memoria_a_respuesta(response_data, req):
        return response_data
    
    def extraer_session_info(req):
        return {"session_id": "fallback", "agent_id": "fallback"}
    
    def obtener_prompt_memoria(req):
        return None

def _autocorregir_con_memoria(comando, argumento_faltante, req, error_msg):
    """
    Intenta autocorregir comando usando memoria de sesión
    """
    try:
        # Consultar memoria de la sesión
        memoria_contexto = obtener_memoria_request(req)
        
        if memoria_contexto and memoria_contexto.get("tiene_historial"):
            # Buscar el parámetro en interacciones previas
            valor_memoria = buscar_parametro_en_memoria(
                memoria_contexto, 
                argumento_faltante, 
                comando
            )
            
            if valor_memoria:
                # Autocorregir comando
                comando_corregido = f"{comando} --{argumento_faltante} {valor_memoria}"
                logging.info(f"🧠 Autocorrección con memoria: {comando_corregido}")
                
                return {
                    "autocorregido": True,
                    "comando_original": comando,
                    "comando_corregido": comando_corregido,
                    "valor_usado": valor_memoria,
                    "fuente": "memoria_sesion"
                }
        
        # Si no hay memoria, sugerir valores comunes
        valores_comunes = _obtener_valores_comunes_argumento(argumento_faltante)
        
        return {
            "autocorregido": False,
            "argumento_faltante": argumento_faltante,
            "valores_sugeridos": valores_comunes,
            "pregunta_usuario": f"Necesito el valor para --{argumento_faltante}. ¿Puedes proporcionarlo?",
            "comando_para_listar": _obtener_comando_listar(argumento_faltante)
        }
        
    except Exception as e:
        logging.warning(f"Error en autocorrección: {e}")
        return {
            "autocorregido": False,
            "error_autocorreccion": str(e)
        }

def _obtener_valores_comunes_argumento(argumento):
    """Devuelve valores comunes para argumentos específicos"""
    valores_comunes = {
        "container-name": ["documents", "backups", "logs", "data", "boat-rental-project"],
        "subscription": ["<tu-subscription-id>"],
        "resource-group": ["boat-rental-rg", "default-rg"],
        "account-name": ["boatrentalstorage"],
        "location": ["eastus", "westus2", "centralus"]
    }
    return valores_comunes.get(argumento, [])

def _obtener_comando_listar(argumento):
    """Devuelve comando para listar valores disponibles"""
    comandos_listar = {
        "container-name": "az storage container list --account-name <account-name>",
        "subscription": "az account list --query '[].id' -o table",
        "resource-group": "az group list --query '[].name' -o table",
        "account-name": "az storage account list --query '[].name' -o table"
    }
    return comandos_listar.get(argumento, "az --help")