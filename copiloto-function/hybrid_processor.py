# hybrid_processor.py
# Módulo para procesar respuestas híbridas de agentes (JSON + texto semántico)

import json
import logging
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
import re


class HybridResponseProcessor:
    """Procesa respuestas de agentes que pueden ser JSON, texto o híbridas"""

    def __init__(self):
        self.semantic_templates = {
            "dashboard": "📊 Generando dashboard con insights del proyecto...",
            "diagnosticar:completo": "🔍 Realizando diagnóstico completo del sistema...",
            "guia:debug_errores": "🛠️ Iniciando guía de depuración de errores...",
            "buscar": "🔎 Buscando archivos en el proyecto...",
            "leer": "📄 Leyendo archivo solicitado...",
            "ejecutar:azure": "☁️ Ejecutando comando Azure CLI..."
        }

        self.error_recovery_map = {
            400: "diagnosticar:validacion",
            401: "diagnosticar:autenticacion",
            403: "diagnosticar:permisos",
            404: "buscar:recurso",
            500: "diagnosticar:completo",
            503: "diagnosticar:servicios"
        }

    def process_agent_response(self, agent_response: str, source: str = "agent") -> Dict[str, Any]:
        """
        Procesa una respuesta de agente que puede ser:
        1. JSON puro
        2. Texto con JSON embebido
        3. Solo texto
        4. Híbrido (JSON + explicación)
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "original_response": agent_response,
            "type": None,
            "command": None,
            "semantic_explanation": None,
            "auto_execute": False,
            "next_actions": []
        }

        # Intentar extraer JSON
        json_data, remaining_text = self._extract_json(agent_response)

        if json_data:
            result["type"] = "hybrid" if remaining_text else "json"
            result["command"] = json_data
            result["semantic_explanation"] = remaining_text or self._generate_explanation(
                json_data)

            # Determinar si debe auto-ejecutarse
            result["auto_execute"] = self._should_auto_execute(json_data)

            # Extraer próximas acciones
            if json_data.get("contexto", {}).get("siguiente_accion"):
                result["next_actions"].append(
                    json_data["contexto"]["siguiente_accion"])

        else:
            result["type"] = "text"
            result["semantic_explanation"] = agent_response

            # Intentar inferir intención del texto
            inferred_command = self._infer_command_from_text(agent_response)
            if inferred_command:
                result["command"] = inferred_command
                # Requiere confirmación si es inferido
                result["auto_execute"] = False

        return result

    def _extract_json(self, text: str) -> Tuple[Optional[Dict], str]:
        """Extrae JSON de un texto y retorna el JSON y el texto restante"""

        # Buscar JSON con regex
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text)

        for match in matches:
            try:
                json_data = json.loads(match)
                # Verificar que tiene estructura esperada
                if self._is_valid_command(json_data):
                    # Obtener texto sin el JSON
                    remaining = text.replace(match, "").strip()
                    return json_data, remaining
            except json.JSONDecodeError:
                continue

        # Intentar parsear todo el texto como JSON
        try:
            json_data = json.loads(text)
            if self._is_valid_command(json_data):
                return json_data, ""
        except:
            pass

        return None, text

    def _is_valid_command(self, data: Dict) -> bool:
        """Verifica si un diccionario es un comando válido"""
        required_fields = ["endpoint", "method"]
        return all(field in data for field in required_fields)

    def _should_auto_execute(self, command: Dict) -> bool:
        """Determina si un comando debe ejecutarse automáticamente"""

        # No auto-ejecutar si es destructivo o requiere confirmación
        dangerous_intenciones = ["eliminar", "borrar", "reset", "deploy"]
        if any(d in command.get("intencion", "").lower() for d in dangerous_intenciones):
            return False

        # Auto-ejecutar si tiene alta urgencia
        if command.get("contexto", {}).get("urgencia") == "alta":
            return True

        # Auto-ejecutar comandos de solo lectura
        read_only = ["status", "health", "buscar", "leer", "dashboard"]
        if any(ro in command.get("intencion", "").lower() for ro in read_only):
            return True

        return False

    def _generate_explanation(self, command: Dict) -> str:
        """Genera una explicación semántica para un comando"""

        intencion = command.get("intencion", "")
        endpoint = command.get("endpoint", "")

        # Buscar template que coincida
        for key, template in self.semantic_templates.items():
            if key in intencion or key in endpoint:
                return template

        # Generar explicación genérica
        if endpoint == "ejecutar":
            return f"Ejecutando intención: {intencion}"
        elif endpoint == "copiloto":
            mensaje = command.get("mensaje", "")
            return f"Procesando comando: {mensaje}"
        else:
            return f"Invocando endpoint: {endpoint}"

    def _infer_command_from_text(self, text: str) -> Optional[Dict]:
        """Intenta inferir un comando desde texto plano"""

        text_lower = text.lower()

        # Mapeo de palabras clave a comandos
        if "dashboard" in text_lower:
            return {
                "endpoint": "ejecutar",
                "method": "POST",
                "intencion": "dashboard",
                "parametros": {},
                "modo": "normal"
            }
        elif "diagnóstico" in text_lower or "diagnostico" in text_lower:
            return {
                "endpoint": "ejecutar",
                "method": "POST",
                "intencion": "diagnosticar:completo",
                "parametros": {},
                "modo": "normal"
            }
        elif "error" in text_lower and ("400" in text or "401" in text or "500" in text):
            # Extraer código de error
            import re
            error_code = re.search(r'\b(4\d{2}|5\d{2})\b', text)
            if error_code:
                code = int(error_code.group())
                return {
                    "endpoint": "ejecutar",
                    "method": "POST",
                    "intencion": self.error_recovery_map.get(code, "diagnosticar:completo"),
                    "parametros": {"error_code": code},
                    "modo": "guiado"
                }
        elif "buscar" in text_lower or "busca" in text_lower:
            return {
                "endpoint": "copiloto",
                "method": "GET",
                "mensaje": "buscar:*"
            }

        return None

    def execute_with_recovery(self, command: Dict, executor_func) -> Dict[str, Any]:
        """
        Ejecuta un comando con recuperación automática si falla

        Args:
            command: Comando a ejecutar
            executor_func: Función que ejecuta el comando
        """

        result = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "execution_result": None,
            "recovery_attempted": False,
            "final_status": "pending"
        }

        try:
            # Intentar ejecutar comando principal
            execution_result = executor_func(command)
            result["execution_result"] = execution_result

            # Verificar si fue exitoso
            if execution_result.get("exito") or execution_result.get("status") == "healthy":
                result["final_status"] = "success"
            else:
                # Si falló y hay acción de recuperación
                if command.get("contexto", {}).get("siguiente_accion"):
                    result["recovery_attempted"] = True
                    recovery_command = {
                        "endpoint": "ejecutar",
                        "method": "POST",
                        "intencion": command["contexto"]["siguiente_accion"],
                        "parametros": {
                            "error_original": execution_result.get("error", "Error desconocido")
                        },
                        "modo": "normal"
                    }

                    recovery_result = executor_func(recovery_command)
                    result["recovery_result"] = recovery_result

                    if recovery_result.get("exito"):
                        result["final_status"] = "recovered"
                    else:
                        result["final_status"] = "failed"
                else:
                    result["final_status"] = "failed"

        except Exception as e:
            result["error"] = str(e)
            result["final_status"] = "error"

            # Intentar diagnóstico automático en caso de excepción
            if command.get("contexto", {}).get("urgencia") == "alta":
                try:
                    diagnostic_command = {
                        "endpoint": "ejecutar",
                        "method": "POST",
                        "intencion": "diagnosticar:completo",
                        "parametros": {"error": str(e)},
                        "modo": "normal"
                    }
                    diagnostic_result = executor_func(diagnostic_command)
                    result["diagnostic_result"] = diagnostic_result
                except:
                    pass

        return result

    def generate_user_response(self, processing_result: Dict) -> str:
        """Genera una respuesta amigable para el usuario basada en el resultado del procesamiento"""

        response_parts = []

        # Agregar explicación semántica
        if processing_result.get("semantic_explanation"):
            response_parts.append(processing_result["semantic_explanation"])

        # Agregar estado de ejecución
        if processing_result.get("execution_result"):
            exec_result = processing_result["execution_result"]

            if exec_result.get("exito"):
                response_parts.append("\n✅ Comando ejecutado exitosamente")
            elif exec_result.get("error"):
                response_parts.append(f"\n⚠️ Error: {exec_result['error']}")

            # Agregar información relevante del resultado
            if exec_result.get("resultado"):
                if isinstance(exec_result["resultado"], dict):
                    if exec_result["resultado"].get("sugerencias"):
                        response_parts.append("\n💡 Sugerencias:")
                        for sug in exec_result["resultado"]["sugerencias"]:
                            response_parts.append(f"  • {sug}")

        # Si hubo recuperación
        if processing_result.get("recovery_attempted"):
            if processing_result.get("final_status") == "recovered":
                response_parts.append(
                    "\n🔄 Se ejecutó una acción de recuperación exitosamente")
            else:
                response_parts.append(
                    "\n⚠️ Se intentó recuperación pero no fue exitosa")

        # Agregar próximas acciones
        if processing_result.get("next_actions"):
            response_parts.append("\n\n📌 Próximas acciones disponibles:")
            for action in processing_result["next_actions"]:
                response_parts.append(f"  • {action}")

        return "\n".join(response_parts)


# Función auxiliar para integrar con function_app.py
def process_hybrid_request(req_body: dict, executor_func) -> dict:
    """
    Procesa una petición que puede venir de un agente con respuesta híbrida

    Args:
        req_body: Cuerpo de la petición
        executor_func: Función para ejecutar comandos
    """

    processor = HybridResponseProcessor()

    # Si viene un campo 'agent_response', procesarlo
    if "agent_response" in req_body:
        # Procesar respuesta del agente
        processed = processor.process_agent_response(
            req_body["agent_response"],
            req_body.get("agent_name", "unknown")
        )

        # Si hay comando y debe auto-ejecutarse
        if processed["command"] and processed["auto_execute"]:
            execution_result = processor.execute_with_recovery(
                processed["command"],
                executor_func
            )

            # Generar respuesta para el usuario
            user_response = processor.generate_user_response({
                **processed,
                **execution_result
            })

            return {
                "success": True,
                "processing_details": processed,
                "execution_details": execution_result,
                "user_response": user_response,
                "metadata": {
                    "auto_executed": True,
                    "timestamp": datetime.now().isoformat()
                }
            }
        else:
            # Solo retornar el procesamiento sin ejecutar
            return {
                "success": True,
                "processing_details": processed,
                "user_response": processed["semantic_explanation"],
                "requires_confirmation": True,
                "command_ready": processed["command"],
                "metadata": {
                    "auto_executed": False,
                    "timestamp": datetime.now().isoformat()
                }
            }

    # Si es una petición normal, procesarla directamente
    return {
        "success": False,
        "error": "No agent response provided",
        "fallback": "Use standard processing"
    }
