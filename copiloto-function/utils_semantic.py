# utils_semantic.py
import re


def explain_arm_cause(cause_text: str) -> dict:
    t = cause_text or ""
    t_low = t.lower()

    if "authorizationfailed" in t_low or "does not have authorization" in t_low:
        return {
            "titulo": "Falta permiso en la identidad administrada",
            "pasos": [
                "Asigna rol Contributor a la Managed Identity del Function App.",
                "Reintenta el deploy."
            ],
            "comandos": [
                'set $pid = (az functionapp identity show -g boat-rental-app-group -n copiloto-semantico-func --query principalId -o tsv)',
                'az role assignment create --assignee $pid --role Contributor --scope /subscriptions/380fa841-83f3-42fe-adc4-582a5ebe139b/resourceGroups/boat-rental-app-group'
            ],
            "accion": 'Reintenta el deploy con el mismo payload.'
        }

    if "already taken" in t_low or "name is not available" in t_low or "StorageAccountAlreadyTaken".lower() in t_low:
        sugerido = f"storagebrv{__import__('random').randrange(100000,999999)}"
        return {
            "titulo": "El nombre de la Storage Account no está disponible",
            "pasos": ["Usa un nombre único global y en minúsculas.", "Reintenta el deployment."],
            "comandos": [f'(usa name="{sugerido}")'],
            "accion": f'Reintenta cambiando "name" a "{sugerido}".'
        }

    if "invalidtemplate" in t_low or "template validation failed" in t_low:
        return {
            "titulo": "Plantilla ARM inválida",
            "pasos": [
                "Verifica que template.resources tenga al menos un recurso con type/apiVersion/name/location/properties.",
                "Si usas parameters, envía { \"param\": { \"value\": ... } }."
            ],
            "accion": "Valida primero con \"validate_only\": true antes de desplegar."
        }

    if "template_uri" in t_low or "blob" in t_low and ("404" in t_low or "not found" in t_low or "forbidden" in t_low):
        return {
            "titulo": "No se pudo descargar la plantilla (templateUri)",
            "pasos": [
                "Asegura que el blob exista y sea público o agrega SAS de lectura.",
                "Prueba inline para descartar permisos de blob."
            ],
            "accion": "Reintenta con plantilla inline o corrige el acceso del blob."
        }

    return {
        "titulo": "Error al desplegar",
        "pasos": ["Revisa credenciales, nombre del recurso y estructura del template.", "Valida con validate_only."],
        "accion": "Reintenta tras aplicar los ajustes."
    }


def render_tool_response(status_code: int, payload: dict) -> str:
    """
    Render semántico:
    - deploy si hay señales de despliegue (deploymentName/state/resourceGroup).
    - genérico en el resto (ping, scripts, etc.).
    Mantiene validate_only y tu manejo de errores.
    """
    ok = (200 <= status_code < 300) and payload.get("ok", True)

    # Señales de despliegue (en payload nivel raíz o dentro de data)
    data = payload.get("data") or {}
    is_deployish = any(k in payload for k in ("deploymentName", "state", "resourceGroup")) or \
        any(k in data for k in ("deploymentName", "state", "resourceGroup"))

    # Éxito
    if ok:
        # Caso de validación (lo dejas tal cual)
        if payload.get("mode") == "validate_only":
            return ("Validación correcta ✅\n"
                    f"RG: {payload.get('resourceGroup')} · Ubicación: {payload.get('location')}\n"
                    f"Template: {'inline' if payload.get('hasTemplate') else 'URI'} · Parámetros: {', '.join(payload.get('parameters_keys', [])) or '—'}\n"
                    "Puedes retirar \"validate_only\" para desplegar.")

        # Plantilla de despliegue solo si realmente es deploy
        if is_deployish:
            state = payload.get("state") or data.get("state") or "Unknown"
            rg = payload.get("resourceGroup") or data.get("resourceGroup")
            name = payload.get("deploymentName") or data.get("deploymentName")
            return (f"Despliegue iniciado/terminado ✅ · estado: {state}\n"
                    f"RG: {rg} · Deployment: {name}")

        # Genérico (ping, scripts, etc.)
        msg = data.get("message") or "Operación exitosa"
        return f"OK · {msg}"

    # Error controlado de tu API (lo mantengo igual)
    if payload.get("ok") is False:
        titulo = payload.get("error_code") or "Error"
        causa = payload.get("cause")
        hint = payload.get("hint")
        pasos = payload.get("next_steps") or []
        extra = explain_arm_cause(str(causa)) if (payload.get(
            "error_code") == "ARM_HTTP_ERROR" or "authorization" in str(causa).lower()) else {}
        msg = [f"❌ {titulo}", f"Causa: {causa}"]
        if hint:
            msg.append(f"Sugerencia: {hint}")
        if pasos:
            msg.append("Siguientes pasos:\n- " + "\n- ".join(pasos))
        if extra:
            msg.append(f"Diagnóstico: {extra['titulo']}")
            msg.append("Cómo resolver:\n- " + "\n- ".join(extra["pasos"]))
            if extra.get("comandos"):
                msg.append("Comandos útiles:\n" +
                           "\n".join(f"- {c}" for c in extra["comandos"]))
            msg.append(f"Acción: {extra['accion']}")
        return "\n".join(msg)

    # Error de transporte/formato (lo mantengo)
    return f"❌ Error de transporte o formato (HTTP {status_code}). Reintenta y, si persiste, revisa logs del Function App."
