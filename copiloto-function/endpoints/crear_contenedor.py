"""
Endpoint: /api/crear-contenedor
Crea cuentas de almacenamiento usando Azure SDK (sin dependencia de CLI)
"""
from function_app import app
import logging
import json
import os
import re
import sys
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Tuple
from uuid import uuid4
import azure.functions as func

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

if TYPE_CHECKING:
    from azure.core.polling import LROPoller
    from azure.mgmt.storage.models import StorageAccount
    from azure.mgmt.storage import StorageManagementClient
    from azure.identity import DefaultAzureCredential

StorageManagementClient: Any
DefaultAzureCredential: Any
HttpResponseError: Any

try:
    from azure.mgmt.storage import StorageManagementClient as _StorageManagementClient
    from azure.identity import DefaultAzureCredential as _DefaultAzureCredential
    from azure.core.exceptions import HttpResponseError as _HttpResponseError
    StorageManagementClient = _StorageManagementClient
    DefaultAzureCredential = _DefaultAzureCredential
    HttpResponseError = _HttpResponseError
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    StorageManagementClient = None
    DefaultAzureCredential = None

    class _HttpResponseErrorPlaceholder(Exception):
        """Placeholder para mantener compatibilidad cuando el SDK no está instalado."""
        pass

    HttpResponseError = _HttpResponseErrorPlaceholder
    logging.warning("Azure Storage SDK no disponible")

_storage_clients: Dict[str, Any] = {}


def _get_storage_client(subscription_id: str) -> Any:
    client = _storage_clients.get(subscription_id)
    if client is None:
        credential = DefaultAzureCredential()
        client = StorageManagementClient(credential, subscription_id)
        _storage_clients[subscription_id] = client
    return client


def _normalizar_nombre(nombre: str) -> Tuple[str, Dict[str, Any]]:
    """Normaliza el nombre de la cuenta respetando las reglas de Azure Storage."""
    valor = (nombre or "").lower()
    detalles: Dict[str, Any] = {
        "original": nombre,
        "ajustes": [],
        "normalizado": valor
    }

    if valor != nombre:
        detalles["ajustes"].append("Se convirtió todo a minúsculas.")

    limpio = re.sub(r"[^a-z0-9]", "", valor)
    if limpio != valor:
        detalles["ajustes"].append(
            "Se eliminaron caracteres no permitidos (solo a-z, 0-9).")

    if len(limpio) > 24:
        detalles["ajustes"].append("Se truncó el nombre a 24 caracteres.")
        limpio = limpio[:24]

    if 0 < len(limpio) < 3:
        faltante = 3 - len(limpio)
        sufijo = uuid4().hex[:faltante]
        limpio = f"{limpio}{sufijo}"
        detalles["ajustes"].append(
            "Se completó hasta 3 caracteres agregando un sufijo aleatorio.")

    if not limpio:
        detalles["ajustes"].append(
            "No se pudo normalizar; proporcione letras o números.")

    detalles["normalizado"] = limpio
    return limpio, detalles


@app.function_name(name="crear_contenedor_http")
@app.route(route="crear-contenedor", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def crear_contenedor_http(req: func.HttpRequest) -> func.HttpResponse:
    from memory_manual import aplicar_memoria_manual
    from cosmos_memory_direct import consultar_memoria_cosmos_directo, aplicar_memoria_cosmos_directo
    from services.memory_service import memory_service

    normalizacion_detalles: Dict[str, Any] = {}

    # 🧠 CONSULTAR MEMORIA COSMOS DB DIRECTAMENTE
    memoria_previa = consultar_memoria_cosmos_directo(req)
    if memoria_previa and memoria_previa.get("tiene_historial"):
        logging.info(
            f"🧠 Crear-contenedor: {memoria_previa['total_interacciones']} interacciones encontradas")

    """Crea una cuenta de almacenamiento usando Azure SDK"""
    try:
        if not SDK_AVAILABLE:
            res = {
                "exito": False,
                "mensaje": "Azure Storage SDK no está instalado en la función.",
                "sugerencias": [
                    "Ejecuta 'pip install azure-mgmt-storage azure-identity' y vuelve a desplegar.",
                    "Verifica que los paquetes estén presentes en requirements.txt."
                ]
            }
            res = aplicar_memoria_cosmos_directo(req, res)
            res = aplicar_memoria_manual(req, res)
            return func.HttpResponse(
                json.dumps(res, ensure_ascii=False),
                mimetype="application/json",
                status_code=200
            )

        # Obtener parámetros
        try:
            body = req.get_json()
        except ValueError:
            res = {
                "exito": False,
                "mensaje": "Cuerpo JSON inválido.",
                "ejemplo": {
                    "nombre": "test-storage-validacion",
                    "location": "eastus",
                    "sku": "Standard_LRS",
                    "kind": "StorageV2"
                },
                "sugerencias": ["Envía un JSON válido en el cuerpo."]
            }
            res = aplicar_memoria_cosmos_directo(req, res)
            res = aplicar_memoria_manual(req, res)
            return func.HttpResponse(
                json.dumps(res, ensure_ascii=False),
                mimetype="application/json",
                status_code=200
            )

        if not isinstance(body, dict):
            res = {
                "exito": False,
                "mensaje": "El cuerpo debe ser un objeto JSON.",
                "ejemplo": {
                    "nombre": "test-storage-validacion",
                    "location": "eastus",
                    "sku": "Standard_LRS",
                    "kind": "StorageV2"
                },
                "sugerencias": ["Envía un objeto JSON (clave/valor) en lugar de un arreglo o texto plano."]
            }
            res = aplicar_memoria_cosmos_directo(req, res)
            res = aplicar_memoria_manual(req, res)
            return func.HttpResponse(
                json.dumps(res, ensure_ascii=False),
                mimetype="application/json",
                status_code=200
            )

        nombre_original = str(body.get("nombre") or "").strip()
        if not nombre_original:
            res = {
                "exito": False,
                "mensaje": "Parámetro 'nombre' es requerido.",
                "sugerencias": [
                    "Incluye la propiedad 'nombre' en el cuerpo JSON con el identificador deseado.",
                    "Ejemplo: {'nombre': 'teststorage01', 'location': 'eastus'}"
                ]
            }
            res = aplicar_memoria_cosmos_directo(req, res)
            res = aplicar_memoria_manual(req, res)
            return func.HttpResponse(
                json.dumps(res, ensure_ascii=False),
                mimetype="application/json",
                status_code=200
            )

        nombre, normalizacion_detalles = _normalizar_nombre(nombre_original)
        if not nombre:
            res = {
                "exito": False,
                "mensaje": "No se pudo normalizar el nombre proporcionado.",
                "normalizacion": normalizacion_detalles,
                "sugerencias": [
                    "Usa solo letras minúsculas y números.",
                    "Asegúrate de que el nombre tenga entre 3 y 24 caracteres."
                ]
            }
            res = aplicar_memoria_cosmos_directo(req, res)
            res = aplicar_memoria_manual(req, res)
            return func.HttpResponse(
                json.dumps(res, ensure_ascii=False),
                mimetype="application/json",
                status_code=200
            )

        location = (body.get("location") or body.get(
            "ubicacion") or "eastus").strip()
        sku = (body.get("sku") or "Standard_LRS").strip()
        kind = (body.get("kind") or "StorageV2").strip()
        resource_group = (body.get("resource_group") or body.get("resourceGroup") or
                          os.environ.get("RESOURCE_GROUP", "boat-rental-app-group")).strip()
        subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")

        if not subscription_id:
            res = {
                "exito": False,
                "mensaje": "AZURE_SUBSCRIPTION_ID no está configurado en la aplicación.",
                "sugerencias": [
                    "Configura la variable de aplicación AZURE_SUBSCRIPTION_ID en Azure Functions.",
                    "Verifica que la identidad administrada tenga permisos sobre la suscripción."
                ]
            }
            res = aplicar_memoria_cosmos_directo(req, res)
            res = aplicar_memoria_manual(req, res)
            return func.HttpResponse(
                json.dumps(res, ensure_ascii=False),
                mimetype="application/json",
                status_code=200
            )

        # Crear cliente de Storage Management
        storage_client = _get_storage_client(subscription_id)

        # Crear parámetros usando diccionario (compatible con todas las versiones)
        parameters: Any = {
            "sku": {"name": sku},
            "kind": kind,
            "location": location,
            "tags": {
                "proyecto": "boat-rental-app",
                "creado_por": "copiloto-function",
                "fecha_creacion": datetime.now().isoformat(),
                "nombre_original": nombre_original
            }
        }

        logging.info(f"🔧 Creando cuenta: {nombre} en {resource_group}")

        # Crear cuenta (operación asíncrona)
        poller: "LROPoller[StorageAccount]" = storage_client.storage_accounts.begin_create(
            resource_group_name=resource_group,
            account_name=nombre,
            parameters=parameters
        )

        # Esperar resultado
        account: "StorageAccount" = poller.result(timeout=120)

        logging.info(f"✅ Cuenta creada: {account.name}")

        res = {
            "exito": True,
            "mensaje": f"Cuenta de almacenamiento '{nombre}' creada exitosamente",
            "cuenta": {
                "nombre": getattr(account, 'name', nombre),
                "id": getattr(account, 'id', ''),
                "location": getattr(account, 'location', location),
                "sku": getattr(getattr(account, 'sku', None), 'name', sku) if hasattr(account, 'sku') else sku,
                "kind": getattr(account, 'kind', kind),
                "resource_group": resource_group,
                "estado": getattr(account, 'provisioning_state', 'Unknown'),
                "primary_endpoints": {
                    "blob": getattr(getattr(account, 'primary_endpoints', None), 'blob', None) if hasattr(account, 'primary_endpoints') else None,
                    "file": getattr(getattr(account, 'primary_endpoints', None), 'file', None) if hasattr(account, 'primary_endpoints') else None
                }
            },
            "metadata": {
                "metodo": "azure_sdk",
                "timestamp": datetime.now().isoformat()
            }
        }

        res = aplicar_memoria_cosmos_directo(req, res)
        res = aplicar_memoria_manual(req, res)

        memory_service.registrar_llamada(
            source="crear_contenedor",
            endpoint="/api/crear-contenedor",
            method=req.method,
            params={"session_id": req.headers.get(
                "Session-ID"), "agent_id": req.headers.get("Agent-ID")},
            response_data=res,
            success=True
        )

        return func.HttpResponse(
            json.dumps(res, ensure_ascii=False),
            mimetype="application/json",
            status_code=201
        )

    except HttpResponseError as exc:
        logging.error(f'❌ Error creando cuenta (Azure): {exc}')

        origen_status = exc.status_code or 500
        error_code = getattr(exc.error, 'code', None) if getattr(
            exc, 'error', None) else None
        mensaje = getattr(exc, 'message', str(exc))

        sugerencias = []
        if error_code in {"StorageAccountAlreadyTaken", "StorageAccountAlreadyExists", "AccountNameAlreadyExists"}:
            sugerencias.append(
                'El nombre ya existe en Azure. Prueba con otro o añade un sufijo numérico.')
        elif error_code in {"AuthorizationFailed", "AuthorizationRequestDenied"}:
            sugerencias.append(
                "Verifica que la identidad usada tenga el rol 'Storage Account Contributor'.")
        elif error_code in {"InvalidAccountName", "AccountNameInvalid"}:
            sugerencias.append(
                'Nombre debe tener 3-24 caracteres, solo minúsculas y números. Revisa la normalización sugerida.')
            if normalizacion_detalles.get('normalizado'):
                sugerencias.append(
                    f"Sugerencia automática: usa '{normalizacion_detalles['normalizado']}' o añade un sufijo numérico.")
        elif origen_status == 429:
            sugerencias.append(
                'Azure devolvió 429. Espera unos segundos e inténtalo de nuevo.')
        else:
            sugerencias.append(
                'Consulta Application Insights para obtener más detalles del error.')

        res = {
            'exito': False,
            'mensaje': 'Azure rechazó la creación de la cuenta.',
            'detalle': mensaje,
            'codigo': error_code,
            'codigo_http_origen': origen_status,
            'normalizacion': normalizacion_detalles,
            'sugerencias': sugerencias
        }

        res = aplicar_memoria_cosmos_directo(req, res)
        res = aplicar_memoria_manual(req, res)

        memory_service.registrar_llamada(
            source='crear_contenedor',
            endpoint='/api/crear-contenedor',
            method=req.method,
            params={'session_id': req.headers.get(
                'Session-ID'), 'agent_id': req.headers.get('Agent-ID')},
            response_data=res,
            success=False
        )

        return func.HttpResponse(
            json.dumps(res, ensure_ascii=False),
            mimetype='application/json',
            status_code=200
        )
    except Exception as e:
        logging.error(f'❌ Error creando cuenta: {e}')

        error_msg = str(e)
        sugerencias = []

        lowered = error_msg.lower()
        if 'already exists' in lowered:
            sugerencias.append(
                'El nombre ya existe. Usa un nombre distinto o añade un sufijo numérico.')
        elif 'invalid' in lowered and 'name' in lowered:
            sugerencias.append(
                'Nombre debe tener 3-24 caracteres, solo minúsculas y números.')
        elif 'permission' in lowered or 'authorization' in lowered:
            sugerencias.append(
                "Verifica que la identidad tenga el rol 'Storage Account Contributor'.")
        else:
            sugerencias.append(
                'Revisa Application Insights para más detalles del error.')

        res = {
            'exito': False,
            'mensaje': 'Ocurrió un error no controlado durante la creación.',
            'detalle': error_msg,
            'tipo_error': type(e).__name__,
            'normalizacion': normalizacion_detalles,
            'sugerencias': sugerencias
        }

        res = aplicar_memoria_cosmos_directo(req, res)
        res = aplicar_memoria_manual(req, res)

        memory_service.registrar_llamada(
            source='crear_contenedor',
            endpoint='/api/crear-contenedor',
            method=req.method,
            params={'session_id': req.headers.get(
                'Session-ID'), 'agent_id': req.headers.get('Agent-ID')},
            response_data=res,
            success=False
        )

        return func.HttpResponse(
            json.dumps(res, ensure_ascii=False),
            mimetype='application/json',
            status_code=200
        )
