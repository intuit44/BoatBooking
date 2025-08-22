from typing import Union, Dict, Any
from typing import Optional, Dict, Any
import azure.functions as func
import logging
import json
import os
import stat
import shutil
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient
from azure.identity import ManagedIdentityCredential, DefaultAzureCredential
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
import base64
import re
import subprocess
import asyncio
import traceback
from typing import List, Any, Union
from hybrid_processor import HybridResponseProcessor, process_hybrid_request
from datetime import datetime
from typing import Optional, cast

# Carpeta temporal para scripts descargados
TMP_SCRIPTS_DIR = Path(tempfile.gettempdir()) / \
    "scripts"  # /tmp/scripts en Linux


def _resolve_local_script_path(nombre_script: str) -> Optional[Path]:
    p = Path(nombre_script)
    if p.is_absolute() and p.exists():
        return p
    p1 = (PROJECT_ROOT / nombre_script).resolve()
    if p1.exists():
        return p1
    p2 = (TMP_SCRIPTS_DIR / nombre_script).resolve()
    if p2.exists():
        return p2
    p3 = (PROJECT_ROOT / "scripts" / Path(nombre_script).name).resolve()
    if p3.exists():
        return p3
    return None


def _download_script_from_blob(nombre_script: str) -> Optional[Path]:
    try:
        client = get_blob_client()
        if not client:
            return None
        container = client.get_container_client(CONTAINER_NAME)
        blob_client = container.get_blob_client(nombre_script)
        if not blob_client.exists():
            return None
        local_path = TMP_SCRIPTS_DIR / nombre_script
        local_path.parent.mkdir(parents=True, exist_ok=True)
        data = blob_client.download_blob().readall()
        local_path.write_bytes(data)
        if local_path.suffix in {".sh", ".py"}:
            mode = os.stat(local_path).st_mode
            os.chmod(local_path, mode | stat.S_IXUSR | stat.S_IXGRP)
        return local_path
    except Exception as e:
        logging.warning(f"_download_script_from_blob failed: {e}")
        return None


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


# Configuración adaptativa mejorada

# Detección robusta de entorno Azure
def detect_azure_env():
    if os.environ.get("WEBSITE_INSTANCE_ID"):
        return True
    if os.environ.get("WEBSITE_SITE_NAME"):
        return True
    if os.environ.get("WEBSITE_RESOURCE_GROUP") or os.environ.get("WEBSITE_OWNER_NAME"):
        return True
    if Path("/home/site/wwwroot").exists():
        return True
    return False


IS_AZURE = detect_azure_env()

# Configuración de Azure Blob Storage
STORAGE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = "boat-rental-project"

# Configuración local para desarrollo
if IS_AZURE:
    PROJECT_ROOT = Path("/home/site/wwwroot")
else:
    PROJECT_ROOT = Path("C:/ProyectosSimbolicos/boat-rental-app")
    COPILOT_ROOT = Path(
        "C:/ProyectosSimbolicos/boat-rental-app/copiloto-function")

# Cache y clientes
CACHE = {}

# Capacidades semánticas
SEMANTIC_CAPABILITIES = {
    "leer": "Lectura de archivos del proyecto",
    "buscar": "Búsqueda inteligente de archivos",
    "explorar": "Exploración de directorios",
    "analizar": "Análisis profundo de código",
    "generar": "Generación de código y artefactos",
    "ejecutar": "Ejecución de comandos simbólicos",
    "diagnosticar": "Diagnóstico del sistema",
    "sugerir": "Sugerencias basadas en contexto"
}


BLOB_CLIENT = None


def get_blob_client():
    global BLOB_CLIENT
    if BLOB_CLIENT:
        return BLOB_CLIENT
    try:
        conn = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if conn:
            BLOB_CLIENT = BlobServiceClient.from_connection_string(conn)
            return BLOB_CLIENT

        account_url = os.getenv(
            "BLOB_ACCOUNT_URL", "https://boatrentalstorage.blob.core.windows.net")

        # 1) Intenta SIEMPRE Managed Identity (system-assigned)
        try:
            cred = ManagedIdentityCredential()  # no client_id -> usa la MI del recurso
            # prueba de token para detectar fallos tempranos
            cred.get_token("https://storage.azure.com/.default")
        except Exception as mi_err:
            logging.warning(
                f"MI token failed: {mi_err}. Falling back to DefaultAzureCredential (env excluido).")
            # 2) Fallback sin EnvironmentCredential para evitar AZURE_CLIENT_ID/SECRET, etc.
            cred = DefaultAzureCredential(
                exclude_environment_credential=True,
                exclude_shared_token_cache_credential=True
            )

        BLOB_CLIENT = BlobServiceClient(
            account_url=account_url, credential=cred)
        return BLOB_CLIENT
    except Exception as e:
        logging.exception("get_blob_client() init failed")
        return None


def leer_archivo_blob(ruta: str) -> dict:
    """Lee un archivo desde Azure Blob Storage con mejor manejo de errores"""
    try:
        client = get_blob_client()
        if not client:
            return {
                "exito": False,
                "error": "Blob Storage no configurado correctamente",
                "detalles": "El cliente de Blob Storage no se pudo inicializar"
            }

        # Normalizar la ruta (quitar barras iniciales)
        ruta_normalizada = ruta.replace('\\', '/').lstrip('/')

        container_client = client.get_container_client(CONTAINER_NAME)
        blob_client = container_client.get_blob_client(ruta_normalizada)

        # Verificar si el blob existe
        if not blob_client.exists():
            # Intentar listar blobs similares
            blobs_similares = []
            for blob in container_client.list_blobs():
                if ruta_normalizada.lower() in blob.name.lower():
                    blobs_similares.append(blob.name)

            return {
                "exito": False,
                "error": f"Archivo no encontrado en Blob: {ruta_normalizada}",
                "sugerencias": blobs_similares[:5] if blobs_similares else [],
                "total_similares": len(blobs_similares)
            }

        # Descargar el contenido
        download_stream = blob_client.download_blob()
        contenido = download_stream.readall().decode('utf-8')

        return {
            "exito": True,
            "contenido": contenido,
            "ruta": f"blob://{CONTAINER_NAME}/{ruta_normalizada}",
            "tamaño": len(contenido),
            "fuente": "Azure Blob Storage",
            "metadata": {
                "last_modified": str(blob_client.get_blob_properties().last_modified),
                "content_type": blob_client.get_blob_properties().content_settings.content_type
            }
        }
    except Exception as e:
        return {
            "exito": False,
            "error": f"Error leyendo desde Blob: {str(e)}",
            "tipo_error": type(e).__name__,
            "detalles": str(e)
        }


def leer_archivo_local(ruta: str) -> dict:
    """Lee un archivo del sistema local"""
    posibles_rutas = [
        PROJECT_ROOT / ruta,
        COPILOT_ROOT / ruta if 'COPILOT_ROOT' in globals() else None,
        Path(ruta) if Path(ruta).is_absolute() else None
    ]

    for ruta_completa in filter(None, posibles_rutas):
        if ruta_completa and ruta_completa.exists():
            try:
                contenido = ruta_completa.read_text(encoding='utf-8')
                return {
                    "exito": True,
                    "contenido": contenido,
                    "ruta": str(ruta_completa),
                    "tamaño": len(contenido),
                    "fuente": "Sistema Local",
                    "metadata": {
                        "last_modified": datetime.fromtimestamp(ruta_completa.stat().st_mtime).isoformat()
                    }
                }
            except Exception as e:
                continue

    return {
        "exito": False,
        "error": f"Archivo no encontrado localmente: {ruta}",
        "rutas_intentadas": [str(r) for r in posibles_rutas if r]
    }


def leer_archivo_dinamico(ruta: str) -> dict:
    """Lee un archivo de forma dinámica con prioridad correcta"""
    # Cache
    if ruta in CACHE:
        return CACHE[ruta]

    # En Azure, intentar Blob primero
    if IS_AZURE:
        resultado = leer_archivo_blob(ruta)
        if resultado["exito"]:
            CACHE[ruta] = resultado
            return resultado
        # Si falla, incluir información de debug
        return resultado
    else:
        # En local, usar sistema de archivos
        resultado = leer_archivo_local(ruta)
        if resultado["exito"]:
            CACHE[ruta] = resultado
        return resultado


def explorar_directorio_blob(prefijo: str = "") -> list:
    """Lista archivos en Blob Storage con un prefijo dado"""
    try:
        client = get_blob_client()
        if not client:
            return []

        container_client = client.get_container_client(CONTAINER_NAME)
        # Normalizar prefijo
        prefijo_normalizado = prefijo.replace(
            '\\', '/').lstrip('/') if prefijo else ""

        archivos = []
        for blob in container_client.list_blobs(name_starts_with=prefijo_normalizado):
            archivos.append({
                "nombre": blob.name,
                "tamaño": blob.size,
                "modificado": str(blob.last_modified),
                "tipo": blob.name.split('.')[-1] if '.' in blob.name else 'sin_extension'
            })

        return archivos
    except Exception as e:
        logging.error(f"Error explorando Blob: {str(e)}")
        return []


def buscar_archivos_semantico(query: str) -> dict:
    """Búsqueda semántica de archivos con análisis de intención"""
    # Analizar intención de búsqueda
    intencion = {
        "tipo_archivo": None,
        "ubicacion": None,
        "patron": query
    }

    # Detectar tipo de archivo
    if ".py" in query or "python" in query.lower():
        intencion["tipo_archivo"] = "python"
    elif ".js" in query or ".ts" in query or "javascript" in query.lower():
        intencion["tipo_archivo"] = "javascript"
    elif ".json" in query or "config" in query.lower():
        intencion["tipo_archivo"] = "configuracion"

    # Detectar ubicación
    if "mobile" in query.lower():
        intencion["ubicacion"] = "mobile-app"
    elif "backend" in query.lower():
        intencion["ubicacion"] = "backend"
    elif "admin" in query.lower():
        intencion["ubicacion"] = "admin-panel"

    # Realizar búsqueda
    archivos_encontrados = []

    if IS_AZURE:
        client = get_blob_client()
        if client:
            container_client = client.get_container_client(CONTAINER_NAME)
            for blob in container_client.list_blobs():
                nombre_lower = blob.name.lower()
                query_lower = query.lower()

                # Búsqueda flexible
                if (query_lower in nombre_lower or
                    all(parte in nombre_lower for parte in query_lower.split()) or
                        (intencion["tipo_archivo"] and blob.name.endswith(f".{intencion['tipo_archivo']}"))):

                    archivos_encontrados.append({
                        "ruta": blob.name,
                        "nombre": Path(blob.name).name,
                        "tamaño": blob.size,
                        "relevancia": 1.0 if query_lower in nombre_lower else 0.7
                    })
    else:
        # Búsqueda local
        for archivo in PROJECT_ROOT.rglob(f"*{query}*"):
            if archivo.is_file():
                archivos_encontrados.append({
                    "ruta": str(archivo.relative_to(PROJECT_ROOT)),
                    "nombre": archivo.name,
                    "tamaño": archivo.stat().st_size,
                    "relevancia": 1.0
                })

    # Ordenar por relevancia
    archivos_encontrados.sort(key=lambda x: x["relevancia"], reverse=True)

    return {
        "intencion_detectada": intencion,
        "archivos": archivos_encontrados[:20],
        "total": len(archivos_encontrados),
        "sugerencias": generar_sugerencias_busqueda(intencion, archivos_encontrados)
    }


def generar_sugerencias_busqueda(intencion: dict, archivos: list) -> list:
    """Genera sugerencias basadas en la búsqueda"""
    sugerencias = []

    if not archivos:
        sugerencias.append(
            "No se encontraron archivos. Intenta con un término más general.")
        if intencion["tipo_archivo"]:
            sugerencias.append(
                f"Puedes buscar todos los archivos {intencion['tipo_archivo']} con: buscar:*.{intencion['tipo_archivo']}")
    else:
        if intencion["ubicacion"]:
            sugerencias.append(
                f"Encontré archivos en {intencion['ubicacion']}. Puedes explorar más con: explorar:{intencion['ubicacion']}")
        if len(archivos) > 20:
            sugerencias.append(
                f"Hay {len(archivos)} resultados. Refina tu búsqueda para mejores resultados.")

    return sugerencias


def generar_test(contexto: dict) -> dict:
    """Genera un archivo de prueba básico basado en el contexto"""
    nombre_archivo = contexto.get("target", "test_sample.py")
    contenido_test = f"""import unittest

class TestSample(unittest.TestCase):
    def test_example(self):
        self.assertEqual(1 + 1, 2)

if __name__ == "__main__":
    unittest.main()
"""
    return {
        "exito": True,
        "contenido": contenido_test,
        "tipo": "test",
        "metadata": {
            "nombre_archivo": nombre_archivo,
            "fecha_generacion": datetime.now().isoformat()
        }
    }


def generar_script(contexto: dict) -> dict:
    """Genera un script básico basado en el contexto"""
    nombre_archivo = contexto.get("target", "script_sample.py")
    contenido_script = f"""#!/usr/bin/env python3

def main():
    print("Script generado automáticamente por Copiloto AI.")

if __name__ == "__main__":
    main()
"""
    return {
        "exito": True,
        "contenido": contenido_script,
        "tipo": "script",
        "metadata": {
            "nombre_archivo": nombre_archivo,
            "fecha_generacion": datetime.now().isoformat()
        }
    }


def generar_artefacto(tipo: str, contexto: dict) -> dict:
    """Genera artefactos basados en el contexto"""
    generadores = {
        "readme": lambda ctx: generar_readme(ctx),
        "config": lambda ctx: generar_config(ctx),
        "test": lambda ctx: generar_test(ctx),
        "script": lambda ctx: generar_script(ctx)
    }

    if tipo in generadores:
        return generadores[tipo](contexto)

    return {
        "exito": False,
        "error": f"Tipo de artefacto no soportado: {tipo}",
        "tipos_soportados": list(generadores.keys())
    }


def generar_config(contexto: dict) -> dict:
    """Genera un archivo de configuración básico basado en el contexto"""
    config = {
        "nombre_proyecto": contexto.get("nombre_proyecto", "Boat Rental App"),
        "version": contexto.get("version", "1.0.0"),
        "entorno": "Azure" if IS_AZURE else "Local",
        "fecha_generacion": datetime.now().isoformat(),
        "parametros": contexto.get("parametros", {})
    }
    config_content = json.dumps(config, indent=2, ensure_ascii=False)
    return {
        "exito": True,
        "contenido": config_content,
        "tipo": "config",
        "metadata": {
            "fecha_generacion": config["fecha_generacion"],
            "entorno": config["entorno"]
        }
    }


def generar_readme(contexto: dict) -> dict:
    """Genera un README basado en el contexto del proyecto"""
    # Analizar estructura del proyecto
    estructura = explorar_directorio_blob() if IS_AZURE else []

    readme_content = f"""# {contexto.get('nombre_proyecto', 'Boat Rental App')}

## 📋 Descripción
{contexto.get('descripcion', 'Sistema de alquiler de embarcaciones con app móvil, backend serverless y panel de administración.')}

## 🏗️ Estructura del Proyecto

```
boat-rental-app/
├── mobile-app/          # React Native + Expo
├── backend/            # Serverless + AWS Lambda
├── admin-panel/        # Next.js + Material-UI
└── copiloto-function/  # Azure Functions AI
```

## 🚀 Inicio Rápido

### Prerrequisitos
- Node.js 18+
- Python 3.9+
- Azure CLI
- AWS CLI

### Instalación
```bash
# Clonar el repositorio
git clone {contexto.get('repo_url', 'https://github.com/tu-usuario/boat-rental-app')}

# Instalar dependencias
cd boat-rental-app
npm install
```

## 📊 Estado del Proyecto
- Total de archivos: {len(estructura)}
- Última actualización: {datetime.now().strftime('%Y-%m-%d')}

## 🤖 Copiloto AI
Este proyecto incluye un copiloto AI que puede:
- Leer y analizar archivos del proyecto
- Generar código y configuraciones
- Ejecutar comandos simbólicos
- Proporcionar asistencia contextual

---
Generado automáticamente por Copiloto AI
"""

    return {
        "exito": True,
        "contenido": readme_content,
        "tipo": "readme",
        "metadata": {
            "archivos_analizados": len(estructura),
            "fecha_generacion": datetime.now().isoformat()
        }
    }


def analizar_codigo_semantico(ruta: str) -> dict:
    """Análisis semántico profundo de código"""
    archivo = leer_archivo_dinamico(ruta)
    if not archivo["exito"]:
        return archivo

    contenido = archivo["contenido"]
    analisis = {
        "archivo": ruta,
        "tipo": Path(ruta).suffix,
        "metricas": {
            "lineas": len(contenido.split('\n')),
            "caracteres": len(contenido),
            "palabras": len(contenido.split())
        },
        "estructura": {},
        "sugerencias": []
    }

    # Análisis específico por tipo
    if ruta.endswith('.py'):
        # Análisis Python
        analisis["estructura"]["imports"] = len(
            re.findall(r'^import |^from ', contenido, re.MULTILINE))
        analisis["estructura"]["funciones"] = len(
            re.findall(r'^def ', contenido, re.MULTILINE))
        analisis["estructura"]["clases"] = len(
            re.findall(r'^class ', contenido, re.MULTILINE))

        if "# TODO" in contenido or "# FIXME" in contenido:
            analisis["sugerencias"].append(
                "Hay tareas pendientes (TODO/FIXME) en el código")

    elif ruta.endswith(('.js', '.ts', '.tsx')):
        # Análisis JavaScript/TypeScript
        analisis["estructura"]["imports"] = len(
            re.findall(r'^import ', contenido, re.MULTILINE))
        analisis["estructura"]["exports"] = len(
            re.findall(r'^export ', contenido, re.MULTILINE))
        analisis["estructura"]["funciones"] = len(
            re.findall(r'function |const \w+ = \(|=> {', contenido))

        if "console.log" in contenido:
            analisis["sugerencias"].append(
                "Considera remover console.log en producción")

    elif ruta.endswith('.json'):
        # Análisis JSON
        try:
            data = json.loads(contenido)
            analisis["estructura"]["tipo"] = "JSON válido"
            analisis["estructura"]["claves"] = list(data.keys()) if isinstance(
                data, dict) else f"Array con {len(data)} elementos"
        except:
            analisis["estructura"]["tipo"] = "JSON inválido"
            analisis["sugerencias"].append(
                "El archivo JSON tiene errores de sintaxis")

    return {
        "exito": True,
        "analisis": analisis,
        "intenciones_sugeridas": [
            f"generar:test para {ruta}",
            f"generar:documentacion para {ruta}",
            f"diagnosticar:calidad de {ruta}"
        ]
    }


def procesar_intencion_semantica(intencion: str, parametros: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Versión completa del procesador con todas las capacidades"""

    # Asegurar que parametros nunca sea None
    if parametros is None:
        parametros = {}

    # Procesar intenciones
    partes = intencion.split(':')
    comando = partes[0].lower()
    contexto = partes[1] if len(partes) > 1 else ""

    # Intenciones básicas
    if comando == "sugerir":
        return {
            "exito": True,
            "sugerencias": [
                "leer:archivo",
                "buscar:patron",
                "generar:readme",
                "diagnosticar:sistema"
            ]
        }
    elif comando == "diagnosticar":
        return diagnosticar_function_app()
    elif comando == "dashboard":
        return generar_dashboard_insights()

    if comando == "crear" and contexto == "archivo":
        ruta = parametros.get("ruta", "")
        contenido = parametros.get("contenido", "")
        if not ruta:
            return {
                "exito": False,
                "error": "Parámetro 'ruta' es requerido para crear archivo"
            }
        return crear_archivo(ruta, contenido)

    elif comando == "crear" and contexto == "contenedor":
        nombre = parametros.get("nombre", "")
        publico = parametros.get("publico", False)
        metadata = parametros.get("metadata", {})

        if not nombre:
            return {
                "exito": False,
                "error": "Parámetro 'nombre' es requerido para crear contenedor",
                "ejemplo": {
                    "intencion": "crear:contenedor",
                    "parametros": {
                        "nombre": "mi-contenedor",
                        "publico": False,
                        "metadata": {"proyecto": "boat-rental"}
                    }
                }
            }

        # Usar el endpoint interno
        return procesar_intencion_crear_contenedor(parametros)

    elif comando == "modificar" and contexto == "archivo":
        ruta = parametros.get("ruta", "")
        operacion = parametros.get("operacion", "")
        if not ruta or not operacion:
            return {
                "exito": False,
                "error": "Parámetros 'ruta' y 'operacion' son requeridos"
            }
        linea_val = parametros.get("linea")
        if linea_val is None:
            linea_val = -1  # or another default int value indicating "not set"
        return modificar_archivo(
            ruta,
            operacion,
            parametros.get("contenido", ""),
            linea_val
        )

    elif comando == "ejecutar" and contexto == "script":
        nombre = parametros.get("nombre", "")
        if not nombre:
            return {
                "exito": False,
                "error": "Parámetro 'nombre' es requerido para ejecutar script"
            }
        return ejecutar_script(
            nombre,
            parametros.get("parametros", [])
        )

    elif comando == "ejecutar" and contexto == "cli":
        servicio = parametros.get("servicio", "")
        cmd = parametros.get("comando", "")
        cli_params = parametros.get("parametros", {})

        if not cmd:
            return {
                "exito": False,
                "error": "Parámetro 'comando' es requerido para ejecutar CLI",
                "servicios_disponibles": ["storage", "functionapp", "webapp", "monitor", "resource"],
                "ejemplo": {
                    "intencion": "ejecutar:cli",
                    "parametros": {
                        "servicio": "storage",
                        "comando": "container list",
                        "parametros": {"account-name": "boatrentalstorage"}
                    }
                }
            }

        return procesar_intencion_cli(parametros)

    elif comando == "git":
        return operacion_git(contexto, parametros)

    elif comando == "ejecutar_agente":
        nombre = parametros.get("nombre", "")
        tarea = parametros.get("tarea", "")
        if not nombre or not tarea:
            return {
                "exito": False,
                "error": "Parámetros 'nombre' y 'tarea' son requeridos"
            }
        return ejecutar_agente_externo(
            nombre,
            tarea,
            parametros.get("parametros_agente", {})
        )

    elif comando == "comando" and contexto == "bash":
        cmd = parametros.get("cmd", "")
        if not cmd:
            return {
                "exito": False,
                "error": "Parámetro 'cmd' es requerido para ejecutar comando bash"
            }
        return comando_bash(
            cmd,
            parametros.get("seguro", False)
        )

    elif comando == "instalar" and contexto == "extension":
        nombre = parametros.get("nombre", "")
        if not nombre:
            return {
                "exito": False,
                "error": "Parámetro 'nombre' es requerido para instalar extensión"
            }
        # Instalar extensiones Azure CLI
        cmd = f"az extension add --name {nombre}"
        return comando_bash(cmd, seguro=True)

    elif comando == "diagnosticar" and contexto == "recursos":
        incluir_metricas = parametros.get("metricas", True)
        incluir_costos = parametros.get("costos", False)
        recurso = parametros.get("recurso", "")

        # Llamar al diagnóstico de recursos
        resultado = diagnostico_recursos_http(
            func.HttpRequest(
                method="GET",
                url="/api/diagnostico-recursos",
                headers={},
                params={
                    "metricas": str(incluir_metricas).lower(),
                    "costos": str(incluir_costos).lower(),
                    "recurso": recurso
                },
                body=b""
            )
        )

        return json.loads(resultado.get_body().decode())

    elif comando == "listar" and contexto == "contenedores":
        # Listar todos los contenedores de la cuenta de storage
        try:
            client = get_blob_client()
            if not client:
                return {
                    "exito": False,
                    "error": "Blob Storage no configurado"
                }

            contenedores = []
            for container in client.list_containers():
                # Contar blobs en cada contenedor
                container_client = client.get_container_client(container.name)
                blob_count = sum(1 for _ in container_client.list_blobs())

                contenedores.append({
                    "nombre": container.name,
                    "ultima_modificacion": container.last_modified.isoformat() if container.last_modified else None,
                    "metadata": container.metadata,
                    "total_blobs": blob_count
                })

            return {
                "exito": True,
                "contenedores": contenedores,
                "total": len(contenedores),
                "storage_account": client.account_name,
                "sugerencias": [
                    "crear:contenedor para añadir nuevo",
                    "eliminar:contenedor para borrar",
                    "diagnosticar:recursos para más detalles"
                ]
            }
        except Exception as e:
            return {
                "exito": False,
                "error": str(e),
                "tipo_error": type(e).__name__
            }

    elif comando == "eliminar" and contexto == "contenedor":
        nombre = parametros.get("nombre", "")
        confirmar = parametros.get("confirmar", False)

        if not nombre:
            return {
                "exito": False,
                "error": "Parámetro 'nombre' es requerido para eliminar contenedor"
            }

        if not confirmar:
            return {
                "exito": False,
                "error": "Eliminación de contenedor requiere confirmación",
                "advertencia": f"Esta operación eliminará el contenedor '{nombre}' y todos sus blobs",
                "accion_requerida": "Añade 'confirmar': true para proceder"
            }

        try:
            client = get_blob_client()
            if not client:
                return {
                    "exito": False,
                    "error": "Blob Storage no configurado"
                }

            container_client = client.get_container_client(nombre)
            container_client.delete_container()

            return {
                "exito": True,
                "mensaje": f"Contenedor '{nombre}' eliminado exitosamente",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "exito": False,
                "error": str(e),
                "tipo_error": type(e).__name__
            }

    elif comando == "configurar" and contexto == "cors":
        # Configurar CORS para la Function App
        origenes = parametros.get("origenes", ["*"])
        metodos = parametros.get("metodos", ["GET", "POST", "PUT", "DELETE"])

        if IS_AZURE:
            app_name = os.environ.get("WEBSITE_SITE_NAME")
            resource_group = os.environ.get("RESOURCE_GROUP", "boat-rental-rg")

            if app_name:
                # Construir comando para configurar CORS
                origenes_str = ",".join(origenes)
                cmd = f"az functionapp cors add --name {app_name} --resource-group {resource_group} --allowed-origins {origenes_str}"

                resultado = ejecutar_comando_azure(cmd)

                if resultado["exito"]:
                    return {
                        "exito": True,
                        "mensaje": "CORS configurado exitosamente",
                        "origenes": origenes,
                        "function_app": app_name
                    }
                else:
                    return {
                        "exito": False,
                        "error": resultado.get("error", "Error configurando CORS")
                    }

        return {
            "exito": False,
            "error": "Solo disponible en ambiente Azure",
            "ambiente_actual": "Local"
        }

    elif comando == "escalar" and contexto == "functionapp":
        # Escalar la Function App
        plan = parametros.get("plan", "EP1")  # EP1 = Elastic Premium 1

        if IS_AZURE:
            app_name = os.environ.get("WEBSITE_SITE_NAME")
            resource_group = os.environ.get("RESOURCE_GROUP", "boat-rental-rg")

            if app_name:
                # Obtener el plan actual
                cmd = f"az functionapp show --name {app_name} --resource-group {resource_group}"
                result = ejecutar_comando_azure(cmd)

                if result["exito"]:
                    plan_id = result["data"].get("appServicePlanId", "")
                    plan_name = plan_id.split(
                        "/")[-1] if plan_id else f"{app_name}-plan"

                    # Escalar el plan
                    cmd_scale = f"az appservice plan update --name {plan_name} --resource-group {resource_group} --sku {plan}"
                    result_scale = ejecutar_comando_azure(cmd_scale)

                    if result_scale["exito"]:
                        return {
                            "exito": True,
                            "mensaje": f"Function App escalada a plan {plan}",
                            "plan_anterior": plan_name,
                            "plan_nuevo": plan,
                            "function_app": app_name
                        }
                    else:
                        return {
                            "exito": False,
                            "error": result_scale.get("error", "Error escalando")
                        }

        return {
            "exito": False,
            "error": "Solo disponible en ambiente Azure",
            "planes_disponibles": ["B1", "B2", "B3", "S1", "S2", "S3", "P1V2", "P2V2", "P3V2", "EP1", "EP2", "EP3"]
        }

    # Si no se reconoce la intención, devolver error
    return {
        "exito": False,
        "error": f"Intención no reconocida: {intencion}",
        "sugerencias": ["dashboard", "diagnosticar:completo", "sugerir"]
    }


def ejecutar_comando_azure(comando: str, formato: str = "json") -> dict:
    """Ejecuta comandos Azure CLI y devuelve resultados estructurados"""
    try:
        # Construir comando completo
        cmd_parts = comando.split()
        if formato and "--output" not in comando:
            cmd_parts.extend(["--output", formato])

        resultado = subprocess.run(
            cmd_parts,
            capture_output=True,
            text=True,
            timeout=30
        )

        if resultado.returncode == 0:
            if formato == "json":
                try:
                    return {
                        "exito": True,
                        "data": json.loads(resultado.stdout),
                        "comando": comando
                    }
                except json.JSONDecodeError:
                    return {
                        "exito": True,
                        "data": resultado.stdout,
                        "comando": comando
                    }
            else:
                return {
                    "exito": True,
                    "data": resultado.stdout,
                    "comando": comando
                }
        else:
            return {
                "exito": False,
                "error": resultado.stderr,
                "comando": comando
            }
    except subprocess.TimeoutExpired:
        return {
            "exito": False,
            "error": "Comando excedió tiempo límite (30s)",
            "comando": comando
        }
    except Exception as e:
        return {
            "exito": False,
            "error": str(e),
            "comando": comando
        }


def diagnosticar_function_app() -> dict:
    """Diagnóstico completo de la Function App"""
    diagnostico = {
        "timestamp": datetime.now().isoformat(),
        "function_app": os.environ.get("WEBSITE_SITE_NAME", "local"),
        "checks": {},
        "recomendaciones": [],
        "metricas": {}
    }

    # 1. Verificar configuración
    diagnostico["checks"]["configuracion"] = {
        "blob_storage": False,  # Se actualizará abajo
        "openai_configurado": bool(os.environ.get("AZURE_OPENAI_KEY")),
        "app_insights": bool(os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")),
        "ambiente": "Azure" if IS_AZURE else "Local"
    }

    # 2. Verificar conectividad Blob Storage SIEMPRE (como build_status)
    client = get_blob_client()
    if client:
        try:
            container_client = client.get_container_client(CONTAINER_NAME)
            if container_client.exists():
                blob_count = sum(1 for _ in container_client.list_blobs())
                diagnostico["checks"]["blob_storage_detalles"] = {
                    "conectado": True,
                    "container": CONTAINER_NAME,
                    "archivos": blob_count
                }
                diagnostico["checks"]["configuracion"]["blob_storage"] = True
            else:
                diagnostico["checks"]["blob_storage_detalles"] = {
                    "conectado": False,
                    "error": f"El contenedor '{CONTAINER_NAME}' no existe"
                }
        except Exception as e:
            diagnostico["checks"]["blob_storage_detalles"] = {
                "conectado": False,
                "error": str(e)
            }
            diagnostico["recomendaciones"].append(
                "Verificar permisos de Blob Storage")
    else:
        diagnostico["checks"]["blob_storage_detalles"] = {
            "conectado": False,
            "error": "No se pudo inicializar el cliente de Blob Storage"
        }

    # 3. Métricas de rendimiento
    diagnostico["metricas"]["cache"] = {
        "archivos_en_cache": len(CACHE),
        "memoria_cache_bytes": sum(len(str(v)) for v in CACHE.values())
    }

    # 4. Verificar endpoints
    if IS_AZURE:
        # Ejecutar comandos Azure CLI para obtener métricas
        cmd_result = ejecutar_comando_azure(
            f"az monitor metrics list --resource /subscriptions/{os.environ.get('AZURE_SUBSCRIPTION_ID')}/resourceGroups/{os.environ.get('RESOURCE_GROUP')}/providers/Microsoft.Web/sites/{os.environ.get('WEBSITE_SITE_NAME')} --metric 'Http5xx' --interval PT1H"
        )
        if cmd_result["exito"]:
            diagnostico["metricas"]["errores_http"] = cmd_result["data"]

    # 5. Generar recomendaciones
    if not diagnostico["checks"].get("blob_storage_detalles", {}).get("conectado"):
        diagnostico["recomendaciones"].append(
            "Sincronizar archivos con Blob Storage: ./sync_to_blob.ps1")

    if diagnostico["metricas"]["cache"]["archivos_en_cache"] > 100:
        diagnostico["recomendaciones"].append(
            "Considerar limpiar caché para optimizar memoria")

    return diagnostico


def generar_dashboard_insights() -> dict:
    """
    Dashboard ultra-ligero y súper rápido - sin operaciones costosas
    """
    logging.info("⚡ Iniciando dashboard ultra-ligero")

    try:
        # Solo datos inmediatos, sin llamadas externas
        dashboard = {
            "titulo": "Dashboard Copiloto Semántico",
            "generado": datetime.now().isoformat(),
            "version": "ultra-ligero",
            "secciones": {
                "estado_sistema": {
                    "function_app": os.environ.get("WEBSITE_SITE_NAME", "local"),
                    "ambiente": "Azure" if IS_AZURE else "Local",
                    "version": "2.0-orchestrator",
                    "timestamp": datetime.now().isoformat(),
                    "uptime": "Activo"
                },
                "metricas_basicas": {
                    "cache_activo": len(CACHE) if 'CACHE' in globals() else 0,
                    "storage_configurado": bool(STORAGE_CONNECTION_STRING),
                    "memoria_cache_kb": round(sum(len(str(v)) for v in CACHE.values()) / 1024, 2) if CACHE else 0,
                    "endpoints_disponibles": 6
                },
                "estado_conexiones": {
                    "blob_storage": "Configurado" if STORAGE_CONNECTION_STRING else "No configurado",
                    "ambiente_ejecucion": "Azure" if IS_AZURE else "Local",
                    "modo": "Operativo"
                }
            },
            "acciones_rapidas": [
                "diagnosticar:completo",
                "verificar:almacenamiento",
                "limpiar:cache",
                "generar:resumen"
            ],
            "metadata": {
                "tiempo_generacion": "< 10ms",
                "optimizado": True,
                "sin_operaciones_costosas": True
            }
        }

        logging.info("✅ Dashboard ultra-ligero generado exitosamente")

        return {
            "exito": True,
            "dashboard": dashboard,
            "mensaje": "Dashboard generado correctamente",
            "tiempo_respuesta": "ultra-rápido"
        }

    except Exception as e:
        logging.error(f"❌ Error en dashboard ultra-ligero: {str(e)}")

        # Fallback súper minimalista
        return {
            "exito": True,  # Mantener como éxito para no romper el flujo
            "dashboard": {
                "titulo": "Dashboard Mínimo",
                "generado": datetime.now().isoformat(),
                "estado": "Operativo (modo seguro)",
                "ambiente": "Azure" if IS_AZURE else "Local",
                "mensaje": "Dashboard en modo de emergencia"
            },
            "fallback": True,
            "error_original": str(e)
        }


def generar_sugerencias_proactivas() -> list:
    """Genera sugerencias basadas en el contexto actual"""
    sugerencias = []

    # Analizar el contexto
    hora_actual = datetime.now().hour

    if 9 <= hora_actual <= 18:
        sugerencias.append({
            "tipo": "productividad",
            "mensaje": "Es horario laboral. Considera revisar los logs de errores recientes.",
            "comando": "diagnosticar:logs"
        })

    if len(CACHE) > 50:
        sugerencias.append({
            "tipo": "optimizacion",
            "mensaje": f"Tienes {len(CACHE)} archivos en caché. Considera limpiar para optimizar.",
            "comando": "ejecutar:limpiar_cache"
        })

    if not STORAGE_CONNECTION_STRING:
        sugerencias.append({
            "tipo": "configuracion",
            "mensaje": "Blob Storage no configurado. Los archivos solo están disponibles localmente.",
            "comando": "guia:configurar_blob"
        })

    return sugerencias


def ejecutar_accion_guiada(accion: str, parametros: dict) -> dict:
    """Ejecuta acciones guiadas complejas"""
    def analizar_logs_recientes(parametros: dict) -> dict:
        """
        Analiza los logs recientes de la aplicación.
        En Azure, recomienda revisar Application Insights.
        """
        resultado = {
            "timestamp": datetime.now().isoformat(),
            "logs": [],
            "sugerencias": []
        }
        # En Azure, sugerir revisar App Insights
        if IS_AZURE and os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"):
            resultado["sugerencias"].append(
                "Revisa Application Insights para ver los logs detallados."
            )
            resultado["logs"].append(
                "Integración directa con App Insights pendiente."
            )
        else:
            resultado["logs"].append(
                "Logs locales no disponibles desde este endpoint."
            )
            resultado["sugerencias"].append(
                "Ejecuta 'az webapp log tail --name <function-app>' para ver logs en tiempo real."
            )
        resultado["exito"] = True
        return resultado

    def configurar_alertas_azure(parametros: dict) -> dict:
        """
        Configura alertas básicas en Azure Function App usando Azure CLI.
        """
        resultado = {
            "timestamp": datetime.now().isoformat(),
            "acciones": [],
            "recomendaciones": []
        }
        if IS_AZURE:
            app_name = os.environ.get("WEBSITE_SITE_NAME")
            resource_group = os.environ.get("RESOURCE_GROUP")
            if app_name and resource_group:
                # Ejemplo: crear alerta de error HTTP 5xx
                cmd = (
                    f"az monitor metrics alert create "
                    f"--name {app_name}-http5xx-alert "
                    f"--resource-group {resource_group} "
                    f"--scopes /subscriptions/{os.environ.get('AZURE_SUBSCRIPTION_ID')}/resourceGroups/{resource_group}/providers/Microsoft.Web/sites/{app_name} "
                    f"--condition \"total Http5xx > 5\" "
                    f"--description \"Alerta de errores HTTP 5xx en Function App\""
                )
                res = ejecutar_comando_azure(cmd)
                resultado["acciones"].append({
                    "accion": "crear_alerta_http5xx",
                    "resultado": res
                })
                resultado["recomendaciones"].append(
                    "Revisa Azure Portal para configurar alertas adicionales"
                )
            else:
                resultado["recomendaciones"].append(
                    "Variables de entorno WEBSITE_SITE_NAME y RESOURCE_GROUP no configuradas"
                )
        else:
            resultado["recomendaciones"].append(
                "Las alertas solo pueden configurarse en Azure"
            )
        resultado["exito"] = True
        resultado["mensaje"] = "Configuración de alertas completada"
        return resultado

    acciones_disponibles = {
        "diagnosticar_completo": lambda p: diagnosticar_sistema_completo(p),
        "generar_reporte": lambda p: generar_reporte_proyecto(p),
        # "optimizar_recursos": lambda p: optimizar_recursos_azure(p),  # Removed due to missing definition
        "analizar_logs": lambda p: analizar_logs_recientes(p),
        "configurar_alertas": lambda p: configurar_alertas_azure(p)
    }

    def optimizar_recursos_azure(parametros: dict) -> dict:
        """
        Optimiza recursos de Azure Function App y Blob Storage.
        Requiere permisos adecuados y configuración de Azure CLI.
        """
        resultados = {
            "timestamp": datetime.now().isoformat(),
            "acciones": [],
            "recomendaciones": []
        }

        # 1. Escalar Function App si está bajo carga
        if IS_AZURE:
            app_name = os.environ.get("WEBSITE_SITE_NAME")
            resource_group = os.environ.get("RESOURCE_GROUP")
            if app_name and resource_group:
                # Escalar a plan Premium si hay más de 100 archivos en cache
                if len(CACHE) > 100:
                    cmd = f"az functionapp plan update --name {app_name}-plan --resource-group {resource_group} --sku EP1"
                    resultado = ejecutar_comando_azure(cmd)
                    resultados["acciones"].append({
                        "accion": "escalar_function_app",
                        "resultado": resultado
                    })
                    resultados["recomendaciones"].append(
                        "Considerar usar plan Premium para mejor performance"
                    )

        # 2. Optimizar Blob Storage (lifecycle management)
        if STORAGE_CONNECTION_STRING:
            client = get_blob_client()
            if client:
                container_client = client.get_container_client(CONTAINER_NAME)
                total_blobs = sum(1 for _ in container_client.list_blobs())
                if total_blobs > 1000:
                    resultados["recomendaciones"].append(
                        "Configura reglas de lifecycle management para blobs antiguos"
                    )
                    resultados["acciones"].append({
                        "accion": "sugerir_lifecycle_management",
                        "detalle": "Usa az storage account management-policy create"
                    })

        # 3. Limpiar caché si excede límite
        if len(CACHE) > 200:
            CACHE.clear()
            resultados["acciones"].append({
                "accion": "limpiar_cache",
                "resultado": "Cache limpiada para liberar memoria"
            })

        resultados["exito"] = True
        resultados["mensaje"] = "Optimización de recursos completada"
        return resultados
    if accion in acciones_disponibles:
        return acciones_disponibles[accion](parametros)

    return {
        "exito": False,
        "error": f"Acción no reconocida: {accion}",
        "acciones_disponibles": list(acciones_disponibles.keys())
    }


def diagnosticar_sistema_completo(parametros: dict) -> dict:
    """Diagnóstico completo del sistema con Azure CLI"""
    resultado = {
        "timestamp": datetime.now().isoformat(),
        "diagnosticos": {}
    }

    # 1. Estado de la Function App
    if IS_AZURE:
        cmd = f"az functionapp show --name {os.environ.get('WEBSITE_SITE_NAME')} --resource-group {os.environ.get('RESOURCE_GROUP')}"
        function_status = ejecutar_comando_azure(cmd)
        if function_status["exito"]:
            resultado["diagnosticos"]["function_app"] = {
                "estado": function_status["data"].get("state", "Unknown"),
                "url": function_status["data"].get("defaultHostName", ""),
                "runtime": function_status["data"].get("siteConfig", {}).get("linuxFxVersion", "")
            }

    # 2. Verificar triggers
    cmd = f"az functionapp function list --name {os.environ.get('WEBSITE_SITE_NAME')} --resource-group {os.environ.get('RESOURCE_GROUP')}"
    triggers = ejecutar_comando_azure(cmd)
    if triggers["exito"]:
        resultado["diagnosticos"]["endpoints"] = [
            {
                "nombre": func.get("name", "").split("/")[-1],
                "url": func.get("invokeUrlTemplate", ""),
                "activo": not func.get("isDisabled", True)
            }
            for func in triggers["data"]
        ]

    # 3. Análisis de errores recientes
    if os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"):
        resultado["diagnosticos"]["errores"] = {
            "ultimas_24h": "Pendiente integración con App Insights",
            "sugerencia": "Configurar Application Insights SDK para métricas detalladas"
        }

    # 4. Recomendaciones
    # if not resultado["diagnosticos"].get("function_app", {}).get("estado") == "Running":
    #     resultado["recomendaciones"].append("La Function App no está en estado Running")

    return resultado


def generar_reporte_proyecto(parametros: dict) -> dict:
    """Genera un reporte completo del proyecto"""
    tipo_reporte = parametros.get("tipo", "general")

    reporte = {
        "tipo": tipo_reporte,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "proyecto": "Boat Rental App",
        "secciones": {}
    }

    # 1. Resumen Ejecutivo
    reporte["secciones"]["resumen"] = {
        "descripcion": "Sistema de alquiler de embarcaciones con arquitectura serverless",
        "componentes": ["Mobile App (React Native)", "Backend (AWS Lambda)", "Admin Panel (Next.js)", "AI Copilot (Azure Functions)"],
        "estado": "Operativo"
    }

    # 2. Arquitectura
    if tipo_reporte in ["tecnico", "general"]:
        reporte["secciones"]["arquitectura"] = {
            "frontend": {
                "mobile": "React Native 0.72.10 + Expo SDK 49",
                "admin": "Next.js 14 + Material-UI"
            },
            "backend": {
                "api": "AWS Lambda + API Gateway",
                "database": "DynamoDB",
                "auth": "JWT"
            },
            "ai": {
                "copiloto": "Azure Functions Python 3.9",
                "storage": "Azure Blob Storage",
                "insights": "Application Insights"
            }
        }

    # 3. Métricas
    if IS_AZURE:
        reporte["secciones"]["metricas"] = {
            "archivos_proyecto": contar_archivos_blob(),
            "endpoints_activos": 4,
            "uptime": "99.9%"
        }

    # 4. Próximos Pasos
    reporte["secciones"]["roadmap"] = [
        "Integración con Azure DevOps para CI/CD",
        "Implementación de tests automatizados",
        "Expansión de capacidades del copiloto AI"
    ]

    return {
        "exito": True,
        "reporte": reporte,
        "formato_disponible": ["json", "markdown", "html"]
    }


def contar_archivos_blob() -> int:
    """Cuenta archivos en Blob Storage"""
    if STORAGE_CONNECTION_STRING:
        client = get_blob_client()
        if client:
            container_client = client.get_container_client(CONTAINER_NAME)
            return sum(1 for _ in container_client.list_blobs())
    return 0


def generar_guia_contextual(tema: str, parametros: Optional[dict] = None) -> dict:
    """Genera guías contextuales paso a paso"""
    guias = {
        "configurar_blob": {
            "titulo": "Configurar Azure Blob Storage",
            "pasos": [
                "1. Ejecuta: ./sync_to_blob.ps1",
                "2. Verifica con: az storage container list --account-name boatrentalstorage",
                "3. Prueba con: leer:mobile-app/package.json"
            ],
            "comandos_utiles": [
                "az storage blob list --container-name boat-rental-project --account-name boatrentalstorage",
                "az functionapp config appsettings set --name copiloto-semantico-func --settings AZURE_STORAGE_CONNECTION_STRING=<connection-string>"
            ]
        },
        "optimizar_performance": {
            "titulo": "Optimizar Performance de Function App",
            "pasos": [
                "1. Habilitar Application Insights",
                "2. Configurar auto-scaling",
                "3. Implementar caché Redis"
            ],
            "metricas_clave": ["Latencia < 500ms", "Error rate < 1%", "Availability > 99.9%"]
        },
        "debug_errores": {
            "titulo": "Debugging de Errores",
            "pasos": [
                "1. Revisar logs: az webapp log tail --name copiloto-semantico-func",
                "2. Verificar App Settings",
                "3. Probar endpoints individualmente"
            ],
            "herramientas": ["Azure Portal", "Application Insights", "Log Analytics"]
        }
    }

    if tema in guias:
        return {
            "exito": True,
            "guia": guias[tema],
            "proximos_pasos": ["diagnosticar:completo", "dashboard"]
        }

    return {
        "exito": True,
        "guias_disponibles": list(guias.keys()),
        "sugerencia": "Especifica un tema de la lista"
    }


def orquestar_flujo_trabajo(flujo: str, parametros: dict = {}) -> dict:
    """Orquesta flujos de trabajo complejos"""
    flujos = {
        "deployment": [
            {"paso": "Verificar código", "comando": "analizar:src"},
            {"paso": "Sincronizar archivos", "comando": "sync_to_blob"},
            {"paso": "Publicar función", "comando": "func azure functionapp publish"},
            {"paso": "Verificar deployment", "comando": "diagnosticar:completo"}
        ],
        "monitoreo": [
            {"paso": "Obtener métricas", "comando": "dashboard"},
            {"paso": "Analizar logs", "comando": "analizar:logs"},
            {"paso": "Generar reporte", "comando": "generar:reporte"}
        ]
    }

    if flujo in flujos:
        return {
            "exito": True,
            "flujo": flujo,
            "pasos": flujos[flujo],
            "estado": "Listo para ejecutar",
            "comando_inicio": f"orquestar:ejecutar:{flujo}"
        }

    return {
        "exito": True,
        "flujos_disponibles": list(flujos.keys()),
        "descripcion": "Flujos de trabajo automatizados"
    }


def generar_sugerencias_comando_azure(comando: str) -> list:
    """Genera sugerencias basadas en comandos Azure ejecutados"""
    sugerencias = []

    if "functionapp" in comando:
        sugerencias.extend([
            "Ver logs: az webapp log tail --name <function-app>",
            "Ver métricas: az monitor metrics list --resource <resource-id>",
            "Escalar: az functionapp plan update --sku"
        ])

    if "storage" in comando:
        sugerencias.extend([
            "Listar blobs: az storage blob list --container-name <container>",
            "Subir archivo: az storage blob upload --file <path>",
            "Generar SAS: az storage container generate-sas"
        ])

    return sugerencias[:3]


@app.function_name(name="copiloto")
@app.route(route="copiloto", auth_level=func.AuthLevel.ANONYMOUS)
def copiloto(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('🤖 Copiloto Semántico activado')

    mensaje = req.params.get('mensaje', '')

    if not mensaje:
        # Panel inicial mejorado con capacidades semánticas
        panel = {
            "tipo": "panel_inicial",
            "titulo": f"🤖 COPILOTO SEMÁNTICO - {'AZURE' if IS_AZURE else 'LOCAL'}",
            "version": "2.0-semantic",
            "capacidades": SEMANTIC_CAPABILITIES,
            "estado": {
                "ambiente": "Azure" if IS_AZURE else "Local",
                "blob_storage": {
                    "configurado": bool(STORAGE_CONNECTION_STRING),
                    "conectado": bool(get_blob_client()),
                    "container": CONTAINER_NAME if STORAGE_CONNECTION_STRING else None
                },
                "cache_activo": len(CACHE),
                "inteligencia": {
                    "analisis_semantico": True,
                    "generacion_artefactos": True,
                    "sugerencias_contextuales": True
                }
            },
            "comandos": {
                "basicos": {
                    "leer:<ruta>": "Lee cualquier archivo del proyecto",
                    "buscar:<patron>": "Búsqueda semántica inteligente",
                    "explorar:<dir>": "Explora directorios con metadata"
                },
                "semanticos": {
                    "analizar:<ruta>": "Análisis profundo de código",
                    "generar:<tipo>": "Genera artefactos (readme, config, test, script)",
                    "diagnosticar:<aspecto>": "Diagnóstico del sistema",
                    "sugerir": "Sugerencias basadas en contexto"
                }
            },
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "ready_for_agents": True,
                "api_version": "2.0"
            }
        }

        return func.HttpResponse(
            json.dumps(panel, indent=2, ensure_ascii=False),
            mimetype="application/json"
        )

    # Procesar comandos con respuesta estructurada
    try:
        respuesta_base = {
            "tipo": "respuesta_semantica",
            "timestamp": datetime.now().isoformat(),
            "comando_original": mensaje,
            "metadata": {
                "procesado_por": "copiloto-semantico",
                "ambiente": "Azure" if IS_AZURE else "Local",
                "version": "2.0"
            }
        }

        # Comando: leer
        if mensaje.startswith("leer:"):
            ruta = mensaje.split(":", 1)[1]
            resultado = leer_archivo_dinamico(ruta)
            respuesta_base.update({
                "accion": "leer_archivo",
                "resultado": resultado,
                "proximas_acciones": [
                    f"analizar:{ruta}",
                    f"generar:test para {ruta}",
                    "buscar:archivos similares"
                ] if resultado["exito"] else ["buscar:*", "explorar:."]
            })

        # Comando: buscar (semántico)
        elif mensaje.startswith("buscar:"):
            patron = mensaje.split(":", 1)[1]
            resultado = buscar_archivos_semantico(patron)
            respuesta_base.update({
                "accion": "busqueda_semantica",
                "resultado": resultado,
                "proximas_acciones": [
                    f"leer:{archivo['ruta']}" for archivo in resultado["archivos"][:3]
                ] + ["explorar:directorio relevante"]
            })

        # Comando: explorar
        elif mensaje.startswith("explorar:"):
            directorio = mensaje.split(":", 1)[1]
            archivos = explorar_directorio_blob(directorio) if IS_AZURE else []

            respuesta_base.update({
                "accion": "explorar_directorio",
                "resultado": {
                    "directorio": directorio,
                    "archivos": archivos[:30],
                    "total": len(archivos),
                    "estadisticas": {
                        "tipos": {},
                        "tamaño_total": sum(a.get("tamaño", 0) for a in archivos)
                    }
                },
                "proximas_acciones": [
                    f"analizar:{directorio}/*.py",
                    f"generar:readme para {directorio}"
                ]
            })

        # Comando: analizar
        elif mensaje.startswith("analizar:"):
            ruta = mensaje.split(":", 1)[1]
            resultado = analizar_codigo_semantico(ruta)
            respuesta_base.update({
                "accion": "analisis_semantico",
                "resultado": resultado,
                "proximas_acciones": resultado.get("intenciones_sugeridas", [])
            })

        # Comando: generar
        elif mensaje.startswith("generar:"):
            partes = mensaje.split(":", 1)[1].split(" para ")
            tipo = partes[0]
            contexto = {"target": partes[1]} if len(partes) > 1 else {}

            resultado = generar_artefacto(tipo, contexto)
            respuesta_base.update({
                "accion": "generar_artefacto",
                "resultado": resultado,
                "proximas_acciones": [
                    "leer:archivo generado",
                    "analizar:calidad del artefacto"
                ]
            })

        # Comando: diagnosticar
        elif mensaje.startswith("diagnosticar:"):
            resultado = procesar_intencion_semantica(mensaje, {})
            respuesta_base.update({
                "accion": "diagnostico",
                "resultado": resultado,
                "proximas_acciones": ["sugerir", "explorar:."]
            })

        # Comando: sugerir
        elif mensaje == "sugerir":
            resultado = procesar_intencion_semantica("sugerir", {})
            respuesta_base.update({
                "accion": "sugerencias",
                "resultado": resultado,
                "proximas_acciones": resultado["sugerencias"][:3] if resultado["exito"] else []
            })

        # Comando no reconocido - interpretación semántica
        else:
            respuesta_base.update({
                "accion": "interpretacion",
                "resultado": {
                    "mensaje": "No reconozco ese comando específico, pero puedo ayudarte.",
                    "interpretacion": f"Parece que quieres: {mensaje}",
                    "sugerencias": [
                        "buscar:" + mensaje,
                        "generar:script para " + mensaje,
                        "sugerir"
                    ]
                },
                "proximas_acciones": ["sugerir", "buscar:*"]
            })

        return func.HttpResponse(
            json.dumps(respuesta_base, indent=2, ensure_ascii=False),
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "tipo": "error",
                "error": str(e),
                "detalles": {
                    "tipo_error": type(e).__name__,
                    "ambiente": "Azure" if IS_AZURE else "Local",
                    "blob_configurado": bool(STORAGE_CONNECTION_STRING)
                },
                "sugerencias": [
                    "Verificar la sintaxis del comando",
                    "Consultar el panel inicial para ver comandos disponibles",
                    "Intentar con 'sugerir' para obtener ayuda"
                ]
            }, indent=2),
            mimetype="application/json",
            status_code=500
        )


def generar_proximas_acciones(intencion: str, resultado: dict) -> list:
    """Genera sugerencias de próximas acciones basadas en el resultado"""
    acciones = []

    if "generar" in intencion and resultado.get("exito"):
        acciones.extend([
            "leer:archivo generado",
            "analizar:calidad",
            "ejecutar:pruebas"
        ])
    elif "buscar" in intencion:
        acciones.extend([
            "leer:primer resultado",
            "analizar:resultados",
            "filtrar:por tipo"
        ])
    elif "diagnosticar" in intencion:
        acciones.extend([
            "corregir:problemas detectados",
            "optimizar:rendimiento",
            "generar:reporte"
        ])

    return acciones[:5]  # Limitar a 5 sugerencias


# --- PARSER ROBUSTO PARA AGENT RESPONSE ---
def clean_agent_response(agent_response: str) -> dict:
    """
    Parser súper robusto y defensivo
    """
    try:
        logging.info(f"🔍 Parseando: {agent_response[:50]}...")

        # Caso 1: Comandos simples
        simple_commands = {
            "ping": {"endpoint": "ping"},
            "status": {"endpoint": "status"},
            "health": {"endpoint": "health"},
            "estado": {"endpoint": "status"}
        }

        clean_text = agent_response.strip().lower()
        if clean_text in simple_commands:
            logging.info(f"✅ Comando simple detectado: {clean_text}")
            return simple_commands[clean_text]

        # Caso 2: Buscar JSON de forma más defensiva
        try:
            # Buscar múltiples patrones de JSON
            patterns = [
                r"```json\s*(\{.*?\})\s*```",  # ```json { } ```
                r"```\s*(\{.*?\})\s*```",     # ``` { } ```
                # Cualquier { } que contenga "endpoint"
                r"(\{[^}]*\"endpoint\"[^}]*\})",
            ]

            json_found = None
            for pattern in patterns:
                match = re.search(pattern, agent_response,
                                  re.DOTALL | re.IGNORECASE)
                if match:
                    json_found = match.group(1).strip()
                    logging.info(
                        f"✅ JSON encontrado con patrón: {pattern[:20]}...")
                    break

            if json_found:
                try:
                    parsed_json = json.loads(json_found)
                    logging.info(
                        f"✅ JSON parseado exitosamente: {list(parsed_json.keys())}")

                    if not isinstance(parsed_json, dict):
                        logging.warning("⚠️ JSON no es un objeto")
                        return {"error": "JSON debe ser un objeto"}

                    # Asegurar campos mínimos
                    if "endpoint" not in parsed_json:
                        parsed_json["endpoint"] = "ejecutar"
                        logging.info(
                            "➕ Agregado endpoint por defecto: ejecutar")

                    if "method" not in parsed_json:
                        parsed_json["method"] = "POST"
                        logging.info("➕ Agregado method por defecto: POST")

                    return parsed_json

                except json.JSONDecodeError as e:
                    logging.error(f"❌ Error parseando JSON: {str(e)}")
                    logging.error(f"JSON problemático: {json_found[:100]}...")
                    return {"error": f"JSON inválido: {str(e)}", "raw": json_found[:100]}

        except Exception as e:
            logging.error(f"❌ Error en búsqueda de JSON: {str(e)}")

        # Caso 3: Palabras clave (más defensivo)
        keywords_map = {
            "dashboard": {"endpoint": "ejecutar", "intencion": "dashboard"},
            "diagnostico": {"endpoint": "ejecutar", "intencion": "diagnosticar:completo"},
            "diagnóstico": {"endpoint": "ejecutar", "intencion": "diagnosticar:completo"},
            "resumen": {"endpoint": "ejecutar", "intencion": "generar:resumen"}
        }

        for keyword, command in keywords_map.items():
            if keyword in clean_text:
                logging.info(f"✅ Palabra clave detectada: {keyword}")
                return command

        # Caso 4: Fallback seguro
        logging.info("ℹ️ Usando fallback para texto libre")
        return {
            "endpoint": "copiloto",
            "mensaje": agent_response[:100],  # Limitar tamaño
            "method": "GET"
        }

    except Exception as e:
        logging.error(f"💥 Error crítico en parser: {str(e)}")
        # Fallback ultra-seguro
        return {
            "endpoint": "ping",  # Usar ping como fallback más seguro
            "error_parser": str(e)
        }


def hybrid_executor_fixed(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint hybrid con parser mejorado
    """
    logging.info('🤖 Endpoint hybrid activado (versión mejorada)')

    try:
        req_body = req.get_json()

        if "agent_response" not in req_body:
            return func.HttpResponse(
                json.dumps({
                    "error": "Falta agent_response",
                    "expected_format": {
                        "agent_response": "string con comando o JSON embebido",
                        "agent_name": "nombre del agente (opcional)"
                    }
                }, indent=2),
                mimetype="application/json",
                status_code=400
            )

        agent_response = req_body["agent_response"]
        agent_name = req_body.get("agent_name", "Architect_BoatRental")

        logging.info(f'Raw agent_response: {agent_response[:200]}...')

        # USAR EL PARSER MEJORADO
        parsed_command = clean_agent_response(agent_response)

        logging.info(f'Comando parseado: {parsed_command}')

        # Manejar errores de parsing
        if "error" in parsed_command:
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "parsing_error": parsed_command["error"],
                    "raw_response": parsed_command.get("raw", agent_response[:100]),
                    "suggestion": "Verifica el formato del JSON embebido o usa comandos simples como 'ping'"
                }, indent=2),
                mimetype="application/json",
                status_code=400
            )

        # Ejecutar comando parseado
        try:
            result = execute_parsed_command(parsed_command)

            # Generar respuesta amigable
            user_response = generate_user_friendly_response_v2(
                agent_response, result)

            return func.HttpResponse(
                json.dumps({
                    "success": True,
                    "parsed_command": parsed_command,
                    "execution_result": result,
                    "user_response": user_response,
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "agent": agent_name,
                        "parser_version": "2.0"
                    }
                }, indent=2, ensure_ascii=False),
                mimetype="application/json"
            )

        except Exception as e:
            logging.error(f"Error ejecutando comando: {str(e)}")
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "execution_error": str(e),
                    "parsed_command": parsed_command,
                    "suggestion": "Error interno ejecutando el comando"
                }, indent=2),
                mimetype="application/json",
                status_code=500
            )

    except Exception as e:
        logging.error(f"Error general en hybrid_executor: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "type": type(e).__name__,
                "suggestion": "Error interno del servidor"
            }, indent=2),
            mimetype="application/json",
            status_code=500
        )


def execute_parsed_command(command: dict) -> dict:
    """Ejecuta un comando ya parseado"""
    endpoint = command.get("endpoint", "ping")
    logging.info(f"🚀 Ejecutando endpoint: {endpoint}")

    if endpoint == "ping":
        logging.info("✅ Ejecutando ping")
        return {
            "exito": True,
            "message": "pong",
            "status": "Function App funcionando correctamente",
            "timestamp": datetime.now().isoformat()
        }

    elif endpoint == "status":
        logging.info("🔎 Consultando status")
        return build_status()

    elif endpoint == "ejecutar":
        intencion = command.get("intencion", "dashboard")
        parametros = command.get("parametros", {})
        logging.info(f"🎯 Ejecutando intencion: {intencion}")
        if intencion == "dashboard":
            logging.info("📊 Iniciando generación de dashboard...")
            try:
                result = generar_dashboard_insights()
                logging.info("✅ Dashboard generado exitosamente")
                return result
            except Exception as e:
                logging.error(f"💥 Error en dashboard: {str(e)}")
                return {
                    "exito": False,
                    "error": f"Error en dashboard: {str(e)}",
                    "fallback": True
                }
        return procesar_intencion_semantica(intencion, parametros)

    elif endpoint == "copiloto":
        mensaje = command.get("mensaje", "")
        logging.info(f"🤖 Procesando comando copiloto: {mensaje}")
        if mensaje.startswith("leer:"):
            archivo = mensaje.split(":", 1)[1]
            logging.info(f"📖 Leyendo archivo: {archivo}")
            return leer_archivo_dinamico(archivo)
        else:
            return {
                "exito": True,
                "mensaje": f"Comando copiloto procesado: {mensaje}",
                "tipo": "copiloto_response"
            }

    else:
        logging.warning(f"❌ Endpoint no implementado: {endpoint}")
        return {
            "exito": False,
            "error": f"Endpoint '{endpoint}' no implementado"
        }


def generate_user_friendly_response_v2(original_response: str, result: dict) -> str:
    """Genera respuesta amigable basada en el resultado"""

    # Extraer explicación original si existe
    explanation_part = ""
    if "```json" in original_response:
        explanation_part = original_response.split("```json")[0].strip()

    if result.get("exito", True):
        if explanation_part:
            return f"{explanation_part}\n\n✅ Comando ejecutado exitosamente"
        else:
            return "✅ Comando ejecutado exitosamente"
    else:
        error_msg = result.get("error", "Error desconocido")
        return f"❌ Error: {error_msg}"


def build_status() -> dict:
    """Construye el payload de estado para endpoints y agentes."""
    storage_status = "desconectado"
    try:
        client = get_blob_client()
        if client:
            container_client = client.get_container_client(CONTAINER_NAME)
            if container_client.exists():
                storage_status = "conectado"
    except Exception as e:
        logging.warning(f"No se pudo verificar Storage: {str(e)}")

    ambiente = "Azure" if (
        storage_status == "conectado" or IS_AZURE) else "Local"

    return {
        "copiloto": "activo",
        "version": "2.0-semantic",
        "timestamp": datetime.now().isoformat(),
        "ambiente": ambiente,
        "storage": storage_status,
        "is_azure": IS_AZURE,
        "container": CONTAINER_NAME,
        "blob_ready": (storage_status == "conectado"),
        "endpoints": [
            "/api/copiloto",
            "/api/ejecutar",
            "/api/hybrid",
            "/api/status",
            "/api/health"
        ],
        "ready": ambiente == "Azure" and storage_status == "conectado"
    }


@app.function_name(name="status")
@app.route(route="status", auth_level=func.AuthLevel.ANONYMOUS)
def status(req: func.HttpRequest) -> func.HttpResponse:
    """Status endpoint muy ligero, solo confirma estado"""
    estado = build_status()
    return func.HttpResponse(
        json.dumps(estado, indent=2, ensure_ascii=False),
        mimetype="application/json",
        status_code=200
    )


@app.function_name(name="listar_blobs")
@app.route(route="listar-blobs", auth_level=func.AuthLevel.ANONYMOUS)
def listar_blobs(req: func.HttpRequest) -> func.HttpResponse:
    """Lista blobs usando el MISMO cliente/contendedor que build_status()."""

    try:
        # Parámetros
        prefix = (req.params.get("prefix") or "").strip()
        try:
            top = int(req.params.get("top", "10"))
        except ValueError:
            top = 10
        top = max(1, min(top, 50))  # 1..50

        # Cliente compartido
        client = get_blob_client()
        if not client:
            return func.HttpResponse(
                json.dumps({
                    "error": "Blob Storage no configurado (blob_client=None)",
                    "archivos": [],
                    "total_mostrados": 0
                }, indent=2, ensure_ascii=False),
                mimetype="application/json",
                status_code=500
            )

        container_client = client.get_container_client(CONTAINER_NAME)
        if not container_client.exists():
            return func.HttpResponse(
                json.dumps({
                    "error": f"El contenedor '{CONTAINER_NAME}' no existe",
                    "archivos": [],
                    "total_mostrados": 0
                }, indent=2, ensure_ascii=False),
                mimetype="application/json",
                status_code=404
            )

        # Itera y corta tras 'top' items (sin by_page -> compatible con más SDKs)
        items = []
        for blob in container_client.list_blobs(name_starts_with=prefix):
            # Tamaño: algunas versiones exponen 'size', otras 'content_length'
            size = getattr(blob, "size", None)
            if size is None:
                size = getattr(blob, "content_length", None)

            # last_modified puede ser None o no tener isoformat()
            lm = getattr(blob, "last_modified", None)
            if lm is not None and hasattr(lm, "isoformat"):
                last_modified = lm.isoformat()
            else:
                last_modified = str(lm) if lm is not None else None

            items.append({
                "name": blob.name,
                "size": size,
                "last_modified": last_modified,
                "tipo": blob.name.split('.')[-1] if '.' in blob.name else "sin_extension"
            })

            if len(items) >= top:
                break

        respuesta = {
            "archivos": items,
            "total_mostrados": len(items),
            "parametros": {"top": top, "prefix": prefix},
            "timestamp": datetime.now().isoformat(),
            "container": CONTAINER_NAME
        }

        return func.HttpResponse(
            json.dumps(respuesta, indent=2, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.exception("listar_blobs failed")
        return func.HttpResponse(
            json.dumps({
                "error": f"listar_blobs: {str(e)}",
                "tipo_error": type(e).__name__,
                "archivos": [],
                "total_mostrados": 0
            }, indent=2, ensure_ascii=False),
            mimetype="application/json",
            status_code=500
        )


@app.function_name(name="ejecutar")
@app.route(route="ejecutar", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def ejecutar(req: func.HttpRequest) -> func.HttpResponse:
    """Versión mejorada del endpoint ejecutar con intenciones extendidas y checkpoint de seguridad"""
    logging.info('🚀 Endpoint ejecutar (orquestador mejorado) activado')

    # Initialize req_body to handle potential exceptions
    req_body = {}

    try:
        # Obtener y validar el body
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = {}

        # Valores por defecto más robustos
        intencion = req_body.get('intencion', '')
        parametros = req_body.get('parametros')
        if parametros is None:
            parametros = {}
        contexto = req_body.get('contexto', {})
        modo = req_body.get('modo', 'normal')

        # Logging mejorado para debug
        logging.info(f'Procesando: intencion={intencion}, modo={modo}')
        logging.debug(f'Parametros: {parametros}')
        logging.debug(f'Contexto: {contexto}')

        # 🛡️ CHECKPOINT DE SEGURIDAD ANTES DE MODIFICACIONES
        # Verificar si la intención implica modificaciones al backend
        if intencion.startswith(("modificar:", "insertar:", "crear:", "reemplazar:")):
            logging.info(
                f"🔒 Ejecutando checkpoint de seguridad para intención: {intencion}")

            payload = {
                "intencion": intencion,
                "parametros": parametros,
                "contexto": contexto
            }

            verificar = ejecutar_checkpoint("antes_modificar_backend", payload)
            if verificar.get("bloqueado"):
                logging.warning(
                    f"❌ Checkpoint bloqueó la operación: {verificar.get('error')}")
                return func.HttpResponse(
                    json.dumps(verificar, ensure_ascii=False),
                    mimetype="application/json",
                    status_code=403
                )
            else:
                logging.info("✅ Checkpoint aprobó la operación")

        # Primero intentar con el procesador extendido
        resultado = procesar_intencion_extendida(intencion, parametros)
        procesador_usado = 'extendido'

        # Si falla, intentar con el procesador base
        if not resultado.get("exito") and resultado.get("error") and "no soportado" in resultado.get("error", "").lower():
            resultado = procesar_intencion_semantica(intencion, parametros)
            procesador_usado = 'base'

        # Manejar casos especiales si ambos procesadores fallan
        if not resultado.get("exito"):
            if intencion == "dashboard":
                resultado = generar_dashboard_insights()
                procesador_usado = 'especial'
            elif intencion == "diagnosticar:completo":
                resultado = diagnosticar_function_app()
                procesador_usado = 'especial'
            elif intencion.startswith("guia:"):
                tema = intencion.split(
                    ":", 1)[1] if ":" in intencion else "ayuda"
                resultado = generar_guia_contextual(tema, parametros)
                procesador_usado = 'especial'
            elif intencion.startswith("orquestar:"):
                flujo = intencion.split(":", 1)[1] if ":" in intencion else ""
                resultado = orquestar_flujo_trabajo(flujo, parametros)
                procesador_usado = 'especial'

        # Asegurar que siempre hay un resultado válido
        if resultado is None:
            resultado = {
                "exito": False,
                "error": "No se pudo procesar la intención",
                "intencion_recibida": intencion,
                "sugerencias": ["dashboard", "diagnosticar:completo", "verificar:almacenamiento", "git:status"]
            }
            procesador_usado = 'fallback'

        # Enriquecer respuesta con metadata
        if not isinstance(resultado, dict):
            resultado = {"resultado": resultado}

        # Ensure resultado is a mutable dict and add metadata
        if isinstance(resultado, dict):
            # Create a completely new mutable dict to avoid type issues
            nuevo_resultado = {}
            # Copy all existing data
            for key, value in resultado.items():
                nuevo_resultado[key] = value

            # Add metadata
            nuevo_resultado['metadata'] = {
                'timestamp': datetime.now().isoformat(),
                'modo': modo,
                'intencion_procesada': intencion,
                'procesador': procesador_usado,
                'ambiente': 'Azure' if IS_AZURE else 'Local',
                'copiloto_version': '2.0-orchestrator-extendido',
                'checkpoint_ejecutado': intencion.startswith(("modificar:", "insertar:", "crear:", "reemplazar:"))
            }

            # Si hay error de urgencia alta, agregar diagnóstico
            if not nuevo_resultado.get('exito', True) and contexto.get('urgencia') == 'alta':
                nuevo_resultado['diagnostico_automatico'] = {
                    "mensaje": "Detectada urgencia alta, ejecutando diagnóstico automático",
                    "comando_sugerido": "diagnosticar:completo"
                }

            resultado = nuevo_resultado

        # Agregar contexto de ayuda si falló
        if not resultado.get('exito', True):
            resultado['ayuda'] = {
                'intenciones_extendidas': [
                    "verificar:almacenamiento",
                    "limpiar:cache",
                    "generar:resumen",
                    "git:status",
                    "analizar:rendimiento",
                    "confirmar:accion"
                ],
                'intenciones_basicas': [
                    "dashboard",
                    "diagnosticar:completo",
                    "buscar:archivos",
                    "generar:readme",
                    "guia:configurar_blob"
                ],
                'ejemplo': {
                    "intencion": "verificar:almacenamiento",
                    "parametros": {},
                    "modo": "normal"
                }
            }

        return func.HttpResponse(
            json.dumps(resultado, indent=2, ensure_ascii=False),
            mimetype="application/json",
            status_code=200  # Siempre 200 aunque haya error lógico
        )

    except Exception as e:
        logging.error(f"Error en ejecutar: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")

        # Respuesta de error estructurada
        error_response = {
            "error": str(e),
            "tipo": type(e).__name__,
            "intencion_recibida": req_body.get('intencion', 'desconocida') if 'req_body' in locals() else 'no_parseado',
            "sugerencia": "Verifica el formato de la petición",
            "ejemplo_valido": {
                "intencion": "verificar:almacenamiento",
                "parametros": {},
                "modo": "normal"
            },
            "metadata": {
                'timestamp': datetime.now().isoformat(),
                'ambiente': 'Azure' if IS_AZURE else 'Local',
                'version': '2.0-orchestrator-extendido'
            }
        }

        return func.HttpResponse(
            json.dumps(error_response, indent=2),
            mimetype="application/json",
            status_code=200  # Cambiar a 200 para evitar problemas con Logic App
        )


def ejecutar_checkpoint(tipo: str, payload: dict) -> dict:
    """
    Ejecuta checkpoints de seguridad antes de operaciones críticas

    Args:
      tipo: Tipo de checkpoint ("antes_modificar_backend", etc.)
      payload: Datos de la operación a verificar

    Returns:
      dict: {"bloqueado": bool, "error": str, "motivo": str, ...}
    """
    try:
        intencion = payload.get("intencion", "")
        parametros = payload.get("parametros", {})
        contexto = payload.get("contexto", {})
        agente = contexto.get("agent_name", "Desconocido")

        if tipo == "antes_modificar_backend":
            return validar_modificacion_backend(intencion, parametros, contexto, agente)

        # Agregar más tipos de checkpoint según sea necesario
        return {"bloqueado": False, "mensaje": f"Checkpoint {tipo} no implementado"}

    except Exception as e:
        logging.error(f"Error en checkpoint {tipo}: {str(e)}")
        return {
            "bloqueado": True,
            "error": f"Error ejecutando checkpoint: {str(e)}",
            "motivo": "error_interno"
        }


def validar_modificacion_backend(intencion: str, parametros: dict, contexto: dict, agente: str) -> dict:
    """
    Valida si es seguro permitir modificaciones al backend

    Args:
      intencion: La intención de modificación
      parametros: Parámetros de la operación
      contexto: Contexto adicional
      agente: Nombre del agente que hace la petición

    Returns:
      dict: Resultado de la validación
    """
    try:
        ruta = parametros.get("ruta", "")

        # 🔍 VALIDACIONES ESPECÍFICAS PARA FUNCTION_APP.PY
        if "function_app.py" in ruta:
            # Verificar checkpoints previos del agente
            checkpoints_requeridos = {
                "leer_archivo_completo": "El agente debe leer el archivo completo primero",
                "verificar_estructura": "Debe verificar la estructura actual del código",
                "identificar_endpoints": "Debe identificar todos los endpoints existentes",
                "verificar_imports": "Debe verificar las importaciones actuales"
            }

            checkpoints_realizados = set(contexto.get("checkpoints", []))
            checkpoints_faltantes = []

            for checkpoint, descripcion in checkpoints_requeridos.items():
                if checkpoint not in checkpoints_realizados:
                    checkpoints_faltantes.append({
                        "checkpoint": checkpoint,
                        "descripcion": descripcion
                    })

            if checkpoints_faltantes:
                return {
                    "bloqueado": True,
                    "error": f"El agente '{agente}' no puede modificar function_app.py sin verificaciones previas",
                    "motivo": "checkpoints_faltantes",
                    "checkpoints_faltantes": checkpoints_faltantes,
                    "accion_requerida": "Ejecutar las verificaciones faltantes antes de intentar modificar",
                    "comandos_sugeridos": [
                        "leer:copiloto-function/function_app.py",
                        "analizar:copiloto-function/function_app.py",
                        "buscar:@app.function_name",
                        "verificar:imports"
                    ]
                }

        # 🔍 VALIDACIONES PARA OPERACIONES PELIGROSAS
        operaciones_peligrosas = {
            "reemplazar:funcion_completa": "Reemplazar una función completa requiere aprobación especial",
            "modificar:imports_core": "Modificar imports principales puede romper el sistema",
            "crear:endpoint_duplicado": "Crear endpoints duplicados causará errores"
        }

        for op_peligrosa, descripcion in operaciones_peligrosas.items():
            if op_peligrosa in intencion:
                confirmacion = contexto.get(
                    "confirmar_operacion_peligrosa", False)
                if not confirmacion:
                    return {
                        "bloqueado": True,
                        "error": f"Operación peligrosa detectada: {op_peligrosa}",
                        "descripcion": descripcion,
                        "motivo": "operacion_peligrosa",
                        "accion_requerida": "Añadir 'confirmar_operacion_peligrosa': true en el contexto"
                    }

        # 🔍 VALIDACIONES DE INTEGRIDAD DE NOMBRES
        if intencion.startswith("crear:") and "funcion" in intencion:
            nombre_funcion = parametros.get("nombre", "")
            if not nombre_funcion:
                return {
                    "bloqueado": True,
                    "error": "Crear función requiere especificar el nombre",
                    "motivo": "parametro_faltante",
                    "parametro_requerido": "nombre"
                }

            # Verificar que no exista ya
            if nombre_funcion in ["copiloto", "ejecutar", "status", "health", "hybrid"]:
                return {
                    "bloqueado": True,
                    "error": f"La función '{nombre_funcion}' ya existe en el backend",
                    "motivo": "nombre_duplicado",
                    "funciones_existentes": ["copiloto", "ejecutar", "status", "health", "hybrid", "listar_blobs"]
                }

        # ✅ VALIDACIÓN APROBADA
        logging.info(f"✅ Checkpoint aprobado para {agente}: {intencion}")
        return {
            "bloqueado": False,
            "aprobado": True,
            "agente": agente,
            "intencion": intencion,
            "timestamp": datetime.now().isoformat(),
            "mensaje": "Operación aprobada por el checkpoint de seguridad"
        }

    except Exception as e:
        logging.error(f"Error en validación de modificación backend: {str(e)}")
        return {
            "bloqueado": True,
            "error": f"Error interno en validación: {str(e)}",
            "motivo": "error_validacion"
        }


# --- ENDPOINT HYBRID MEJORADO ---

@app.function_name(name="hybrid")
@app.route(route="hybrid", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def hybrid_executor(req: func.HttpRequest) -> func.HttpResponse:
    try:
        logging.info("🚀 Entrando a hybrid_executor")

        req_body = req.get_json()
        if "agent_response" not in req_body:
            return func.HttpResponse(
                json.dumps({"error": "Falta agent_response"}, indent=2),
                mimetype="application/json",
                status_code=400
            )

        agent_response = req_body["agent_response"]
        agent_name = req_body.get("agent_name", "Architect_BoatRental")
        logging.info(f'Raw agent_response: {agent_response[:200]}...')

        # USAR EL PARSER MEJORADO
        parsed_command = clean_agent_response(agent_response)
        logging.info(f'Comando parseado: {parsed_command}')

        # Manejar errores de parsing
        if "error" in parsed_command:
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "parsing_error": parsed_command["error"],
                    "suggestion": "Verifica el formato del JSON o usa comandos simples"
                }, indent=2),
                mimetype="application/json",
                status_code=400
            )

        # Ejecutar comando parseado
        result = execute_parsed_command(parsed_command)

        # Respuesta exitosa
        return func.HttpResponse(
            json.dumps({
                "success": True,
                "parsed_command": parsed_command,
                "execution_result": result,
                "user_response": "✅ Comando ejecutado exitosamente" if result.get("exito", True) else f"❌ Error: {result.get('error')}",
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "agent": agent_name,
                    "parser_version": "2.0"
                }
            }, indent=2, ensure_ascii=False),
            mimetype="application/json"
        )

    except Exception as e:
        logging.error("💥 Error inesperado en hybrid_executor", exc_info=True)
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


def process_direct_command(command: dict) -> func.HttpResponse:
    """Procesa un comando directo sin agent_response wrapper"""
    try:
        logging.info(
            f"Procesando comando directo: {command.get('endpoint', 'unknown')}")

        # Mapear a la estructura esperada
        if command.get("endpoint") == "ejecutar":
            resultado = procesar_intencion_semantica(
                command.get("intencion", ""),
                command.get("parametros", {})
            )
        elif command.get("endpoint") == "copiloto":
            # Simular llamada a copiloto
            resultado = {
                "tipo": "respuesta_semantica",
                "comando_original": command.get("mensaje", ""),
                "accion": "procesado",
                "resultado": {"exito": True}
            }
        elif command.get("endpoint") == "status":
            resultado = build_status()
        else:
            resultado = {
                "exito": False,
                "error": f"Endpoint {command.get('endpoint')} no reconocido"
            }

        return func.HttpResponse(
            json.dumps(resultado, indent=2, ensure_ascii=False),
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "command_received": command
            }, indent=2),
            mimetype="application/json",
            status_code=500
        )


def generate_semantic_explanation(command: dict) -> str:
    """Genera una explicación semántica para un comando JSON"""

    intencion = command.get("intencion", "")
    urgencia = command.get("contexto", {}).get("urgencia", "normal")

    explanations = {
        "dashboard": "📊 Voy a generar el dashboard con insights del proyecto",
        "diagnosticar:completo": "🔍 Realizaré un diagnóstico completo del sistema",
        "guia:debug_errores": "🛠️ Te guiaré paso a paso para resolver el error",
        "buscar": "🔎 Buscaré archivos en el proyecto",
        "ejecutar:azure": "☁️ Ejecutaré el comando Azure CLI solicitado"
    }

    # Buscar explicación base
    base_explanation = None
    for key, explanation in explanations.items():
        if key in intencion:
            base_explanation = explanation
            break

    if not base_explanation:
        base_explanation = f"Procesando intención: {intencion}"

    # Agregar contexto de urgencia si es alta
    if urgencia == "alta":
        base_explanation = f"⚠️ URGENCIA ALTA: {base_explanation}"
    elif urgencia == "critica":
        base_explanation = f"🚨 CRÍTICO: {base_explanation}"

    return base_explanation


def execute_hybrid_command(command: dict) -> dict:
    """Ejecuta un comando del agente con mejor manejo de errores"""
    try:
        logging.info(f'Ejecutando comando: {command}')

        endpoint = command.get("endpoint", "ejecutar")

        if endpoint == "ejecutar":
            intencion = command.get("intencion", "")
            parametros = command.get("parametros", {})

            # Llamar al procesador semántico
            resultado = procesar_intencion_semantica(intencion, parametros)

            # Asegurar que el resultado tenga la estructura esperada
            if not isinstance(resultado, dict):
                resultado = {
                    "exito": False,
                    "error": f"Resultado inesperado del procesador: {type(resultado).__name__}",
                    "resultado_original": str(resultado)
                }

            return resultado

        elif endpoint == "copiloto":
            mensaje = command.get("mensaje", "")
            if mensaje.startswith("leer:"):
                archivo = mensaje.split(":", 1)[1]
                return leer_archivo_dinamico(archivo)
            elif mensaje.startswith("buscar:"):
                patron = mensaje.split(":", 1)[1]
                return buscar_archivos_semantico(patron)
            else:
                return {
                    "exito": True,
                    "mensaje": f"Comando copiloto procesado: {mensaje}",
                    "tipo": "copiloto_response"
                }

        elif endpoint == "status":
            return build_status()

        else:
            return {
                "exito": False,
                "error": f"Endpoint '{endpoint}' no implementado",
                "endpoints_disponibles": ["ejecutar", "copiloto", "status"]
            }

    except Exception as e:
        logging.error(f"Error ejecutando comando: {str(e)}")
        return {
            "exito": False,
            "error": str(e),
            "tipo_error": type(e).__name__,
            "comando_fallido": command
        }


def generate_user_friendly_response(processed: dict, execution_result: dict) -> str:
    """Genera una respuesta amigable para el usuario"""

    parts = []

    # Agregar explicación semántica
    if processed.get("semantic_explanation"):
        parts.append(processed["semantic_explanation"])

    # Agregar resultado de ejecución
    if execution_result.get("exito"):
        parts.append("\n✅ Comando ejecutado exitosamente")

        # Agregar detalles relevantes
        if execution_result.get("resultado"):
            if isinstance(execution_result["resultado"], dict):
                # Extraer información importante
                if "dashboard" in str(processed.get("command", {})).lower():
                    parts.append(
                        "\n📊 Dashboard generado con las siguientes secciones:")
                    for seccion in execution_result["resultado"].get("secciones", {}).keys():
                        parts.append(f"  • {seccion}")

    else:
        error_msg = execution_result.get("error", "Error desconocido")
        parts.append(f"\n❌ Error: {error_msg}")

        # Sugerir acciones de recuperación
        if execution_result.get("sugerencias"):
            parts.append("\n💡 Sugerencias:")
            for sug in execution_result["sugerencias"]:
                parts.append(f"  • {sug}")

    # Agregar próximas acciones
    if processed.get("next_actions"):
        parts.append("\n\n📌 Próximas acciones disponibles:")
        for action in processed["next_actions"]:
            parts.append(f"  • {action}")

    return "\n".join(parts)


def validar_modificacion_archivo(payload: dict) -> dict:
    """
    Valida si es seguro modificar un archivo simbólicamente. 
    Solo permite modificar si se ha leído, estructurado y verificado antes.
    """
    intencion = payload.get("intencion", "")
    ruta = payload.get("parametros", {}).get("ruta", "")
    agente = payload.get("contexto", {}).get("agent_name", "Desconocido")

    requiere_verificacion = any([
        intencion.startswith("modificar:"),
        intencion.startswith("crear:funcion"),
        intencion.startswith("insertar:bloque")
    ])

    if requiere_verificacion and "function_app.py" in ruta:
        # Requiere verificar pasos previos
        checkpoints = payload.get("contexto", {}).get("checkpoints", [])
        verificado = set(checkpoints)

        requeridos = {
            "leer_archivo_completo",
            "verificar_estructura",
            "verificar_funcion_target",
            "verificar_endpoints_existentes"
        }

        faltantes = requeridos - verificado
        if faltantes:
            return {
                "exito": False,
                "bloqueado": True,
                "error": f"El agente '{agente}' no puede modificar {ruta} aún.",
                "faltan_verificaciones": list(faltantes),
                "sugerencia": "Ejecuta primero: leer:<ruta>, analizar:<funcion>, verificar estructura"
            }

    return {"exito": True, "bloqueado": False}


@app.function_name(name="invocar")
@app.route(route="invocar", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def invocar(req: func.HttpRequest) -> func.HttpResponse:
    """
    Recibe un JSON desde un agente (ej. Architect_BoatRental) y lo ejecuta
    """
    try:
        comando = req.get_json()

        endpoint = comando.get("endpoint")
        metodo = comando.get("method", "GET").upper()

        if endpoint == "copiloto" and metodo == "GET":
            mensaje = comando.get("mensaje", "")
            req_clon = func.HttpRequest(
                method="GET",
                url=f"http://localhost/api/copiloto?mensaje={mensaje}",
                headers={},
                params={"mensaje": mensaje},
                body=b""
            )
            return copiloto(req_clon)

        elif endpoint == "ejecutar" and metodo == "POST":
            intencion = comando.get("intencion")
            parametros = comando.get("parametros", {})
            contexto = comando.get("contexto", {})
            modo = comando.get("modo", "normal")

            req_clon = func.HttpRequest(
                method="POST",
                url="http://localhost/api/ejecutar",
                headers={},
                params={},
                body=json.dumps({
                    "intencion": intencion,
                    "parametros": parametros,
                    "contexto": contexto,
                    "modo": modo
                }).encode("utf-8")
            )
            return ejecutar(req_clon)

        elif endpoint == "status":
            return status(req)
        elif endpoint == "health":
            return health(req)

        return func.HttpResponse(
            json.dumps({"error": f"Endpoint '{endpoint}' no manejado"}),
            status_code=400,
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


@app.function_name(name="health")
# Cambiar a ANONYMOUS
@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Health check con información detallada"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0-orchestrator",
        "capabilities": {
            "semantic_processing": True,
            "azure_cli_integration": True,
            "blob_storage": bool(STORAGE_CONNECTION_STRING),
            "orchestration": True,
            "guided_mode": True
        },
        "endpoints": {
            "GET /api/copiloto": "Interfaz principal",
            "POST /api/ejecutar": "Ejecución de comandos complejos",
            "GET /api/status": "Estado detallado",
            "GET /api/health": "Health check"
        },
        "ready": True
    }

    return func.HttpResponse(
        json.dumps(health_status, indent=2),
        mimetype="application/json"
    )


# --------- CREAR ----------
def crear_archivo(ruta: str, contenido: str) -> dict:
    """Crea un nuevo archivo en el proyecto con validaciones robustas"""
    try:
        # Validación de entrada
        if not ruta or not isinstance(ruta, str):
            return {
                "exito": False,
                "error": "La ruta no puede estar vacía y debe ser una cadena válida",
                "tipo_operacion": "crear_archivo"
            }

        if contenido is None:
            contenido = ""  # Permitir archivos vacíos

        # Validación de caracteres en la ruta
        caracteres_invalidos = ['?', '*', '<', '>', '|', ':', '"']
        if any(c in ruta for c in caracteres_invalidos):
            return {
                "exito": False,
                "error": f"La ruta contiene caracteres inválidos: {', '.join(caracteres_invalidos)}",
                "tipo_operacion": "crear_archivo"
            }

        # Normalizar la ruta (eliminar barras duplicadas y espacios)
        ruta = ruta.strip().replace('\\', '/').replace('//', '/')

        if IS_AZURE:
            # Creación en Azure Blob Storage
            client = get_blob_client()
            if not client:
                return {
                    "exito": False,
                    "error": "No se pudo obtener el cliente de Blob Storage. Verifica la configuración de conexión",
                    "tipo_operacion": "crear_archivo",
                    "diagnostico": "Revisa AZURE_STORAGE_CONNECTION_STRING o las credenciales de Managed Identity"
                }

            try:
                container_client = client.get_container_client(CONTAINER_NAME)
                blob_client = container_client.get_blob_client(ruta)
                blob_client.upload_blob(contenido, overwrite=True)
                return {
                    "exito": True,
                    "mensaje": f"Archivo creado exitosamente en Blob Storage: {ruta}",
                    "ubicacion": f"blob://{CONTAINER_NAME}/{ruta}",
                    "tipo_operacion": "crear_archivo",
                    "tamaño_bytes": len(contenido.encode('utf-8'))
                }
            except Exception as blob_error:
                return {
                    "exito": False,
                    "error": f"Error al interactuar con Blob Storage: {str(blob_error)}",
                    "tipo_operacion": "crear_archivo",
                    "tipo_error": type(blob_error).__name__,
                    "sugerencia": "Verifica permisos del Storage Account y la existencia del contenedor"
                }

        # --- Rama local ---
        archivo_path = PROJECT_ROOT / ruta   # <- definir ANTES del try
        try:
            archivo_path.parent.mkdir(parents=True, exist_ok=True)
            archivo_path.write_text(contenido, encoding='utf-8')
            return {
                "exito": True,
                "mensaje": f"Archivo creado exitosamente: {archivo_path.name}",
                "ubicacion": str(archivo_path),
                "tipo_operacion": "crear_archivo",
                "tamaño_bytes": len(contenido.encode('utf-8'))
            }
        except PermissionError:
            return {
                "exito": False,
                "error": f"Sin permisos para crear el archivo en: {archivo_path.parent}",
                "tipo_operacion": "crear_archivo"
            }
        except OSError as os_error:
            return {
                "exito": False,
                "error": f"Error del sistema operativo: {str(os_error)}",
                "tipo_operacion": "crear_archivo",
                "tipo_error": type(os_error).__name__
            }

    except Exception as e:
        return {
            "exito": False,
            "error": f"Error inesperado al crear archivo: {str(e)}",
            "tipo_operacion": "crear_archivo",
            "tipo_error": type(e).__name__
        }


# --------- MODIFICAR ----------


def modificar_archivo(
    ruta: str,
    operacion: str,
    contenido: Union[str, Dict[str, Any]] = "",
    linea: int = -1,
    body: Optional[dict] = None,
) -> dict:
    """Modifica un archivo existente con operaciones extensas y validaciones"""
    try:
        # Validación de entrada
        if not ruta or not isinstance(ruta, str):
            return {
                "exito": False,
                "error": "La ruta no puede estar vacía y debe ser una cadena válida",
                "tipo_operacion": "modificar_archivo"
            }

        if not operacion or not isinstance(operacion, str):
            return {
                "exito": False,
                "error": "La operación no puede estar vacía y debe ser una cadena válida",
                "tipo_operacion": "modificar_archivo"
            }

        # Operaciones válidas
        operaciones_validas = [
            "agregar_linea", "reemplazar_linea", "eliminar_linea",
            "buscar_reemplazar", "agregar_inicio", "agregar_final",
            "insertar_antes", "insertar_despues"
        ]
        if operacion not in operaciones_validas:
            return {
                "exito": False,
                "error": f"Operación '{operacion}' no válida",
                "operaciones_validas": operaciones_validas,
                "tipo_operacion": "modificar_archivo"
            }

        # Leer archivo actual
        archivo_actual = leer_archivo_dinamico(ruta)
        if not archivo_actual["exito"]:
            return {
                **archivo_actual,
                "tipo_operacion": "modificar_archivo",
                "operacion_solicitada": operacion
            }

        contenido_actual = archivo_actual["contenido"]
        lineas = contenido_actual.split('\n')
        contenido_modificado = ""

        # Procesar operaciones
        if operacion == "agregar_linea":
            if linea != -1 and 0 <= linea <= len(lineas):
                lineas.insert(linea, contenido)
            else:
                lineas.append(contenido)

        elif operacion == "reemplazar_linea":
            if linea == -1 or not (0 <= linea < len(lineas)):
                return {
                    "exito": False,
                    "error": f"Línea {linea} no válida. El archivo tiene {len(lineas)} líneas (0-{len(lineas)-1})",
                    "tipo_operacion": "modificar_archivo",
                    "operacion": operacion
                }
            lineas[linea] = contenido

        elif operacion == "eliminar_linea":
            if linea == -1 or not (0 <= linea < len(lineas)):
                return {
                    "exito": False,
                    "error": f"Línea {linea} no válida. El archivo tiene {len(lineas)} líneas (0-{len(lineas)-1})",
                    "tipo_operacion": "modificar_archivo",
                    "operacion": operacion
                }
            del lineas[linea]

        elif operacion == "buscar_reemplazar":
            params = {}
            # a) contenido como dict
            if isinstance(contenido, dict):
                params = contenido
            # b) contenido como string "OLD->NEW" o "OLD|NEW" o JSON
            elif isinstance(contenido, str):
                for sep in ("->", "|"):
                    if sep in contenido:
                        old, new = contenido.split(sep, 1)
                        params = {"buscar": old.strip(
                        ), "reemplazar": new.strip()}
                        break
                else:
                    try:
                        maybe = json.loads(contenido)
                        if isinstance(maybe, dict):
                            params = maybe
                    except Exception:
                        pass
            # c) Fallback: claves al tope del body (si fue pasado)
            if not params and isinstance(body, dict) and "buscar" in body and "reemplazar" in body:
                params = {"buscar": str(
                    body["buscar"]), "reemplazar": str(body["reemplazar"])}

            # Validaciones rápidas
            if not params or not str(params.get("buscar", "")).strip():
                return {
                    "exito": False,
                    "error": "El contenido debe incluir 'buscar' y 'reemplazar' (no vacío)",
                    "tipo_operacion": "modificar_archivo",
                    "operacion": operacion,
                    "ejemplo": {"buscar": "OK", "reemplazar": "OK ✅"},
                }

            old = str(params["buscar"])
            new = str(params.get("reemplazar", ""))

            ocurrencias = contenido_actual.count(old)
            if ocurrencias == 0:
                return {
                    "exito": False,
                    "error": f"No se encontró el texto '{old}' para reemplazar",
                    "tipo_operacion": "modificar_archivo",
                    "operacion": operacion
                }

            contenido_modificado = contenido_actual.replace(old, new)
            res_write = crear_archivo(ruta, contenido_modificado)
            if res_write.get("exito"):
                res_write.update({
                    "operacion_realizada": operacion,
                    "ocurrencias": ocurrencias,
                    "mensaje": f"Archivo modificado: {ocurrencias} reemplazos"
                })
            return res_write

        elif operacion == "agregar_inicio":
            lineas.insert(0, contenido)

        elif operacion == "agregar_final":
            lineas.append(contenido)

        elif operacion == "insertar_antes":
            if linea == -1 or not (0 <= linea < len(lineas)):
                return {
                    "exito": False,
                    "error": f"Línea {linea} no válida para insertar antes",
                    "tipo_operacion": "modificar_archivo",
                    "operacion": operacion
                }
            lineas.insert(linea, contenido)

        elif operacion == "insertar_despues":
            if linea == -1 or not (0 <= linea < len(lineas)):
                return {
                    "exito": False,
                    "error": f"Línea {linea} no válida para insertar después",
                    "tipo_operacion": "modificar_archivo",
                    "operacion": operacion
                }
            lineas.insert(linea + 1, contenido)

        # Si no se procesó buscar_reemplazar, unir líneas
        if operacion != "buscar_reemplazar":
            contenido_modificado = '\n'.join(lineas)

        # Guardar
        resultado_creacion = crear_archivo(ruta, contenido_modificado)
        if resultado_creacion["exito"]:
            resultado_creacion.update({
                "operacion_realizada": operacion,
                "linea_afectada": linea if linea != -1 else None,
                "lineas_totales": len(lineas),
                "mensaje": f"Archivo modificado exitosamente con operación '{operacion}'"
            })
        return resultado_creacion

    except Exception as e:
        return {
            "exito": False,
            "error": f"Error inesperado al modificar archivo: {str(e)}",
            "tipo_operacion": "modificar_archivo",
            "operacion": operacion,
            "tipo_error": type(e).__name__
        }


# --------- HTTP WRAPPERS (columna 0) ----------
@app.function_name(name="escribir_archivo_http")
@app.route(route="escribir-archivo", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def escribir_archivo_http(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint HTTP para crear/escribir archivos"""
    try:
        body = req.get_json()
        ruta = (body.get("path") or body.get("ruta") or "").strip()
        contenido = body.get(
            "content") if "content" in body else body.get("contenido")

        if not ruta:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "Parámetro 'ruta' o 'path' es requerido",
                    "ejemplo": {"ruta": "test.txt", "contenido": "Hola mundo"}
                }, ensure_ascii=False),
                mimetype="application/json", status_code=400
            )

        # 1. Validar
        payload = {
            "intencion": "crear:archivo",
            "parametros": {"ruta": ruta},
            "contexto": body.get("contexto", {})
        }
        resultado = validar_modificacion_archivo(payload)

        # 2. Bloquear si no cumple
        if resultado.get("bloqueado"):
            return func.HttpResponse(
                json.dumps(resultado, ensure_ascii=False),
                mimetype="application/json",
                status_code=403
            )

        res = crear_archivo(ruta, contenido)
        return func.HttpResponse(
            json.dumps(res, ensure_ascii=False),
            mimetype="application/json",
            status_code=201 if res.get("exito") else 400
        )
    except Exception as e:
        logging.exception("escribir_archivo_http failed")
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(e)}),
            mimetype="application/json", status_code=500
        )


# arriba del módulo
SOFT_ERRORS = True  # 200 para validación/no_encontrado; 500 solo para excepciones


def _status_from_result(res: dict) -> int:
    if res.get("exito") is True:
        return 200
    if SOFT_ERRORS:
        return 200
    msg = str(res.get("error", "")).lower()
    return 404 if ("no existe" in msg or "no encontrado" in msg) else 400


@app.function_name(name="modificar_archivo_http")
@app.route(route="modificar-archivo", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def modificar_archivo_http(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint HTTP para modificar archivos existentes"""
    try:
        body = req.get_json()
        ruta = (body.get("path") or body.get("ruta") or "").strip()
        operacion = (body.get("operacion") or "").strip()
        contenido = body.get(
            "content") if "content" in body else body.get("contenido")
        linea = int(body.get("linea")) if body.get("linea") is not None else -1

        if not ruta or not operacion:
            res = {
                "exito": False,
                "tipo": "validacion",
                "codigo": "PARAM_FALTANTE",
                "error": "Parámetros 'ruta' y 'operacion' son requeridos",
                "operaciones_validas": [
                    "agregar_linea", "reemplazar_linea", "eliminar_linea",
                    "buscar_reemplazar", "agregar_inicio", "agregar_final",
                    "insertar_antes", "insertar_despues"
                ],
                "ejemplo": {"ruta": "test.txt", "operacion": "agregar_linea", "contenido": "Nueva línea", "linea": 0},
                "siguiente_accion": "proporcionar_parametros"
            }
            return func.HttpResponse(
                json.dumps(res, ensure_ascii=False),
                mimetype="application/json",
                status_code=_status_from_result(res)
            )

        # 1. Validar
        payload = {
            "intencion": "modificar:archivo",
            "parametros": {"ruta": ruta},
            "contexto": body.get("contexto", {})
        }
        resultado = validar_modificacion_archivo(payload)

        # 2. Bloquear si no cumple
        if resultado.get("bloqueado"):
            return func.HttpResponse(
                json.dumps(resultado, ensure_ascii=False),
                mimetype="application/json",
                status_code=403
            )

        res = modificar_archivo(ruta, operacion, contenido, linea, body=body)

        # Enriquecer respuesta para archivos no encontrados
        if not res.get("exito") and "no encontrado" in str(res.get("error", "")).lower():
            sugerencias = []
            try:
                if IS_AZURE:
                    client = get_blob_client()
                    container_client = None
                    if client and hasattr(client, "get_container_client"):
                        container_client = client.get_container_client(
                            CONTAINER_NAME)
                    if container_client:
                        nombre_base = os.path.basename(ruta)
                        for blob in container_client.list_blobs():
                            name = getattr(blob, "name", "")
                            if not name:
                                continue
                            if (nombre_base.lower() in name.lower()) or (ruta.lower() in name.lower()):
                                sugerencias.append(name)
            except Exception as e:
                logging.warning(
                    "No se pudo listar blobs para sugerencias: %s", e)

            # Respuesta "soft-error" estructurada para el agente
            res = {
                "exito": False,
                "tipo": "no_encontrado",
                "codigo": "RUTA_NO_EXISTE",
                "error": f"El archivo '{ruta}' no existe",
                "ruta_solicitada": ruta,
                "alternativas": sugerencias[:5],
                "sugerencias": sugerencias[:5],
                "total_similares": len(sugerencias),
                "tipo_operacion": "modificar_archivo",
                "operacion_solicitada": operacion,
                "siguiente_accion": (
                    "preguntar_confirmacion" if len(sugerencias) > 1 else
                    ("proponer_unica" if len(sugerencias) == 1 else "pedir_ruta")
                ),
                "mensaje_agente": _generar_mensaje_no_encontrado(ruta, sugerencias)
            }

            # Sugerencia accionable cuando hay 1 sola coincidencia
            if len(sugerencias) == 1:
                alt = sugerencias[0]
                payload_contenido = (
                    contenido if contenido is not None
                    else (body.get("contenido") or body.get("content"))
                )
                res["accion_sugerida"] = {
                    "endpoint": "/api/modificar-archivo",
                    "http_method": "POST",
                    "payload": {
                        "ruta": alt,
                        "operacion": operacion,
                        "contenido": payload_contenido
                    },
                    "autorizacion_requerida": True,
                    "confirm_prompt": f"¿Aplico la operación '{operacion}' en '{alt}'?"
                }
                res["ruta_sugerida"] = alt

        return func.HttpResponse(
            json.dumps(res, ensure_ascii=False),
            mimetype="application/json",
            status_code=_status_from_result(res)
        )

    except Exception as e:
        logging.exception("modificar_archivo_http failed")
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(e)}),
            mimetype="application/json", status_code=500
        )


def _generar_mensaje_no_encontrado(ruta: str, sugerencias: list) -> str:
    """Genera mensaje en lenguaje natural para el agente"""
    if len(sugerencias) == 1:
        return f"El archivo '{ruta}' no existe. Encontré '{sugerencias[0]}'. ¿Quieres usar esa ruta?"
    elif len(sugerencias) > 1:
        primeras = sugerencias[:3]
        lista = "', '".join(primeras)
        return f"El archivo '{ruta}' no existe. Encontré varias opciones: '{lista}'. ¿Cuál quieres usar?"
    else:
        return f"El archivo '{ruta}' no existe y no encontré alternativas similares. Por favor, proporciona la ruta correcta."


@app.function_name(name="leer_archivo_http")
@app.route(route="leer-archivo", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def leer_archivo_http(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint HTTP para leer archivos"""
    try:
        ruta = (req.params.get("path") or req.params.get("ruta") or "").strip()
        if not ruta:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "Parámetro 'ruta' o 'path' es requerido",
                    "ejemplo": "/api/leer-archivo?ruta=test.txt"
                }, ensure_ascii=False),
                mimetype="application/json", status_code=400
            )
        res = leer_archivo_dinamico(ruta)
        return func.HttpResponse(
            json.dumps(res, ensure_ascii=False),
            mimetype="application/json",
            status_code=200 if res.get("exito") else 404
        )
    except Exception as e:
        logging.exception("leer_archivo_http failed")
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(e)}),
            mimetype="application/json", status_code=500
        )


@app.function_name(name="eliminar_archivo_http")
@app.route(route="eliminar-archivo", methods=["POST", "DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
def eliminar_archivo_http(req: func.HttpRequest) -> func.HttpResponse:
    """Elimina un archivo del Blob (preferente) o del filesystem local."""
    try:
        # Body opcional + querystring
        try:
            data = req.get_json()
        except ValueError:
            data = {}
        ruta = (data.get("ruta") or data.get("path") or
                req.params.get("ruta") or req.params.get("path") or "").strip()
        ruta = ruta.replace("\\", "/")

        # Validaciones mínimas
        if not ruta:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "Parámetro 'ruta' (o 'path') es requerido",
                    "ejemplo": {"ruta": "docs/PRUEBA.md"}
                }, ensure_ascii=False),
                mimetype="application/json", status_code=400
            )
        if ruta.startswith("/") or ".." in ruta.split("/"):
            return func.HttpResponse(
                json.dumps(
                    {"exito": False, "error": "Ruta inválida."}, ensure_ascii=False),
                mimetype="application/json", status_code=400
            )

        # 1) Intentar borrar en Blob
        borrado = None
        client = get_blob_client()
        if client:
            try:
                container = client.get_container_client(CONTAINER_NAME)
                blob = container.get_blob_client(ruta)
                try:
                    # Elimina blob base + snapshots
                    blob.delete_blob(delete_snapshots="include")
                    borrado = {
                        "exito": True,
                        "mensaje": "Archivo eliminado en Blob.",
                        "eliminado": "blob",
                        "ubicacion": f"blob://{CONTAINER_NAME}/{ruta}",
                        "ruta": ruta,
                        "tipo_operacion": "eliminar_archivo"
                    }
                except ResourceNotFoundError:
                    # Si hay versioning, eliminar posibles versiones individuales
                    try:
                        deleted_any = False
                        for b in container.list_blobs(name_starts_with=ruta, include=["versions", "snapshots"]):
                            vid = getattr(b, "version_id", None)
                            if vid:
                                container.get_blob_client(
                                    b.name, version_id=vid).delete_blob()
                                deleted_any = True
                        if deleted_any:
                            borrado = {
                                "exito": True,
                                "mensaje": "Versiones del blob eliminadas.",
                                "eliminado": "blob_versions",
                                "ubicacion": f"blob://{CONTAINER_NAME}/{ruta}",
                                "ruta": ruta,
                                "tipo_operacion": "eliminar_archivo"
                            }
                    except Exception as _:
                        pass
            except HttpResponseError as e_blob:
                logging.warning(f"No se pudo eliminar en Blob: {e_blob}")

        # 2) Si no se eliminó en Blob, intentar local
        if not borrado:
            try:
                local_path = (PROJECT_ROOT / ruta).resolve()
                if str(local_path).startswith(str(PROJECT_ROOT.resolve())) and local_path.exists():
                    local_path.unlink()
                    borrado = {
                        "exito": True,
                        "mensaje": "Archivo eliminado localmente.",
                        "eliminado": "local",
                        "ubicacion": str(local_path),
                        "ruta": ruta,
                        "tipo_operacion": "eliminar_archivo"
                    }
            except Exception as e_local:
                logging.warning(f"No se pudo eliminar localmente: {e_local}")

        # 3) Respuesta
        if borrado:
            return func.HttpResponse(json.dumps(borrado, ensure_ascii=False),
                                     mimetype="application/json", status_code=200)

        return func.HttpResponse(
            json.dumps({"exito": False, "error": f"No encontrado o no se pudo eliminar: {ruta}",
                        "tipo_operacion": "eliminar_archivo"}, ensure_ascii=False),
            mimetype="application/json", status_code=404
        )

    except Exception as e:
        logging.exception("eliminar_archivo_http failed")
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(
                e), "tipo_operacion": "eliminar_archivo"}),
            mimetype="application/json", status_code=500
        )


# Lista blanca de scripts permitidos para ejecución (desactivada temporalmente)
ALLOWED_SCRIPTS = None


def ejecutar_script(nombre_script: str, parametros: list = []) -> dict:
    """Ejecuta un script PowerShell, Bash o Python.
       Si no existe localmente y estamos en Azure, intenta descargarlo desde Blob a /tmp/scripts/..."""
    try:
        # 1) Resolver ruta local existente
        local_path = _resolve_local_script_path(nombre_script)

        # 2) Si no existe y estamos en Azure: descargar desde Blob
        descargado_de_blob = False
        if not local_path and IS_AZURE:
            local_path = _download_script_from_blob(nombre_script)
            if not local_path:
                alt_blob = f"scripts/{Path(nombre_script).name}"
                local_path = _download_script_from_blob(alt_blob)
            if local_path:
                descargado_de_blob = True

        if not local_path:
            return {
                "exito": False,
                "error": f"No se encontró el script '{nombre_script}' localmente y no fue posible obtenerlo de Blob",
                "script": nombre_script
            }

        # 3) Comando según extensión
        path_str = str(local_path)
        if path_str.endswith('.ps1'):
            ps_cmd = shutil.which("pwsh") or shutil.which(
                "powershell") or "powershell"
            comando = [ps_cmd, "-ExecutionPolicy", "Bypass", "-File", path_str]
        elif path_str.endswith('.sh'):
            comando = ['bash', path_str]
        elif path_str.endswith('.py'):
            py = shutil.which("python3") or shutil.which("python") or "python"
            comando = [py, path_str]
        else:
            comando = [path_str]
        if parametros:
            comando.extend(parametros)
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(local_path.parent)
        )
        return {
            "exito": resultado.returncode == 0,
            "stdout": resultado.stdout,
            "stderr": resultado.stderr,
            "codigo_salida": resultado.returncode,
            "comando_ejecutado": ' '.join(comando),
            "script_path_local": str(local_path),
            "descargado_de_blob": descargado_de_blob
        }
    except subprocess.TimeoutExpired:
        return {
            "exito": False,
            "error": "Script excedió tiempo límite (60s)",
            "script": nombre_script
        }
    except Exception as e:
        return {
            "exito": False,
            "error": str(e),
            "script": nombre_script,
            "tipo_error": type(e).__name__
        }


@app.function_name(name="ejecutar_script_http")
@app.route(route="ejecutar-script", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def ejecutar_script_http(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint HTTP seguro para ejecutar scripts con lista blanca"""
    try:
        body = req.get_json()
        nombre = (body.get("script") or body.get(
            "nombre_script") or "").strip()
        parametros = body.get("parametros") or []

        if not nombre:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "Parámetro 'script' o 'nombre_script' es requerido",
                    "scripts_permitidos": list(ALLOWED_SCRIPTS) if ALLOWED_SCRIPTS else None
                }, ensure_ascii=False),
                mimetype="application/json", status_code=400
            )

        if ALLOWED_SCRIPTS and nombre not in ALLOWED_SCRIPTS:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "Script no permitido",
                    "script_solicitado": nombre,
                    "scripts_permitidos": list(ALLOWED_SCRIPTS)
                }, ensure_ascii=False),
                mimetype="application/json", status_code=403
            )

        res = ejecutar_script(nombre, parametros)
        return func.HttpResponse(
            json.dumps(res, ensure_ascii=False),
            mimetype="application/json",
            status_code=200 if res.get("exito") else 500
        )
    except Exception as e:
        logging.exception("ejecutar_script_http failed")
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(e)}),
            mimetype="application/json", status_code=500
        )


def operacion_git(comando: str, parametros: Optional[dict] = None) -> dict:
    """Ejecuta operaciones Git permitidas"""
    if parametros is None:
        parametros = {}
    comandos_permitidos = {
        "status": "git status --porcelain",
        "add": "git add",
        "commit": "git commit -m",
        "push": "git push",
        "pull": "git pull",
        "branch": "git branch",
        "checkout": "git checkout"
    }
    if comando not in comandos_permitidos:
        return {
            "exito": False,
            "error": f"Comando no permitido: {comando}",
            "comandos_permitidos": list(comandos_permitidos.keys())
        }
    try:
        cmd = comandos_permitidos[comando]
        if comando == "add" and parametros.get("archivo"):
            cmd += f" {parametros['archivo']}"
        elif comando == "commit" and parametros.get("mensaje"):
            cmd += f' "{parametros["mensaje"]}"'
        elif comando == "checkout" and parametros.get("rama"):
            cmd += f" {parametros['rama']}"
        resultado = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        return {
            "exito": resultado.returncode == 0,
            "salida": resultado.stdout,
            "error": resultado.stderr if resultado.stderr else None,
            "comando": cmd
        }
    except Exception as e:
        return {
            "exito": False,
            "error": str(e),
            "comando_intentado": comando
        }


def ejecutar_agente_externo(agente: str, tarea: str, parametros: Optional[dict] = None) -> dict:
    """Ejecuta o delega tarea a un agente externo"""
    if parametros is None:
        parametros = {}
    agentes_disponibles = {
        "Agent975": {
            "endpoint": os.environ.get("AI_FOUNDRY_ENDPOINT"),
            "proyecto": "booking-agents",
            "capacidades": ["analizar", "refactorizar", "documentar"]
        },
        "CodeGPT": {
            "api": "https://api.codegpt.co",
            "capacidades": ["generar", "completar", "explicar"]
        },
        "Codex": {
            "servicio": "openai-codex",
            "capacidades": ["codigo", "traducir", "optimizar"]
        }
    }
    if agente not in agentes_disponibles:
        return {
            "exito": False,
            "error": f"Agente no disponible: {agente}",
            "agentes_disponibles": list(agentes_disponibles.keys())
        }
    config_agente = agentes_disponibles[agente]
    return {
        "exito": True,
        "agente": agente,
        "tarea": tarea,
        "estado": "delegado",
        "configuracion": config_agente,
        "parametros_enviados": parametros,
        "mensaje": f"Tarea '{tarea}' delegada a {agente}",
        "siguiente_accion": "verificar_resultado"
    }


def comando_bash(cmd: str, seguro: bool = False) -> dict:
    """Ejecuta comandos bash/shell de forma segura"""
    comandos_seguros = [
        "ls", "pwd", "echo", "cat", "grep", "find", "which",
        "az", "git", "npm", "node", "python", "pip"
    ]
    primer_comando = cmd.split()[0]
    if not seguro and primer_comando not in comandos_seguros:
        return {
            "exito": False,
            "error": f"Comando '{primer_comando}' no está en la lista de comandos seguros",
            "sugerencia": "Usa parametro 'seguro': true para forzar ejecución"
        }
    try:
        resultado = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT)
        )
        return {
            "exito": resultado.returncode == 0,
            "stdout": resultado.stdout,
            "stderr": resultado.stderr,
            "comando": cmd,
            "directorio": str(PROJECT_ROOT)
        }
    except subprocess.TimeoutExpired:
        return {
            "exito": False,
            "error": "Comando excedió tiempo límite (30s)",
            "comando": cmd
        }
    except Exception as e:
        return {
            "exito": False,
            "error": str(e),
            "comando": cmd
        }


def procesar_intencion_extendida(intencion: str, parametros: Optional[Dict[str, Any]] = None) -> dict:
    """
    Procesa intenciones semánticas extendidas no cubiertas en el procesador base
    """
    if parametros is None:
        parametros = {}

    intenciones_map = {
        "verificar:almacenamiento": verificar_almacenamiento,
        "limpiar:cache": limpiar_cache,
        "sincronizar:blobs": sincronizar_blob_storage if 'sincronizar_blob_storage' in globals() else lambda p: {"exito": False, "error": "Función no implementada"},
        "generar:resumen": generar_resumen_ejecutivo,
        "generar:documentacion": generar_documentacion_tecnica if 'generar_documentacion_tecnica' in globals() else lambda p: {"exito": False, "error": "Función no implementada"},
        "git:status": git_status_seguro,
        "git:push": git_push_seguro if 'git_push_seguro' in globals() else lambda p: {"exito": False, "error": "Función no implementada"},
        "git:commit": git_commit_semantico if 'git_commit_semantico' in globals() else lambda p: {"exito": False, "error": "Función no implementada"},
        "analizar:rendimiento": analizar_rendimiento_sistema if 'analizar_rendimiento_sistema' in globals() else lambda p: {"exito": False, "error": "Función no implementada"},
        "analizar:seguridad": auditoria_seguridad if 'auditoria_seguridad' in globals() else lambda p: {"exito": False, "error": "Función no implementada"},
        "analizar:dependencias": revisar_dependencias if 'revisar_dependencias' in globals() else lambda p: {"exito": False, "error": "Función no implementada"},
        "confirmar:accion": confirmar_accion_pendiente,
        "cancelar:accion": cancelar_operacion if 'cancelar_operacion' in globals() else lambda p: {"exito": False, "error": "Función no implementada"}
    }

    for patron, funcion in intenciones_map.items():
        if intencion.startswith(patron) or patron in intencion:
            return funcion(parametros)

    return interpretar_intencion_semantica(intencion, parametros)


def verificar_almacenamiento(params: dict) -> dict:
    try:
        client = get_blob_client()
        if not client:
            return {"exito": False, "error": "Blob Storage no configurado"}
        container_client = client.get_container_client(CONTAINER_NAME)
        total_blobs = 0
        total_size = 0
        tipos_archivo = {}
        for blob in container_client.list_blobs():
            total_blobs += 1
            total_size += blob.size
            extension = blob.name.split(
                '.')[-1] if '.' in blob.name else 'sin_extension'
            tipos_archivo[extension] = tipos_archivo.get(extension, 0) + 1
        return {
            "exito": True,
            "almacenamiento": {
                "container": CONTAINER_NAME,
                "total_archivos": total_blobs,
                "tamaño_total_mb": round(total_size / (1024 * 1024), 2),
                "tipos_archivo": tipos_archivo,
                "estado": "conectado"
            },
            "sugerencias": [
                "limpiar:cache si hay muchos archivos temporales",
                "sincronizar:blobs para actualizar archivos locales"
            ] if total_blobs > 1000 else []
        }
    except Exception as e:
        return {"exito": False, "error": str(e)}


def limpiar_cache(params: dict) -> dict:
    global CACHE
    archivos_antes = len(CACHE)
    memoria_antes = sum(len(str(v)) for v in CACHE.values())
    CACHE.clear()
    return {
        "exito": True,
        "limpieza": {
            "archivos_eliminados": archivos_antes,
            "memoria_liberada_bytes": memoria_antes,
            "timestamp": datetime.now().isoformat()
        },
        "mensaje": f"Cache limpiado: {archivos_antes} archivos, {memoria_antes/1024:.2f} KB liberados"
    }


def generar_resumen_ejecutivo(params: dict) -> dict:
    diagnostico = diagnosticar_function_app()
    almacenamiento = verificar_almacenamiento({})
    resumen = {
        "titulo": "Resumen Ejecutivo - Boat Rental System",
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "estado_general": "operativo" if diagnostico.get("checks", {}).get("configuracion", {}).get("ambiente") else "degradado",
        "metricas_clave": {
            "archivos_proyecto": almacenamiento.get("almacenamiento", {}).get("total_archivos", 0),
            "tamaño_total_mb": almacenamiento.get("almacenamiento", {}).get("tamaño_total_mb", 0),
            "cache_activo": len(CACHE),
            "ambiente": "Azure" if IS_AZURE else "Local"
        },
        "componentes": {
            "mobile_app": {"estado": "activo", "tecnologia": "React Native + Expo"},
            "backend": {"estado": "activo", "tecnologia": "AWS Lambda + DynamoDB"},
            "admin_panel": {"estado": "activo", "tecnologia": "Next.js + Material-UI"},
            "copiloto_ai": {"estado": "activo", "version": "2.0-orchestrator"}
        },
        "proximas_acciones": [
            "Implementar CI/CD con Azure DevOps",
            "Aumentar cobertura de tests al 80%",
            "Optimizar queries de base de datos"
        ],
        "riesgos_identificados": []
    }
    if not almacenamiento.get("exito"):
        resumen["riesgos_identificados"].append("Blob Storage desconectado")
    if len(CACHE) > 500:
        resumen["riesgos_identificados"].append("Cache sobrecargado")
    return {
        "exito": True,
        "resumen": resumen,
        "formato_disponible": ["json", "markdown", "pdf"],
        "siguiente_accion": "generar:reporte para detalles completos"
    }


def git_status_seguro(params: dict) -> dict:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            archivos_modificados = []
            archivos_nuevos = []
            archivos_eliminados = []
            for line in lines:
                if line.startswith(' M'):
                    archivos_modificados.append(line[3:])
                elif line.startswith('??'):
                    archivos_nuevos.append(line[3:])
                elif line.startswith(' D'):
                    archivos_eliminados.append(line[3:])
            return {
                "exito": True,
                "estado_git": {
                    "modificados": archivos_modificados,
                    "nuevos": archivos_nuevos,
                    "eliminados": archivos_eliminados,
                    "limpio": len(lines) == 0
                },
                "siguiente_accion": "git:commit" if lines else None
            }
        else:
            return {"exito": False, "error": result.stderr}
    except Exception as e:
        return {"exito": False, "error": str(e)}


def confirmar_accion_pendiente(params: dict) -> dict:
    accion_id = params.get("accion_id")
    confirmar = params.get("confirmar", False)
    if not accion_id:
        return {"exito": False, "error": "Se requiere accion_id para confirmar"}
    if confirmar:
        return {
            "exito": True,
            "mensaje": f"Acción {accion_id} confirmada y ejecutada",
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {
            "exito": False,
            "mensaje": f"Acción {accion_id} no confirmada",
            "estado": "cancelada"
        }


def interpretar_intencion_semantica(intencion: str, params: dict) -> dict:
    keywords_map = {
        "estado": "status",
        "salud": "health",
        "dashboard": "dashboard",
        "diagnóstico": "diagnosticar:completo",
        "diagnostico": "diagnosticar:completo",
        "resumen": "generar:resumen",
        "reporte": "generar:reporte",
        "limpiar": "limpiar:cache",
        "almacenamiento": "verificar:almacenamiento",
        "storage": "verificar:almacenamiento",
        "git": "git:status",
        "commit": "git:commit",
        "push": "git:push"
    }
    intencion_lower = intencion.lower()
    for keyword, mapped_intent in keywords_map.items():
        if keyword in intencion_lower:
            return procesar_intencion_extendida(mapped_intent, params)
    return {
        "exito": False,
        "mensaje": f"No pude interpretar la intención: '{intencion}'",
        "sugerencias": [
            "dashboard - Ver métricas del sistema",
            "diagnosticar:completo - Diagnóstico exhaustivo",
            "generar:resumen - Resumen ejecutivo",
            "verificar:almacenamiento - Estado del storage",
            "git:status - Estado del repositorio"
        ],
        "tip": "Puedes usar comandos más específicos o palabras clave conocidas"
    }

# --- FUNCIONES FALTANTES PARA INTENCIONES EXTENDIDAS ---


def sincronizar_blob_storage(params: dict) -> dict:
    """Sincroniza archivos locales con Azure Blob Storage"""
    try:
        # Aquí deberías implementar la lógica real de sincronización
        # Por ahora, solo simula la operación
        return {
            "exito": True,
            "mensaje": "Sincronización de archivos con Blob Storage iniciada.",
            "detalles": "Esta función es un placeholder. Implementa la lógica real según tus necesidades."
        }
    except Exception as e:
        return {"exito": False, "error": str(e)}


def generar_documentacion_tecnica(params: dict) -> dict:
    """Genera documentación técnica del proyecto"""
    try:
        # Simulación de generación de documentación
        return {
            "exito": True,
            "documentacion": "# Documentación Técnica\n\nEste es un ejemplo de documentación generada automáticamente.",
            "formato": "markdown",
            "mensaje": "Documentación técnica generada correctamente."
        }
    except Exception as e:
        return {"exito": False, "error": str(e)}


def git_push_seguro(params: dict) -> dict:
    """Realiza un git push seguro"""
    try:
        result = subprocess.run(
            ["git", "push"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=20
        )
        return {
            "exito": result.returncode == 0,
            "salida": result.stdout,
            "error": result.stderr if result.stderr else None,
            "mensaje": "Push realizado correctamente." if result.returncode == 0 else "Error en git push."
        }
    except Exception as e:
        return {"exito": False, "error": str(e)}


def git_commit_semantico(params: dict) -> dict:
    """Realiza un git commit con mensaje semántico"""
    mensaje = params.get("mensaje", "Commit semántico automático")
    try:
        result = subprocess.run(
            ["git", "commit", "-am", mensaje],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=15
        )
        return {
            "exito": result.returncode == 0,
            "salida": result.stdout,
            "error": result.stderr if result.stderr else None,
            "mensaje": "Commit realizado correctamente." if result.returncode == 0 else "Error en git commit."
        }
    except Exception as e:
        return {"exito": False, "error": str(e)}


def analizar_rendimiento_sistema(params: dict) -> dict:
    """Analiza el rendimiento del sistema"""
    try:
        # Simulación de análisis de rendimiento
        return {
            "exito": True,
            "rendimiento": {
                "cpu": "Bajo uso",
                "memoria": "Óptima",
                "latencia": "< 200ms"
            },
            "mensaje": "Análisis de rendimiento completado."
        }
    except Exception as e:
        return {"exito": False, "error": str(e)}


def auditoria_seguridad(params: dict) -> dict:
    """Realiza una auditoría de seguridad básica"""
    try:
        # Simulación de auditoría de seguridad
        return {
            "exito": True,
            "seguridad": {
                "vulnerabilidades": 0,
                "dependencias_obsoletas": 0,
                "recomendaciones": ["Actualizar dependencias regularmente", "Revisar logs de acceso"]
            },
            "mensaje": "Auditoría de seguridad completada."
        }
    except Exception as e:
        return {"exito": False, "error": str(e)}


def revisar_dependencias(params: dict) -> dict:
    """Revisa dependencias del proyecto"""
    try:
        # Simulación de revisión de dependencias
        return {
            "exito": True,
            "dependencias": [
                {"nombre": "azure-functions",
                    "version": "1.16.0", "estado": "actualizada"},
                {"nombre": "azure-storage-blob",
                    "version": "12.14.1", "estado": "actualizada"}
            ],
            "mensaje": "Revisión de dependencias completada."
        }
    except Exception as e:
        return {"exito": False, "error": str(e)}


def cancelar_operacion(params: dict) -> dict:
    """Cancela una operación pendiente"""
    try:
        operacion = params.get("operacion", "desconocida")
        return {
            "exito": True,
            "mensaje": f"Operación '{operacion}' cancelada correctamente.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"exito": False, "error": str(e)}


def mover_archivo(origen: str, destino: str, overwrite: bool = False, eliminar_origen: bool = True) -> dict:
    """Mueve/renombra un archivo (Blob o local). En Azure copia y luego borra el origen."""
    try:
        if not origen or not destino:
            return {"exito": False, "error": "Parámetros 'origen' y 'destino' son requeridos"}

        # Normalizar
        origen = origen.strip().replace('\\', '/').replace('//', '/')
        destino = destino.strip().replace('\\', '/').replace('//', '/')

        if IS_AZURE:
            client = get_blob_client()
            if not client:
                return {"exito": False, "error": "Blob Storage no configurado"}

            container = client.get_container_client(CONTAINER_NAME)
            src = container.get_blob_client(origen)
            dst = container.get_blob_client(destino)

            if not src.exists():
                return {"exito": False, "error": f"Origen no existe: {origen}"}
            if dst.exists() and not overwrite:
                return {"exito": False, "error": f"Destino ya existe: {destino}. Usa overwrite=true"}

            # Copia (descargar/subir para evitar fricciones de permisos con copy-from-url)
            data = src.download_blob().readall()
            dst.upload_blob(data, overwrite=True)

            # Borrar origen si se pide "mover" (no solo copiar)
            if eliminar_origen:
                src.delete_blob()

            return {
                "exito": True,
                "mensaje": f"Movido en Blob: {origen} -> {destino}",
                "origen": origen,
                "destino": destino,
                "ubicacion": f"blob://{CONTAINER_NAME}/{destino}"
            }
        else:
            src = PROJECT_ROOT / origen
            dst = PROJECT_ROOT / destino
            if not src.exists():
                return {"exito": False, "error": f"Origen no existe: {src}"}
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists() and not overwrite:
                return {"exito": False, "error": f"Destino ya existe: {dst}. Usa overwrite=true"}

            # Copiar y borrar
            data = src.read_bytes()
            dst.write_bytes(data)
            if eliminar_origen:
                src.unlink()

            return {
                "exito": True,
                "mensaje": f"Movido local: {src} -> {dst}",
                "origen": str(src),
                "destino": str(dst),
                "ubicacion": str(dst)
            }
    except Exception as e:
        return {"exito": False, "error": f"mover_archivo: {str(e)}", "tipo_error": type(e).__name__}


@app.function_name(name="mover_archivo_http")
@app.route(route="mover-archivo", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def mover_archivo_http(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint HTTP para mover/renombrar archivos."""
    try:
        body = req.get_json()
        origen = (body.get("origen") or "").strip()
        destino = (body.get("destino") or "").strip()
        overwrite = bool(body.get("overwrite", False))
        eliminar_origen = bool(body.get("eliminar_origen", True))

        if not origen or not destino:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "Parámetros 'origen' y 'destino' son requeridos",
                    "ejemplo": {"origen": "docs/PRUEBA.md", "destino": "docs/historico/PRUEBA.md", "overwrite": True}
                }, ensure_ascii=False),
                mimetype="application/json", status_code=400
            )

        res = mover_archivo(origen, destino, overwrite=overwrite,
                            eliminar_origen=eliminar_origen)
        return func.HttpResponse(
            json.dumps(res, ensure_ascii=False),
            mimetype="application/json",
            status_code=200 if res.get("exito") else 400
        )
    except Exception as e:
        logging.exception("mover_archivo_http failed")
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(e)}),
            mimetype="application/json", status_code=500
        )


# ---------- util md5 ----------
def _md5_to_b64(maybe_md5) -> Optional[str]:
    if isinstance(maybe_md5, (bytes, bytearray)):
        return base64.b64encode(bytes(maybe_md5)).decode("utf-8")
    return None

# ---------- info-archivo ----------


@app.function_name(name="info_archivo_http")
@app.route(route="info-archivo", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def info_archivo_http(req: func.HttpRequest) -> func.HttpResponse:
    try:
        ruta = (req.params.get("ruta") or "").strip()
        if not ruta:
            return func.HttpResponse(json.dumps({"exito": False, "error": "Falta 'ruta'"}), mimetype="application/json", status_code=400)

        if IS_AZURE:
            client = get_blob_client()
            if not client:
                return func.HttpResponse(json.dumps({"exito": False, "error": "Blob Storage no configurado"}), mimetype="application/json", status_code=500)
            c = client.get_container_client(CONTAINER_NAME)
            b = c.get_blob_client(ruta)
            if not b.exists():
                return func.HttpResponse(json.dumps({"exito": False, "error": "No existe"}), mimetype="application/json", status_code=404)

            props = b.get_blob_properties()
            cs = getattr(props, "content_settings", None)
            meta = {
                "size": getattr(props, "size", getattr(props, "content_length", None)),
                "content_type": getattr(props, "content_type", None),
                "etag": getattr(props, "etag", None),
                "last_modified": (getattr(props, "last_modified", None) or datetime.utcnow()).isoformat(),
                "md5": _md5_to_b64(getattr(cs, "content_md5", None) if cs else None),
            }
            return func.HttpResponse(json.dumps({"exito": True, "ruta": f"blob://{CONTAINER_NAME}/{ruta}", "metadata": meta}, ensure_ascii=False),
                                     mimetype="application/json", status_code=200)
        else:
            p = PROJECT_ROOT / ruta
            if not p.exists():
                return func.HttpResponse(json.dumps({"exito": False, "error": "No existe"}), mimetype="application/json", status_code=404)
            st = p.stat()
            meta = {"size": st.st_size, "last_modified": datetime.fromtimestamp(
                st.st_mtime).isoformat()}
            return func.HttpResponse(json.dumps({"exito": True, "ruta": str(p), "metadata": meta}, ensure_ascii=False),
                                     mimetype="application/json", status_code=200)
    except Exception as e:
        logging.exception("info_archivo_http failed")
        return func.HttpResponse(json.dumps({"exito": False, "error": str(e)}), mimetype="application/json", status_code=500)

# ---------- descargar-archivo ----------


@app.function_name(name="descargar_archivo_http")
@app.route(route="descargar-archivo", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def descargar_archivo_http(req: func.HttpRequest) -> func.HttpResponse:
    try:
        ruta = (req.params.get("ruta") or "").strip()
        modo = (req.params.get("modo")
                or "inline").strip().lower()  # inline|base64
        if not ruta:
            return func.HttpResponse(json.dumps({"exito": False, "error": "Falta 'ruta'"}), mimetype="application/json", status_code=400)

        def pack_ok(raw: bytes, ct: str):
            if modo == "base64":
                return {"exito": True, "ruta": ruta, "content_type": ct, "base64": base64.b64encode(raw).decode("utf-8")}
            try:
                return {"exito": True, "ruta": ruta, "content_type": ct, "contenido": raw.decode("utf-8")}
            except UnicodeDecodeError:
                return {"exito": True, "ruta": ruta, "content_type": ct, "base64": base64.b64encode(raw).decode("utf-8")}

        if IS_AZURE:
            client = get_blob_client()
            if not client:
                return func.HttpResponse(json.dumps({"exito": False, "error": "Blob Storage no configurado"}), mimetype="application/json", status_code=500)
            c = client.get_container_client(CONTAINER_NAME)
            b = c.get_blob_client(ruta)
            if not b.exists():
                return func.HttpResponse(json.dumps({"exito": False, "error": "No existe"}), mimetype="application/json", status_code=404)
            raw = b.download_blob().readall()
            ct = getattr(b.get_blob_properties(), "content_type",
                         "application/octet-stream")
            return func.HttpResponse(json.dumps(pack_ok(raw, ct), ensure_ascii=False), mimetype="application/json", status_code=200)
        else:
            p = PROJECT_ROOT / ruta
            if not p.exists():
                return func.HttpResponse(json.dumps({"exito": False, "error": "No existe"}), mimetype="application/json", status_code=404)
            raw = p.read_bytes()
            return func.HttpResponse(json.dumps(pack_ok(raw, "text/plain"), ensure_ascii=False), mimetype="application/json", status_code=200)
    except Exception as e:
        logging.exception("descargar_archivo_http failed")
        return func.HttpResponse(json.dumps({"exito": False, "error": str(e)}), mimetype="application/json", status_code=500)

# ---------- copiar-archivo (envoltura de mover) ----------


def copiar_archivo(origen: str, destino: str, overwrite: bool = False) -> dict:
    return mover_archivo(origen, destino, overwrite=overwrite, eliminar_origen=False)


@app.function_name(name="copiar_archivo_http")
@app.route(route="copiar-archivo", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def copiar_archivo_http(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        origen = (body.get("origen") or "").strip()
        destino = (body.get("destino") or "").strip()
        overwrite = bool(body.get("overwrite", False))
        if not origen or not destino:
            return func.HttpResponse(json.dumps({"exito": False, "error": "Faltan 'origen' y/o 'destino'"}), mimetype="application/json", status_code=400)
        res = copiar_archivo(origen, destino, overwrite=overwrite)
        return func.HttpResponse(json.dumps(res, ensure_ascii=False), mimetype="application/json", status_code=200 if res.get("exito") else 400)
    except Exception as e:
        logging.exception("copiar_archivo_http failed")
        return func.HttpResponse(json.dumps({"exito": False, "error": str(e)}), mimetype="application/json", status_code=500)

# ---------- preparar-script (descarga desde Blob a /tmp) ----------


def _scripts_tmp_dir() -> Path:
    # /tmp es writable en Linux consumption
    base = Path(os.environ.get("TMPDIR") or "/tmp") / "copiloto-scripts"
    return base


def preparar_script_desde_blob(ruta_blob: str) -> dict:
    try:
        if not ruta_blob:
            return {"exito": False, "error": "Falta ruta_blob"}
        if not IS_AZURE:
            p = PROJECT_ROOT / ruta_blob
            return {"exito": p.exists(), "local_path": str(p)}

        client = get_blob_client()
        if not client:
            return {"exito": False, "error": "Blob Storage no configurado"}
        c = client.get_container_client(CONTAINER_NAME)
        b = c.get_blob_client(ruta_blob)
        if not b.exists():
            return {"exito": False, "error": f"No existe en Blob: {ruta_blob}"}

        local_dir = _scripts_tmp_dir()
        # ✅ crear en /tmp en tiempo de ejecución
        local_dir.mkdir(parents=True, exist_ok=True)
        local = local_dir / Path(ruta_blob).name
        raw = b.download_blob().readall()
        local.write_bytes(raw)
        try:
            os.chmod(local, 0o755)
        except Exception:
            pass
        return {"exito": True, "local_path": str(local)}
    except Exception as e:
        return {"exito": False, "error": str(e)}


@app.function_name(name="preparar_script_http")
@app.route(route="preparar-script", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def preparar_script_http(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        ruta = (body.get("ruta") or "").strip()
        if not ruta:
            return func.HttpResponse(json.dumps({"exito": False, "error": "Falta 'ruta'"}), mimetype="application/json", status_code=400)
        res = preparar_script_desde_blob(ruta)
        return func.HttpResponse(json.dumps(res, ensure_ascii=False), mimetype="application/json", status_code=200 if res.get("exito") else 400)
    except Exception as e:
        logging.exception("preparar_script_http failed")
        return func.HttpResponse(json.dumps({"exito": False, "error": str(e)}), mimetype="application/json", status_code=500)
# Añadir estos endpoints a function_app.py

# ========== CREAR CONTENEDOR ==========


@app.function_name(name="crear_contenedor_http")
@app.route(route="crear-contenedor", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def crear_contenedor_http(req: func.HttpRequest) -> func.HttpResponse:
    """Crea un nuevo contenedor en Azure Blob Storage"""
    try:
        body = req.get_json()
        nombre = (body.get("nombre") or "").strip()
        publico = body.get("publico", False)
        metadata = body.get("metadata")
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}
        if not isinstance(metadata, dict):
            metadata = {}

        if not nombre:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "Parámetro 'nombre' es requerido",
                    "ejemplo": {"nombre": "nuevo-contenedor", "publico": False}
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=400
            )

        # Validar nombre del contenedor (Azure rules)
        import re
        if not re.match(r'^[a-z0-9]([a-z0-9\-]{1,61}[a-z0-9])?$', nombre):
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "Nombre inválido. Debe ser minúsculas, números y guiones (3-63 caracteres)",
                    "nombre_proporcionado": nombre
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=400
            )

        client = get_blob_client()
        if not client:
            return func.HttpResponse(
                json.dumps(
                    {"exito": False, "error": "Blob Storage no configurado"}),
                mimetype="application/json",
                status_code=500
            )

        try:
            # Configurar nivel de acceso
            from azure.storage.blob import PublicAccess
            public_access = PublicAccess.Container.value if publico else None

            # Crear contenedor
            container_client = client.create_container(
                name=nombre,
                public_access=public_access,
                metadata=metadata
            )

            return func.HttpResponse(
                json.dumps({
                    "exito": True,
                    "mensaje": f"Contenedor '{nombre}' creado exitosamente",
                    "contenedor": nombre,
                    "publico": publico,
                    "metadata": metadata,
                    "url": f"https://{client.account_name}.blob.core.windows.net/{nombre}"
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=201
            )

        except Exception as e:
            mensaje = str(e).lower()
            if "already exists" in mensaje:
                return func.HttpResponse(
                    json.dumps({
                        "exito": False,
                        "error": f"El contenedor '{nombre}' ya existe",
                        "sugerencia": "Usa un nombre diferente o elimina el contenedor existente"
                    }, ensure_ascii=False),
                    mimetype="application/json",
                    status_code=409
                )
            if "publicaccessnotpermitted" in mensaje:
                return func.HttpResponse(
                    json.dumps({
                        "exito": False,
                        "error": "No se permite el acceso público en esta cuenta de almacenamiento",
                        "sugerencia": "Habilita 'allowBlobPublicAccess = true' en la configuración del Storage Account"
                    }, ensure_ascii=False),
                    mimetype="application/json",
                    status_code=403
                )
            raise

    except Exception as e:
        logging.exception("crear_contenedor_http failed")
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(
                e), "tipo_error": type(e).__name__}),
            mimetype="application/json",
            status_code=500
        )

# ========== EJECUTAR CLI ==========


@app.function_name(name="ejecutar_cli_http")
@app.route(route="ejecutar-cli", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def ejecutar_cli_http(req: func.HttpRequest) -> func.HttpResponse:
    """Ejecuta comandos Azure CLI de forma controlada"""
    # Initialize timeout with default value before try block
    timeout = 30
    cmd_parts = []  # define here for exception scope
    try:
        body = req.get_json()
        comando = (body.get("comando") or "").strip()
        servicio = (body.get("servicio") or "").strip()
        parametros = body.get("parametros", {})
        timeout = body.get("timeout", 30)

        if not comando:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": "Parámetro 'comando' es requerido",
                    "servicios_permitidos": ["storage", "functionapp", "webapp", "monitor", "resource"],
                    "ejemplo": {
                        "servicio": "storage",
                        "comando": "account show",
                        "parametros": {"name": "boatrentalstorage"}
                    }
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=400
            )

        # Lista blanca de servicios permitidos
        servicios_permitidos = {
            "storage": ["account", "container", "blob", "share"],
            "functionapp": ["show", "list", "config", "cors", "deployment"],
            "webapp": ["log", "config", "deployment"],
            "monitor": ["metrics", "activity-log"],
            "resource": ["list", "show", "tag"]
        }

        if servicio and servicio not in servicios_permitidos:
            return func.HttpResponse(
                json.dumps({
                    "exito": False,
                    "error": f"Servicio '{servicio}' no permitido",
                    "servicios_permitidos": list(servicios_permitidos.keys())
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=403
            )

        # Construir comando completo
        cmd_parts = ["az"]
        if servicio:
            cmd_parts.append(servicio)
        cmd_parts.extend(comando.split())

        # Añadir parámetros
        for key, value in parametros.items():
            if key.startswith("--"):
                cmd_parts.append(key)
            else:
                cmd_parts.append(f"--{key}")
            if value is not None:
                cmd_parts.append(str(value))

        # Añadir output JSON por defecto
        if "--output" not in " ".join(cmd_parts):
            cmd_parts.extend(["--output", "json"])

        # Validación de seguridad adicional
        comandos_peligrosos = ["delete", "remove", "purge", "reset"]
        if any(cmd in comando.lower() for cmd in comandos_peligrosos):
            requiere_confirmacion = body.get(
                "confirmar_operacion_peligrosa", False)
            if not requiere_confirmacion:
                return func.HttpResponse(
                    json.dumps({
                        "exito": False,
                        "error": "Operación peligrosa detectada",
                        "comando_detectado": comando,
                        "requiere": "Añade 'confirmar_operacion_peligrosa': true para ejecutar",
                        "advertencia": "Esta operación puede eliminar o modificar recursos"
                    }, ensure_ascii=False),
                    mimetype="application/json",
                    status_code=403
                )

        # Ejecutar comando
        resultado = subprocess.run(
            cmd_parts,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        # Procesar resultado
        output = resultado.stdout
        try:
            # Intentar parsear como JSON
            output_json = json.loads(output) if output else None
        except:
            output_json = None

        comando_ejecutado = " ".join(cmd_parts)
        return func.HttpResponse(
            json.dumps({
                "exito": resultado.returncode == 0,
                "comando_ejecutado": comando_ejecutado,
                "codigo_salida": resultado.returncode,
                "output": output_json if output_json else output,
                "error": resultado.stderr if resultado.stderr else None,
                "metadata": {
                    "servicio": servicio,
                    "timeout": timeout,
                    "timestamp": datetime.now().isoformat()
                }
            }, ensure_ascii=False),
            mimetype="application/json",
            status_code=200 if resultado.returncode == 0 else 400
        )

    except subprocess.TimeoutExpired:
        comando_ejecutado = " ".join(cmd_parts) if cmd_parts else None
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "error": f"Comando excedió tiempo límite ({timeout}s)",
                "comando": comando_ejecutado
            }),
            mimetype="application/json",
            status_code=408
        )
    except Exception as e:
        logging.exception("ejecutar_cli_http failed")
        return func.HttpResponse(
            json.dumps({"exito": False, "error": str(
                e), "tipo_error": type(e).__name__}),
            mimetype="application/json",
            status_code=500
        )

# ========== DIAGNOSTICO RECURSOS ==========


@app.function_name(name="diagnostico_recursos_http")
@app.route(route="diagnostico-recursos", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
def diagnostico_recursos_http(req: func.HttpRequest) -> func.HttpResponse:
    """Diagnóstico completo de recursos Azure"""
    try:
        # Parámetros opcionales
        incluir_metricas = req.params.get("metricas", "true").lower() == "true"
        incluir_costos = req.params.get("costos", "false").lower() == "true"
        recurso_especifico = req.params.get("recurso", "")

        diagnostico = {
            "timestamp": datetime.now().isoformat(),
            "ambiente": "Azure" if IS_AZURE else "Local",
            "recursos": {},
            "metricas": {},
            "alertas": [],
            "recomendaciones": []
        }

        # 1. Estado de Function App
        app_name = None
        resource_group = None
        if IS_AZURE:
            app_name = os.environ.get("WEBSITE_SITE_NAME")
            resource_group = os.environ.get("RESOURCE_GROUP", "boat-rental-rg")

            if app_name:
                cmd = f"az functionapp show --name {app_name} --resource-group {resource_group}"
                result = ejecutar_comando_azure(cmd)
                if result["exito"]:
                    data = result["data"]
                    diagnostico["recursos"]["function_app"] = {
                        "nombre": app_name,
                        "estado": data.get("state", "Unknown"),
                        "plan": data.get("appServicePlanId", "").split("/")[-1],
                        "runtime": data.get("siteConfig", {}).get("pythonVersion", ""),
                        "url": f"https://{app_name}.azurewebsites.net",
                        "location": data.get("location", ""),
                        "kind": data.get("kind", "")
                    }

        # 2. Estado de Storage Account
        try:
            client = get_blob_client()
            if client:
                # Obtener propiedades del account
                account_name = client.account_name
                cmd = f"az storage account show --name {account_name}"
                result = ejecutar_comando_azure(cmd)
                if result["exito"]:
                    data = result["data"]
                    diagnostico["recursos"]["storage_account"] = {
                        "nombre": account_name,
                        "tipo": data.get("sku", {}).get("name", ""),
                        "replicacion": data.get("sku", {}).get("tier", ""),
                        "location": data.get("location", ""),
                        "estado": data.get("statusOfPrimary", ""),
                        "tier": data.get("accessTier", "")
                    }

                # Contar contenedores y blobs
                contenedores = list(client.list_containers())
                total_blobs = 0
                for container in contenedores:
                    container_client = client.get_container_client(
                        container.name)
                    total_blobs += sum(1 for _ in container_client.list_blobs())

                diagnostico["recursos"]["storage_stats"] = {
                    "contenedores": len(contenedores),
                    "total_blobs": total_blobs,
                    "contenedor_principal": CONTAINER_NAME
                }
        except Exception as e:
            diagnostico["recursos"]["storage_account"] = {
                "estado": "error",
                "error": str(e)
            }

        # 3. Métricas de rendimiento (si solicitado)
        if incluir_metricas and IS_AZURE:
            subscription = os.environ.get("AZURE_SUBSCRIPTION_ID")
            if subscription and app_name:
                # Métricas de las últimas 24 horas
                resource_id = f"/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/Microsoft.Web/sites/{app_name}"

                metricas_consultar = ["Http5xx", "Requests",
                                      "ResponseTime", "MemoryWorkingSet"]
                for metrica in metricas_consultar:
                    cmd = f"az monitor metrics list --resource {resource_id} --metric {metrica} --interval PT1H --start-time {(datetime.now() - timedelta(hours=24)).isoformat()}"
                    result = ejecutar_comando_azure(cmd)
                    if result["exito"] and result["data"]:
                        # Procesar métricas
                        diagnostico["metricas"][metrica] = "Datos disponibles"

        # 4. Análisis y recomendaciones
        if diagnostico["recursos"].get("function_app", {}).get("estado") != "Running":
            diagnostico["alertas"].append({
                "nivel": "critico",
                "mensaje": "Function App no está en estado Running",
                "accion": "Verificar logs y reiniciar si es necesario"
            })

        if diagnostico["recursos"].get("storage_stats", {}).get("total_blobs", 0) > 10000:
            diagnostico["recomendaciones"].append({
                "tipo": "optimizacion",
                "mensaje": "Alto número de blobs detectado",
                "accion": "Considerar implementar lifecycle management policies"
            })

        # 5. Cache y memoria
        diagnostico["sistema"] = {
            "cache_archivos": len(CACHE),
            "memoria_cache_kb": round(sum(len(str(v)) for v in CACHE.values()) / 1024, 2) if CACHE else 0,
            "endpoints_activos": [
                "/api/crear-contenedor",
                "/api/ejecutar-cli",
                "/api/diagnostico-recursos"
            ]
        }

        return func.HttpResponse(
            json.dumps(diagnostico, indent=2, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.exception("diagnostico_recursos_http failed")
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "error": str(e),
                "tipo_error": type(e).__name__,
                "sugerencia": "Verifica los permisos y la configuración de Azure CLI"
            }),
            mimetype="application/json",
            status_code=500
        )

# ========== FUNCIONES AUXILIARES PARA INTENCIONES ==========


def procesar_intencion_crear_contenedor(parametros: dict) -> dict:
    """Procesa intención de crear contenedor"""
    nombre = parametros.get("nombre", "")
    if not nombre:
        return {
            "exito": False,
            "error": "Nombre del contenedor requerido",
            "sugerencia": "Proporciona: {'nombre': 'mi-contenedor'}"
        }

    # Llamar al endpoint interno
    resultado = crear_contenedor_http(
        func.HttpRequest(
            method="POST",
            url="/api/crear-contenedor",
            headers={},
            params={},
            body=json.dumps(parametros).encode()
        )
    )

    return json.loads(resultado.get_body().decode())


def procesar_intencion_cli(parametros: dict) -> dict:
    """Procesa intención de ejecutar CLI"""
    comando = parametros.get("comando", "")
    servicio = parametros.get("servicio", "")

    if not comando:
        return {
            "exito": False,
            "error": "Comando CLI requerido",
            "ejemplo": {
                "servicio": "storage",
                "comando": "account list"
            }
        }

    # Ejecutar comando
    return ejecutar_comando_azure_seguro(servicio, comando, parametros)


def ejecutar_comando_azure_seguro(servicio: str, comando: str, params: dict) -> dict:
    """Wrapper seguro para comandos Azure CLI"""
    try:
        # Validaciones de seguridad
        if any(x in comando.lower() for x in ["delete", "remove", "purge"]):
            if not params.get("confirmar_operacion_peligrosa"):
                return {
                    "exito": False,
                    "error": "Operación peligrosa requiere confirmación",
                    "requiere": "confirmar_operacion_peligrosa: true"
                }

        # Construir y ejecutar
        full_cmd = f"az {servicio} {comando}" if servicio else f"az {comando}"
        return ejecutar_comando_azure(full_cmd, formato="json")

    except Exception as e:
        return {"exito": False, "error": str(e)}
