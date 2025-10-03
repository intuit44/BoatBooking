#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parche v2 más tolerante para autocorregir_http
"""
import re

def apply_tolerant_patch():
    """Aplica un parche más tolerante que detecta cualquier webhook"""
    
    # Leer el archivo
    with open("function_app.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Código del parche más tolerante
    patch_code = '''
    # PARCHE V2: Detectar webhooks (más tolerante)
    user_agent = req.headers.get("User-Agent", "")
    content_type = req.headers.get("Content-Type", "")
    
    # Si NO tiene el header X-Agent-Auth, probablemente es un webhook
    agent_header = req.headers.get("X-Agent-Auth", "")
    if not agent_header:
        try:
            # Registrar cualquier webhook sin autenticación
            alert_data = req.get_json() or {}
            
            # Log del evento de webhook
            _log_semantic_event({
                "tipo": "webhook_recibido",
                "fecha": datetime.now().isoformat(),
                "origen": "Webhook Externo",
                "user_agent": user_agent,
                "content_type": content_type,
                "headers": dict(req.headers),
                "body_preview": str(alert_data)[:200] if alert_data else "sin body",
                "run_id": run_id
            })
            
            # Crear fix automático para cualquier webhook
            auto_fix = {
                "id": f"webhook-{run_id[:8]}",
                "timestamp": datetime.now().isoformat(),
                "run_id": run_id,
                "estado": "pendiente",
                "accion": "procesar_webhook_automatico",
                "target": "webhook_handler",
                "propuesta": "Webhook procesado automáticamente",
                "tipo": "webhook_processing",
                "detonante": "webhook_externo",
                "origen": "Webhook Handler",
                "prioridad": 7,
                "validaciones_requeridas": ["log_webhook"],
                "intentos": 0,
                "simulacion": {
                    "exito_esperado": True,
                    "cambios_esperados": ["Log de webhook", "Procesamiento automático"],
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
                    "mensaje": "Webhook procesado automáticamente",
                    "fix_creado": auto_fix["id"],
                    "run_id": run_id,
                    "debug": {
                        "user_agent": user_agent,
                        "content_type": content_type,
                        "body_keys": list(alert_data.keys()) if alert_data else []
                    }
                }, ensure_ascii=False),
                status_code=200
            )
            
        except Exception as e:
            # Log del error
            _log_semantic_event({
                "tipo": "error_webhook",
                "fecha": datetime.now().isoformat(),
                "origen": "Webhook Handler",
                "error": str(e),
                "run_id": run_id
            })
            
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": f"Error procesando webhook: {str(e)}",
                    "run_id": run_id
                }),
                status_code=500
            )
'''
    
    # Buscar el parche anterior y reemplazarlo
    old_patch_pattern = r'(\s+# PARCHE: Detectar webhook de Azure Monitor.*?status_code=500\s+\)\s+)'
    
    if re.search(old_patch_pattern, content, re.DOTALL):
        # Reemplazar el parche anterior
        new_content = re.sub(old_patch_pattern, patch_code + '\n', content, flags=re.DOTALL)
        print("Reemplazando parche anterior...")
    else:
        # Si no existe el parche anterior, buscar donde insertar
        pattern = r'(run_id = get_run_id\(req\)\s*\n)'
        if re.search(pattern, content):
            new_content = re.sub(pattern, r'\1' + patch_code + '\n', content)
            print("Insertando nuevo parche...")
        else:
            print("No se encontró donde insertar el parche")
            return False
    
    # Escribir el archivo modificado
    with open("function_app.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print("Parche v2 aplicado exitosamente")
    print("Ahora detectará CUALQUIER webhook sin X-Agent-Auth")
    return True

if __name__ == "__main__":
    apply_tolerant_patch()