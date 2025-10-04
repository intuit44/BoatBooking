#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parche para autocorregir_http: detectar webhooks de Azure Monitor
"""
import json
from datetime import datetime
from pathlib import Path

def patch_autocorregir_function():
    """Agrega detección de webhooks de Azure Monitor a autocorregir_http"""
    
    # Código a insertar después de run_id = get_run_id(req)
    azure_monitor_patch = '''
    # PARCHE: Detectar webhook de Azure Monitor
    user_agent = req.headers.get("User-Agent", "")
    content_type = req.headers.get("Content-Type", "")
    
    # Si es webhook de Azure Monitor, manejar diferente
    if "Azure-Monitor" in user_agent or "microsoft" in user_agent.lower():
        try:
            # Registrar evento de alerta de Azure Monitor
            alert_data = req.get_json() or {}
            
            # Log del evento de alerta
            try:
                from services.memory_service import memory_service
                if memory_service:
                    memory_service.log_event("alerta_azure_monitor", {
                        "fecha": datetime.now().isoformat(),
                        "origen": "Azure Monitor",
                        "alerta_id": alert_data.get("data", {}).get("alertContext", {}).get("id", "unknown"),
                        "severidad": alert_data.get("data", {}).get("essentials", {}).get("severity", "unknown"),
                        "estado": alert_data.get("data", {}).get("essentials", {}).get("monitorCondition", "unknown"),
                        "descripcion": alert_data.get("data", {}).get("essentials", {}).get("description", "Alerta de Azure Monitor")
                    }, session_id=run_id)
            except ImportError:
                pass  # memory_service no disponible
            
            # Crear fix automático para HTTP 500
            if "500" in str(alert_data).lower() or "error" in str(alert_data).lower():
                auto_fix = {
                    "id": f"azure-monitor-{run_id[:8]}",
                    "timestamp": datetime.now().isoformat(),
                    "run_id": run_id,
                    "estado": "pendiente",
                    "accion": "investigar_error_http_500",
                    "target": "function_app_logs",
                    "propuesta": "Revisar logs y aplicar fix automático si es posible",
                    "tipo": "error_critico",
                    "detonante": "azure_monitor_alert",
                    "origen": "Azure Monitor Webhook",
                    "prioridad": 8,
                    "validaciones_requeridas": ["revisar_logs", "diagnostico_automatico"],
                    "intentos": 0,
                    "simulacion": {
                        "exito_esperado": True,
                        "cambios_esperados": ["Diagnóstico automático", "Fix si es posible"],
                        "riesgos": [],
                        "rollback_disponible": True
                    }
                }
                
                # Guardar en pending_fixes
                pending_fixes = _load_pending_fixes()
                pending_fixes.append(auto_fix)
                _save_pending_fixes(pending_fixes)
                
                return func.HttpResponse(
                    json.dumps({
                        "exito": True,
                        "mensaje": "Alerta de Azure Monitor procesada",
                        "fix_creado": auto_fix["id"],
                        "run_id": run_id
                    }, ensure_ascii=False),
                    status_code=200
                )
            
            return func.HttpResponse(
                json.dumps({
                    "exito": True,
                    "mensaje": "Webhook de Azure Monitor recibido",
                    "run_id": run_id
                }, ensure_ascii=False),
                status_code=200
            )
            
        except Exception as e:
            # Log del error pero no fallar
            try:
                from services.memory_service import memory_service
                if memory_service:
                    memory_service.log_event("error_webhook_azure", {
                        "fecha": datetime.now().isoformat(),
                        "origen": "Azure Monitor",
                        "error": str(e)
                    }, session_id=run_id)
            except ImportError:
                pass  # memory_service no disponible
            
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": f"Error procesando webhook: {str(e)}",
                    "run_id": run_id
                }),
                status_code=500
            )
    '''
    
    print("Parche creado para detectar webhooks de Azure Monitor")
    print("Insertar este código después de: run_id = get_run_id(req)")
    print("\n" + azure_monitor_patch)
    
    return azure_monitor_patch

if __name__ == "__main__":
    patch_autocorregir_function()