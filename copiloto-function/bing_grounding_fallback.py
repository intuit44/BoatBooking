#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de fallback con Bing Grounding para resolver consultas ambiguas
"""

import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional


def ejecutar_bing_grounding_fallback(query: str, contexto: str, error_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Ejecuta Bing Grounding como fallback para consultas ambiguas
    """
    try:
        logging.info(f"🔍 Ejecutando Bing Grounding para: {query[:50]}...")

        # Preparar payload para Bing Grounding
        bing_payload = {
            "query": query,
            "contexto": contexto,
            "intencion_original": query,
            "prioridad": "alta" if "error" in contexto else "media"
        }

        # Intentar llamar al endpoint de Bing Grounding
        try:
            # Simular llamada a Bing Grounding (implementar según tu API)
            resultado_bing = simular_bing_grounding(query, contexto)

            if resultado_bing.get("exito"):
                # Registrar en memoria semántica
                try:
                    from services.memory_service import memory_service
                    memory_service.log_semantic_event({
                        "tipo": "bing_grounding_success",
                        "texto_semantico": f"Bing Grounding éxito para query: {query}",
                        "query_original": query,
                        "comando_sugerido": resultado_bing.get("comando_sugerido"),
                        "contexto": contexto
                    })
                except:
                    pass

                return {
                    "exito": True,
                    "fuente": "bing_grounding",
                    "query_original": query,
                    "resultado": resultado_bing,
                    "accion_sugerida": resultado_bing.get("accion_sugerida", "revisar_sugerencia"),
                    "comando_ejecutable": resultado_bing.get("comando_sugerido"),
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "contexto": contexto,
                        "confianza": resultado_bing.get("confianza", 0.8)
                    }
                }
            else:
                return generar_fallback_local(query, contexto, error_info)

        except Exception as bing_error:
            logging.warning(f"Error en Bing Grounding: {bing_error}")
            return generar_fallback_local(query, contexto, error_info)

    except Exception as e:
        logging.error(f"Error crítico en Bing Grounding fallback: {e}")
        return {
            "exito": False,
            "error": str(e),
            "query_original": query,
            "fallback_usado": "error_critico"
        }


def simular_bing_grounding(query: str, contexto: str) -> Dict[str, Any]:
    """
    Simula Bing Grounding con lógica inteligente local
    TODO: Reemplazar con llamada real a Bing Search API
    """
    query_lower = query.lower()

    # Mapeo inteligente de consultas comunes
    azure_mappings = {
        # Cosmos DB
        ("cosmos", "list"): {
            "comando_sugerido": "az cosmosdb list --output json",
            "resumen": "Para listar cuentas de Cosmos DB, usa el comando az cosmosdb list",
            "confianza": 0.95
        },
        ("cosmos", "crear"): {
            "comando_sugerido": "az cosmosdb create --name <nombre> --resource-group <grupo>",
            "resumen": "Para crear una cuenta de Cosmos DB, usa az cosmosdb create",
            "confianza": 0.90
        },

        # Storage
        ("storage", "list"): {
            "comando_sugerido": "az storage account list --output json",
            "resumen": "Para listar cuentas de almacenamiento, usa az storage account list",
            "confianza": 0.95
        },
        ("storage", "crear"): {
            "comando_sugerido": "az storage account create --name <nombre> --resource-group <grupo>",
            "resumen": "Para crear una cuenta de almacenamiento, usa az storage account create",
            "confianza": 0.90
        },

        # Resource Groups
        ("resource", "list"): {
            "comando_sugerido": "az group list --output json",
            "resumen": "Para listar grupos de recursos, usa az group list",
            "confianza": 0.95
        },
        ("grupo", "list"): {
            "comando_sugerido": "az group list --output json",
            "resumen": "Para listar grupos de recursos, usa az group list",
            "confianza": 0.95
        },

        # Function Apps
        ("function", "list"): {
            "comando_sugerido": "az functionapp list --output json",
            "resumen": "Para listar Function Apps, usa az functionapp list",
            "confianza": 0.95
        },

        # Web Apps
        ("webapp", "list"): {
            "comando_sugerido": "az webapp list --output json",
            "resumen": "Para listar Web Apps, usa az webapp list",
            "confianza": 0.95
        }
    }

    # Buscar coincidencias
    for (service, action), mapping in azure_mappings.items():
        if service in query_lower and (action in query_lower or "list" in query_lower or "ver" in query_lower):
            return {
                "exito": True,
                "comando_sugerido": mapping["comando_sugerido"],
                "resumen": mapping["resumen"],
                "confianza": mapping["confianza"],
                "fuentes": ["Azure CLI Documentation"],
                "accion_sugerida": "ejecutar_comando"
            }

    # Fallback genérico para Azure
    if "azure" in query_lower or "az" in query_lower:
        return {
            "exito": True,
            "comando_sugerido": "az --help",
            "resumen": "Para obtener ayuda general de Azure CLI, usa az --help",
            "confianza": 0.7,
            "fuentes": ["Azure CLI Help"],
            "accion_sugerida": "mostrar_ayuda"
        }

    return {"exito": False, "error": "No se encontró mapeo para la consulta"}


def generar_fallback_local(query: str, contexto: str, error_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Genera respuesta de fallback local cuando Bing Grounding no está disponible
    """
    query_lower = query.lower()

    # Sugerencias basadas en palabras clave
    sugerencias = []

    if "cosmos" in query_lower:
        sugerencias.extend([
            "az cosmosdb list - Listar cuentas de Cosmos DB",
            "az cosmosdb show --name <nombre> --resource-group <grupo> - Ver detalles",
            "az cosmosdb create - Crear nueva cuenta"
        ])

    if "storage" in query_lower:
        sugerencias.extend([
            "az storage account list - Listar cuentas de almacenamiento",
            "az storage account show --name <nombre> - Ver detalles",
            "az storage account create - Crear nueva cuenta"
        ])

    if "resource" in query_lower or "grupo" in query_lower:
        sugerencias.extend([
            "az group list - Listar grupos de recursos",
            "az group show --name <nombre> - Ver detalles del grupo",
            "az group create - Crear nuevo grupo"
        ])

    if not sugerencias:
        sugerencias = [
            "az --help - Ayuda general de Azure CLI",
            "az <servicio> --help - Ayuda específica de un servicio",
            "az account show - Ver información de la cuenta actual"
        ]

    return {
        "exito": True,
        "fuente": "fallback_local",
        "query_original": query,
        "mensaje": f"No pude encontrar una respuesta específica para '{query}', pero aquí tienes algunas sugerencias:",
        "sugerencias": sugerencias,
        "accion_sugerida": "revisar_sugerencias",
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "contexto": contexto,
            "tipo_fallback": "local_suggestions"
        }
    }


def ejecutar_comando_sugerido(comando: str) -> Dict[str, Any]:
    """
    Ejecuta automáticamente un comando sugerido por Bing Grounding
    """
    try:
        # Llamar al endpoint ejecutar-cli interno
        import requests

        payload = {"comando": comando}
        response = requests.post(
            "http://localhost:7071/api/ejecutar-cli",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "exito": True,
                "comando_ejecutado": comando,
                "resultado": data,
                "fuente": "auto_execution"
            }
        else:
            return {
                "exito": False,
                "error": f"Error ejecutando comando: {response.status_code}",
                "comando": comando
            }

    except Exception as e:
        return {
            "exito": False,
            "error": str(e),
            "comando": comando
        }
