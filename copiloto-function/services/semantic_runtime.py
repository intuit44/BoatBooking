#!/usr/bin/env python3
"""
Cerebro semántico autónomo - Runtime de autoconciencia
"""
import os
import time
import requests
import threading
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configuración
BASE_URL = os.getenv("FUNCTION_BASE_URL",
                     "") or "https://copiloto-semantico-func-us2.azurewebsites.net"
PERIOD = int(os.getenv("SEMANTIC_PERIOD_SEC", "300"))  # 5 minutos
MAX_HOURLY = int(os.getenv("SEMANTIC_MAX_ACTIONS_PER_HOUR", "6"))
AUTOPILOT_ENABLED = os.getenv("SEMANTIC_AUTOPILOT", "off").lower() == "on"


class SemanticRuntime:
    """Cerebro semántico autónomo del agente"""

    def __init__(self):
        self.actions_window = []
        self.memory = []
        self.running = False

    def _get_sensor_data(self, path: str) -> Dict[str, Any]:
        """Lee datos de sensores (endpoints de diagnóstico)"""
        try:
            response = requests.get(
                f"{BASE_URL}{path}",
                timeout=20,
                headers={"Accept": "application/json"}
            )
            if response.ok and "application/json" in response.headers.get("Content-Type", ""):
                return response.json()
        except Exception as e:
            logging.warning(f"Sensor {path} failed: {e}")
        return {}

    def _safe_execute(self, command_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta comando de forma segura vía endpoint inteligente"""
        try:
            response = requests.post(
                f"{BASE_URL}/api/ejecutar-comando-inteligente",
                json={
                    "comando": command_dict.get("comando", "az"),
                    "intencion": command_dict.get("intencion", ""),
                    "parametros": command_dict.get("parametros", {})
                },
                timeout=60,
                headers={"Accept": "application/json"}
            )
            return response.json() if response.ok else {
                "exito": False,
                "error": f"HTTP {response.status_code}"
            }
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def _process_with_hybrid(self, state_insight: str) -> Dict[str, Any]:
        """Procesa estado usando HybridResponseProcessor"""
        try:
            response = requests.post(
                f"{BASE_URL}/api/hybrid",
                json={"agent_response": state_insight, "source": "autopilot"},
                timeout=30,
                headers={"Accept": "application/json"}
            )
            return response.json() if response.ok else {}
        except Exception as e:
            logging.warning(f"Hybrid processing failed: {e}")
            return {}

    def _should_execute(self, processed: Dict[str, Any]) -> bool:
        """Determina si debe ejecutar una acción (política de seguridad)"""
        now = time.time()

        # Limpiar ventana de acciones (solo últimas 1 hora)
        self.actions_window = [
            t for t in self.actions_window if now - t < 3600]

        # Verificar presupuesto horario
        if len(self.actions_window) >= MAX_HOURLY:
            return False

        # Verificar que sea auto-ejecutable
        if not processed.get("auto_execute", False):
            return False

        # Verificar que tenga comando válido
        if not processed.get("command"):
            return False

        return True

    def _persist_cycle(self, state: Dict[str, Any], interpretation: Dict[str, Any], action_taken: bool, result: Optional[Dict[str, Any]] = None):
        """Persiste ciclo en memoria (CosmosDB vía endpoint)"""
        try:
            cycle_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "state_snapshot": state,
                "interpretation": interpretation,
                "action_taken": action_taken,
                "result": result,
                "cycle_type": "semantic_autopilot"
            }

            # Guardar en memoria local
            self.memory.append(cycle_data)
            if len(self.memory) > 100:  # Mantener solo últimos 100 ciclos
                self.memory.pop(0)

            # TODO: Persistir en CosmosDB vía endpoint
            # requests.post(f"{BASE_URL}/api/memory-service", json=cycle_data)

        except Exception as e:
            logging.warning(f"Memory persistence failed: {e}")

    def _semantic_cycle(self):
        """Ciclo principal de autoconciencia semántica"""
        try:
            # 1. PERCEPCIÓN: Leer sensores
            sistema = self._get_sensor_data("/api/verificar-sistema")
            app_insights = self._get_sensor_data("/api/verificar-app-insights")
            cosmos = self._get_sensor_data("/api/verificar-cosmos")

            # 2. ESTADO COMPACTO
            state = {
                "cpu": sistema.get("cpu_percent", 0),
                "memoria": sistema.get("memoria", {}).get("percent", 0),
                "telemetria_activa": app_insights.get("telemetria_activa", False),
                "cosmos_conectado": cosmos.get("cosmos_conectado", False),
                "timestamp": datetime.utcnow().isoformat(),
                "ambiente": sistema.get("ambiente", "Unknown")
            }

            # 3. RAZONAMIENTO: Crear insight semántico
            insight = (
                f"diagnostico autonomo: cpu={state['cpu']}% "
                f"memoria={state['memoria']}% "
                f"telemetria={'activa' if state['telemetria_activa'] else 'inactiva'} "
                f"cosmos={'conectado' if state['cosmos_conectado'] else 'desconectado'} "
                f"ambiente={state['ambiente']}"
            )

            # 4. INTERPRETACIÓN: Procesar con HybridResponseProcessor
            interpretation = self._process_with_hybrid(insight)

            # 5. DECISIÓN: Evaluar si debe actuar
            action_taken = False
            result = None

            if self._should_execute(interpretation):
                # 6. ACCIÓN: Ejecutar comando inteligente
                result = self._safe_execute(interpretation["command"])
                action_taken = True
                self.actions_window.append(time.time())

                logging.info(
                    f"Semantic action executed: {interpretation['command']}")

            # 7. MEMORIA: Persistir ciclo completo
            self._persist_cycle(state, interpretation, action_taken, result)

            # 8. TELEMETRÍA: Enviar a Application Insights
            # TODO: Enviar customEvent vía endpoint

        except Exception as e:
            logging.error(f"Semantic cycle error: {e}")

    def start(self):
        """Inicia el runtime semántico autónomo"""
        print("🧠 Iniciando cerebro semántico autónomo...")
        autopilot_status = "on" if AUTOPILOT_ENABLED else "off"
        print(f"[CONFIG] Autopilot: {autopilot_status}")
        print(f"[CONFIG] Period: {PERIOD} sec")
        print(f"[CONFIG] Max hourly actions: {MAX_HOURLY}")

        if not AUTOPILOT_ENABLED:
            logging.info(
                "Semantic autopilot disabled (SEMANTIC_AUTOPILOT=off)")
            return

        if self.running:
            return

        self.running = True
        logging.info(
            f"Starting semantic runtime (period={PERIOD}s, max_hourly={MAX_HOURLY})")

        def _loop():
            while self.running:
                print(
                    f"[CICLO] Iniciando nuevo ciclo a las {datetime.now().isoformat()}")
                try:
                    self._semantic_cycle()
                except Exception as e:
                    logging.error(f"Semantic loop error: {e}")

                time.sleep(PERIOD)

        # Ejecutar en hilo daemon
        thread = threading.Thread(target=_loop, daemon=True)
        thread.start()

        logging.info("Semantic runtime started successfully")

    def stop(self):
        """Detiene el runtime semántico"""
        self.running = False
        logging.info("Semantic runtime stopped")


# Instancia global
semantic_runtime = SemanticRuntime()


def start_semantic_loop():
    """Función de conveniencia para iniciar el cerebro semántico"""
    semantic_runtime.start()


def stop_semantic_loop():
    """Función de conveniencia para detener el cerebro semántico"""
    semantic_runtime.stop()
