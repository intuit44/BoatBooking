# -*- coding: utf-8 -*-
import requests, json, time, threading

def iniciar_autodiagnostico():
    base = "https://copiloto-semantico-func-us2.azurewebsites.net/api"

    def ciclo():
        while True:
            try:
                r1 = requests.get(f"{base}/verificar-sistema", timeout=10).json()
                r2 = requests.get(f"{base}/verificar-app-insights", timeout=10).json()
                r3 = requests.get(f"{base}/verificar-cosmos", timeout=10).json()

                estado = {
                    "cpu": r1.get("memoria", {}).get("percent"),
                    "telemetria": r2.get("exito"),
                    "cosmos": r3.get("exito"),
                    "timestamp": time.time()
                }

                if not estado["cosmos"]:
                    accion = "⚠️ Sin conexión a CosmosDB"
                elif not estado["telemetria"]:
                    accion = "⚠️ Telemetría inactiva"
                elif estado["cpu"] and estado["cpu"] > 85:
                    accion = "⚠️ Carga elevada"
                else:
                    accion = "✅ Estado óptimo"

                print(f"[MONITOR] {accion} ({estado})")

                try:
                    from services.memory_service import memory_service
                    memory_service.log_event("estado_sistema", {
                        "accion": accion,
                        "estado": estado
                    })
                except Exception:
                    pass

            except Exception as e:
                print(f"[MONITOR] Error durante autodiagnóstico: {e}")

            time.sleep(600)  # cada 10 minutos

    threading.Thread(target=ciclo, daemon=True).start()