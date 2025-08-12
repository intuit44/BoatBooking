from typing import Optional
import azure.functions as func
import logging
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
import base64
import re
import subprocess
import asyncio
from typing import Dict, List, Any, Optional, Union

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Configuración adaptativa
IS_AZURE = os.environ.get("WEBSITE_INSTANCE_ID") is not None

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
BLOB_CLIENT = None

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


def get_blob_client():
    """Obtiene el cliente de Blob Storage con mejor manejo de errores"""
    global BLOB_CLIENT
    if not BLOB_CLIENT and STORAGE_CONNECTION_STRING:
        try:
            BLOB_CLIENT = BlobServiceClient.from_connection_string(
                STORAGE_CONNECTION_STRING)
            # Verificar que el container existe
            container_client = BLOB_CLIENT.get_container_client(CONTAINER_NAME)
            if not container_client.exists():
                logging.warning(f"Container {CONTAINER_NAME} no existe")
                return None
        except Exception as e:
            logging.error(f"Error conectando a Blob Storage: {str(e)}")
            return None
    return BLOB_CLIENT


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

    # Procesar intenciones existentes primero
    resultado = procesar_intencion_semantica(intencion, parametros)

    # Nuevas intenciones
    partes = intencion.split(':')
    comando = partes[0].lower()
    contexto = partes[1] if len(partes) > 1 else ""

    if comando == "crear" and contexto == "archivo":
        ruta = parametros.get("ruta", "")
        contenido = parametros.get("contenido", "")
        if not ruta:
            return {
                "exito": False,
                "error": "Parámetro 'ruta' es requerido para crear archivo"
            }
        return crear_archivo(ruta, contenido)

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

    return resultado


def router_universal(intencion: str, contexto: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Enruta intenciones a servicios apropiados"""

    if contexto is None:
        contexto = {}

    routing_rules = {
        "diagnosticar": "copiloto",
        "generar:codigo": "codegpt",
        "generar:test": "copiloto",
        "analizar:tsx": "agent975",
        "crear:agente": "ai_foundry",
        "deploy": "azure_devops",
        "monitor": "app_insights"
    }

    # Encontrar la mejor coincidencia
    for patron, servicio in routing_rules.items():
        if intencion.startswith(patron):
            return {
                "servicio": servicio,
                "intencion_original": intencion,
                "accion": "delegar",
                "contexto": contexto
            }

    # Por defecto, procesar localmente
    return {
        "servicio": "copiloto",
        "intencion_original": intencion,
        "accion": "procesar",
        "contexto": contexto
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
        "blob_storage": bool(STORAGE_CONNECTION_STRING),
        "openai_configurado": bool(os.environ.get("AZURE_OPENAI_KEY")),
        "app_insights": bool(os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")),
        "ambiente": "Azure" if IS_AZURE else "Local"
    }

    # 2. Verificar conectividad Blob Storage
    if STORAGE_CONNECTION_STRING:
        client = get_blob_client()
        if client:
            try:
                container_client = client.get_container_client(CONTAINER_NAME)
                blob_count = sum(1 for _ in container_client.list_blobs())
                diagnostico["checks"]["blob_storage_detalles"] = {
                    "conectado": True,
                    "container": CONTAINER_NAME,
                    "archivos": blob_count
                }
            except Exception as e:
                diagnostico["checks"]["blob_storage_detalles"] = {
                    "conectado": False,
                    "error": str(e)
                }
                diagnostico["recomendaciones"].append(
                    "Verificar permisos de Blob Storage")

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
    if not diagnostico["checks"]["blob_storage_detalles"].get("conectado"):
        diagnostico["recomendaciones"].append(
            "Sincronizar archivos con Blob Storage: ./sync_to_blob.ps1")

    if diagnostico["metricas"]["cache"]["archivos_en_cache"] > 100:
        diagnostico["recomendaciones"].append(
            "Considerar limpiar caché para optimizar memoria")

    return diagnostico


def generar_dashboard_insights() -> dict:
    """Genera un dashboard con insights del proyecto"""
    dashboard = {
        "titulo": "Dashboard Copiloto Semántico",
        "generado": datetime.now().isoformat(),
        "secciones": {}
    }

    # 1. Estado del Sistema
    dashboard["secciones"]["estado_sistema"] = {
        "function_app": os.environ.get("WEBSITE_SITE_NAME", "local"),
        "ambiente": "Azure" if IS_AZURE else "Local",
        "version": "2.0-orchestrator",
        "uptime": "Activo"
    }

    # 2. Uso de Recursos
    if IS_AZURE and os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"):
        # Aquí podrías integrar con Application Insights SDK
        dashboard["secciones"]["metricas"] = {
            "requests_totales": "Pendiente integración App Insights",
            "errores_24h": 0,
            "latencia_promedio": "< 500ms"
        }

    # 3. Análisis de Código
    archivos_analizados = []
    if STORAGE_CONNECTION_STRING:
        client = get_blob_client()
        if client:
            container_client = client.get_container_client(CONTAINER_NAME)
            for blob in container_client.list_blobs():
                if blob.name.endswith(('.py', '.js', '.ts')):
                    archivos_analizados.append({
                        "archivo": blob.name,
                        "tamaño": blob.size,
                        "modificado": str(blob.last_modified)
                    })

    dashboard["secciones"]["codigo"] = {
        "archivos_totales": len(archivos_analizados),
        "ultimos_modificados": sorted(archivos_analizados, key=lambda x: x["modificado"], reverse=True)[:5]
    }

    # 4. Sugerencias Proactivas
    dashboard["secciones"]["sugerencias"] = generar_sugerencias_proactivas()

    return dashboard


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
                        "Considera usar plan Premium para mejor performance"
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
@app.route(route="copiloto", auth_level=func.AuthLevel.FUNCTION)
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


@app.function_name(name="status")
@app.route(route="status")
def status(req: func.HttpRequest) -> func.HttpResponse:
    """Status endpoint mejorado con información semántica"""

    # Verificar conexión a Blob Storage
    blob_status = "desconectado"
    blob_detalles = {}

    if STORAGE_CONNECTION_STRING:
        client = get_blob_client()
        if client:
            try:
                container_client = client.get_container_client(CONTAINER_NAME)
                if container_client.exists():
                    blob_status = "conectado"
                    # Contar archivos
                    total_blobs = sum(1 for _ in container_client.list_blobs())
                    blob_detalles = {
                        "container": CONTAINER_NAME,
                        "total_archivos": total_blobs,
                        "conexion": "activa"
                    }
                else:
                    blob_status = "container_no_existe"
                    blob_detalles = {
                        "error": f"Container '{CONTAINER_NAME}' no encontrado"}
            except Exception as e:
                blob_status = "error"
                blob_detalles = {"error": str(e)}

    estado = {
        "copiloto": "activo",
        "version": "2.0-semantic",
        "timestamp": datetime.now().isoformat(),
        "capacidades": {
            "semanticas": list(SEMANTIC_CAPABILITIES.keys()),
            "total": len(SEMANTIC_CAPABILITIES)
        },
        "ambiente": {
            "tipo": "Azure" if IS_AZURE else "Local",
            "detalles": {
                "project_root": str(PROJECT_ROOT) if not IS_AZURE else "/home/site/wwwroot",
                "python_version": os.environ.get("PYTHON_VERSION", "3.9"),
                "function_app": os.environ.get("WEBSITE_SITE_NAME", "local")
            }
        },
        "storage": {
            "blob_storage": {
                "estado": blob_status,
                "detalles": blob_detalles,
                "connection_string_configurado": bool(STORAGE_CONNECTION_STRING)
            },
            "cache": {
                "archivos_en_cache": len(CACHE),
                "memoria_usada": sum(len(str(v)) for v in CACHE.values()) if CACHE else 0
            }
        },
        "endpoints": {
            "copiloto": "/api/copiloto",
            "ejecutar": "/api/ejecutar",
            "status": "/api/status"
        },
        "listo_para_agentes": True,
        "metadata": {
            "api_version": "2.0",
            "semantic_engine": "activo",
            "ultima_actualizacion": "2025-08-05"
        }
    }

    return func.HttpResponse(
        json.dumps(estado, indent=2, ensure_ascii=False),
        mimetype="application/json"
    )


@app.function_name(name="ejecutar")
@app.route(route="ejecutar", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def ejecutar(req: func.HttpRequest) -> func.HttpResponse:
    """Endpoint mejorado para ejecución de comandos complejos"""
    logging.info('🚀 Endpoint ejecutar (orquestador) activado')

    try:
        req_body = req.get_json()

        # Extraer parámetros con valores por defecto
        intencion = req_body.get('intencion', '')
        # Siempre será dict, nunca None
        parametros = req_body.get('parametros') or {}
        contexto = req_body.get('contexto', {})
        modo = req_body.get('modo', 'normal')

        # Validar que tenemos una intención
        if not intencion:
            return func.HttpResponse(
                json.dumps({
                    "error": "Parámetro 'intencion' es requerido",
                    "ejemplo": {
                        "intencion": "dashboard",
                        "parametros": {},
                        "modo": "normal"
                    }
                }, indent=2),
                mimetype="application/json",
                status_code=400
            )

        # Procesar según el modo
        if modo == "guiado":
            resultado = generar_guia_contextual(intencion, parametros)
        elif modo == "orquestador":
            resultado = orquestar_flujo_trabajo(intencion, parametros)
        else:
            # Usar la nueva función con tipado correcto
            resultado = procesar_intencion_semantica(
                intencion, parametros)

        # Enriquecer respuesta
        resultado['metadata'] = {
            'timestamp': datetime.now().isoformat(),
            'modo': modo,
            'intencion_procesada': intencion,
            'ambiente': 'Azure' if IS_AZURE else 'Local',
            'copiloto_version': '2.0-orchestrator'
        }

        # Agregar contexto de ayuda si falló
        if not resultado.get('exito', True):
            resultado['ayuda'] = {
                'ejemplos': [
                    {"intencion": "diagnosticar:completo",
                        "descripcion": "Diagnóstico completo del sistema"},
                    {"intencion": "dashboard",
                        "descripcion": "Dashboard con insights"},
                    {"intencion": "guia:configurar_blob",
                        "descripcion": "Guía paso a paso"},
                    {"intencion": "ejecutar:azure", "parametros": {
                        "comando": "az functionapp list"}}
                ],
                'modos': ["normal", "guiado", "orquestador"]
            }

        return func.HttpResponse(
            json.dumps(resultado, indent=2, ensure_ascii=False),
            mimetype="application/json"
        )

    except ValueError as e:
        return func.HttpResponse(
            json.dumps({
                "error": "JSON inválido",
                "detalles": str(e),
                "ejemplo": {
                    "intencion": "dashboard",
                    "parametros": {},
                    "modo": "guiado"
                }
            }, indent=2),
            mimetype="application/json",
            status_code=400
        )
    except Exception as e:
        logging.error(f"Error en ejecutar: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "tipo": type(e).__name__,
                "sugerencia": "Verifica el formato de la petición"
            }, indent=2),
            mimetype="application/json",
            status_code=500
        )

# Agregar una función health check mejorada


@app.function_name(name="invocar")
@app.route(route="invocar", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
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


def crear_archivo(ruta: str, contenido: str) -> dict:
    """Crea un nuevo archivo en el proyecto"""
    try:
        if IS_AZURE:
            client = get_blob_client()
            if client:
                container_client = client.get_container_client(CONTAINER_NAME)
                blob_client = container_client.get_blob_client(ruta)
                blob_client.upload_blob(contenido, overwrite=True)
                return {
                    "exito": True,
                    "mensaje": f"Archivo creado en Blob: {ruta}",
                    "ubicacion": f"blob://{CONTAINER_NAME}/{ruta}"
                }
            else:
                return {
                    "exito": False,
                    "error": "No se pudo obtener el cliente de Blob Storage"
                }
        else:
            archivo_path = PROJECT_ROOT / ruta
            archivo_path.parent.mkdir(parents=True, exist_ok=True)
            archivo_path.write_text(contenido, encoding='utf-8')
            return {
                "exito": True,
                "mensaje": f"Archivo creado: {archivo_path}",
                "ubicacion": str(archivo_path)
            }
    except Exception as e:
        return {
            "exito": False,
            "error": str(e)
        }


def modificar_archivo(ruta: str, operacion: str, contenido: str = "", linea: int = -1) -> dict:
    """Modifica un archivo existente"""
    try:
        archivo_actual = leer_archivo_dinamico(ruta)
        if not archivo_actual["exito"]:
            return archivo_actual

        contenido_actual = archivo_actual["contenido"]
        lineas = contenido_actual.split('\n')

        if operacion == "agregar_linea":
            if linea is not None and 0 <= linea <= len(lineas):
                lineas.insert(linea, contenido)
            else:
                lineas.append(contenido)
        elif operacion == "reemplazar_linea":
            if linea is not None and 0 <= linea < len(lineas):
                lineas[linea] = contenido
        elif operacion == "eliminar_linea":
            if linea is not None and 0 <= linea < len(lineas):
                del lineas[linea]
        elif operacion == "buscar_reemplazar":
            params = json.loads(contenido)
            contenido_nuevo = contenido_actual.replace(
                params["buscar"], params["reemplazar"])
            return crear_archivo(ruta, contenido_nuevo)
        contenido_nuevo = '\n'.join(lineas)
        return crear_archivo(ruta, contenido_nuevo)
    except Exception as e:
        return {
            "exito": False,
            "error": str(e),
            "operacion": operacion
        }


def ejecutar_script(nombre_script: str, parametros: list = []) -> dict:
    """Ejecuta un script PowerShell, Bash o Python"""
    try:
        if nombre_script.endswith('.ps1'):
            comando = ['powershell', '-ExecutionPolicy',
                       'Bypass', '-File', nombre_script]
        elif nombre_script.endswith('.sh'):
            comando = ['bash', nombre_script]
        elif nombre_script.endswith('.py'):
            comando = ['python', nombre_script]
        else:
            comando = [nombre_script]
        if parametros:
            comando.extend(parametros)
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(PROJECT_ROOT)
        )
        return {
            "exito": resultado.returncode == 0,
            "stdout": resultado.stdout,
            "stderr": resultado.stderr,
            "codigo_salida": resultado.returncode,
            "comando_ejecutado": ' '.join(comando)
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
            "script": nombre_script
        }


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
