"""
Endpoint: /api/introspection
Permite al agente conocer su propia estructura (autopercepción)
"""
import logging
import json
import os
import sys
import yaml
import azure.functions as func

from pathlib import Path
from datetime import datetime
from function_app import app

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


@app.function_name(name="introspection")
@app.route(route="introspection", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def introspection_http(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint de autopercepción: devuelve estructura interna del sistema
    """

    try:
        # monitoreo, correccion, diagnostico, etc.
        categoria = req.params.get("categoria")

        # Leer openapi.yaml para obtener todos los endpoints
        openapi_path = Path(__file__).parent.parent / "openapi.yaml"

        endpoints_map = {}

        if openapi_path.exists():
            with open(openapi_path, 'r', encoding='utf-8') as f:
                openapi_spec = yaml.safe_load(f)

            paths = openapi_spec.get("paths", {})

            for path, methods in paths.items():
                for method, details in methods.items():
                    if method in ["get", "post", "put", "delete", "patch"]:
                        tags = details.get("tags", ["Sin categoría"])
                        summary = details.get("summary", "")

                        # Categorizar endpoints
                        categoria_endpoint = "general"
                        if any(k in summary.lower() for k in ["diagnóstico", "diagnostico", "validar", "verificar"]):
                            categoria_endpoint = "diagnostico"
                        elif any(k in summary.lower() for k in ["monitoreo", "monitor", "error", "log"]):
                            categoria_endpoint = "monitoreo"
                        elif any(k in summary.lower() for k in ["corrección", "correccion", "fix", "reparar"]):
                            categoria_endpoint = "correccion"
                        elif any(k in summary.lower() for k in ["memoria", "historial", "interacción"]):
                            categoria_endpoint = "memoria"
                        elif any(k in summary.lower() for k in ["configurar", "settings", "app settings"]):
                            categoria_endpoint = "configuracion"

                        if categoria_endpoint not in endpoints_map:
                            endpoints_map[categoria_endpoint] = []

                        endpoints_map[categoria_endpoint].append({
                            "path": path,
                            "method": method.upper(),
                            "summary": summary,
                            "tags": tags,
                            "operationId": details.get("operationId", "")
                        })

        # Si se solicita una categoría específica
        if categoria:
            categoria_lower = categoria.lower()
            endpoints_categoria = endpoints_map.get(categoria_lower, [])

            return func.HttpResponse(
                json.dumps({
                    "exito": True,
                    "categoria": categoria,
                    "endpoints": endpoints_categoria,
                    "total": len(endpoints_categoria),
                    "mensaje": f"Encontrados {len(endpoints_categoria)} endpoints de categoría '{categoria}'",
                    "categorias_disponibles": list(endpoints_map.keys())
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=200
            )

        # Devolver resumen completo con respuesta_usuario clara
        total_eps = sum(len(v) for v in endpoints_map.values())
        capacidades_activas = [
            k for k, v in endpoints_map.items() if len(v) > 0]

        respuesta_usuario = f"""🧠 AUTOPERCEPCIÓN ESTRUCTURAL COMPLETADA

📊 INVENTARIO DEL SISTEMA:
- Total de endpoints: {total_eps}
- Categorías activas: {', '.join(capacidades_activas)}

✅ CAPACIDADES CONFIRMADAS:
"""

        for cat, eps in endpoints_map.items():
            if len(eps) > 0:
                respuesta_usuario += f"\n• {cat.upper()}: {len(eps)} endpoints disponibles"
                for ep in eps[:2]:  # Mostrar primeros 2 de cada categoría
                    respuesta_usuario += f"\n  - {ep['method']} {ep['path']}"
                if len(eps) > 2:
                    respuesta_usuario += f"\n  ... y {len(eps)-2} más"

        respuesta_usuario += "\n\n🎯 PRÓXIMOS PASOS: Usar estos endpoints para validaciones específicas."

        resumen = {
            "exito": True,
            "respuesta_usuario": respuesta_usuario,
            "timestamp": datetime.now().isoformat(),
            "estructura": {
                "total_endpoints": total_eps,
                "categorias": {k: len(v) for k, v in endpoints_map.items()},
                "endpoints_por_categoria": endpoints_map
            },
            "capacidades": {
                "diagnostico": len(endpoints_map.get("diagnostico", [])) > 0,
                "monitoreo": len(endpoints_map.get("monitoreo", [])) > 0,
                "correccion": len(endpoints_map.get("correccion", [])) > 0,
                "memoria": len(endpoints_map.get("memoria", [])) > 0,
                "configuracion": len(endpoints_map.get("configuracion", [])) > 0
            },
            "mensaje": "Autopercepción estructural completada"
        }

        return func.HttpResponse(
            json.dumps(resumen, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error en introspection: {e}")
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "error": str(e)
            }, ensure_ascii=False),
            mimetype="application/json",
            status_code=500
        )
