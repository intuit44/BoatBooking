# -*- coding: utf-8 -*-
"""
Herramientas para enriquecer threads guardados en Blob Storage.
Genera resúmenes semánticos y consulta memoria adicional (Cosmos DB).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, cast

from blob_service import BlobService
from services.redis_buffer_service import redis_buffer

# Constantes globales de control de tamaño
MAX_MENSAJE_CHARS = 600
MAX_MENSAJES_THREAD = 20
MAX_RESUMEN_CHARS = 6000


def enriquecer_thread_data(thread_data: Dict[str, Any],
                           mensajes: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Genera un resumen enriquecido del thread combinando:
    - Información del JSON (response_data, metadata, mensajes)
    - Contexto adicional desde Cosmos DB (si hay session_id)
    """
    resumen_partes: List[str] = []
    detalles: Dict[str, Any] = {}
    mensajes = mensajes or []

    thread_id = thread_data.get("id") or thread_data.get("thread_id")
    endpoint = thread_data.get("endpoint") or thread_data.get("ruta")
    session_id = thread_data.get("session_id")

    if thread_id:
        resumen_partes.append(f"🧵 Thread: {thread_id}")
    if endpoint:
        resumen_partes.append(f"Endpoint asociado: {endpoint}")

    response_data = thread_data.get("response_data")
    resumen_resp = _resumir_response_data(response_data, detalles)
    if resumen_resp:
        resumen_partes.append(resumen_resp)

    historial_ctx = _obtener_historial_contexto(session_id)
    if historial_ctx:
        detalles["resumen_corto"] = historial_ctx.get("resumen_corto")
        resumen_partes.append(historial_ctx["resumen_corto"])

    search_ctx = _obtener_ai_search_context(thread_id, response_data)
    if search_ctx:
        detalles["ai_search_resumen"] = search_ctx.get("resumen_corto")
        resumen_partes.append(search_ctx["resumen_corto"])

    # Formatear solo últimos 3 mensajes al final
    mensajes_fmt = _formatear_mensajes(
        mensajes[-3:] if len(mensajes) > 3 else mensajes)
    if mensajes_fmt:
        conversacion = "\n".join(mensajes_fmt)
        resumen_partes.append(
            "\n🗣️ Conversación (últimos 3 mensajes):\n" + conversacion)

    resumen_final = "\n".join(
        resumen_partes) if resumen_partes else "No se encontró contenido interpretable en el thread."
    if len(resumen_final) > MAX_RESUMEN_CHARS:
        resumen_final = resumen_final[:MAX_RESUMEN_CHARS].rstrip() + \
            "\n… (contenido truncado)"

    return {
        "resumen": resumen_final,
        "detalles": detalles,
        "mensajes_formateados": mensajes_fmt
    }


def _resumir_response_data(response_data: Any, detalles: Dict[str, Any]) -> Optional[str]:
    if not isinstance(response_data, dict):
        return None

    exito = response_data.get("exito")
    resumen = response_data.get("resumen") or response_data.get("mensaje")

    # Solo campos útiles en detalles
    if resumen:
        detalles["resumen_corto"] = resumen[:300]

    partes = []
    if exito is True and resumen:
        partes.append(f"✅ {resumen[:400]}")
    elif exito is False:
        error = response_data.get("error") or "Error no especificado"
        partes.append(f"⚠️ {error[:400]}")
    elif resumen:
        partes.append(resumen[:400])

    return "\n".join(partes) if partes else None


def _formatear_mensajes(mensajes: List[Dict[str, Any]]) -> List[str]:
    result = []
    for msg in mensajes:
        if not isinstance(msg, dict):
            continue

        role = msg.get("role", "usuario")
        ts = msg.get("created_at", msg.get("timestamp", ""))

        # Priorizar campos interpretativos
        content = (msg.get("texto_semantico") or
                   msg.get("respuesta_usuario") or
                   msg.get("detalle") or
                   msg.get("contenido", "") or
                   msg.get("content", ""))

        if not isinstance(content, str):
            content = str(content)

        content = content.strip()

        # Excluir líneas con thread_id, rutas o paths
        lines = [l for l in content.split("\n")
                 if not any(x in l.lower() for x in ["thread:", "assistant-", "ruta_blob", "c:\\", "/home/", "blob.core"])]
        content = " ".join(lines).strip()

        # Limitar a 400 caracteres útiles
        if len(content) > 400:
            content = content[:400].rstrip() + "…"

        if content:
            result.append(f"[{role} @ {ts[:19] if ts else 'N/A'}] {content}")

    return result


def _obtener_historial_contexto(session_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not session_id:
        return None

    try:
        from cosmos_memory_direct import consultar_memoria_cosmos_directo

        class MockRequest:
            def __init__(self, s_id: str):
                self.headers = {"Session-ID": s_id, "Agent-ID": "assistant"}
                self.method = "GET"
                self.params = {}

        # Cast the mock to Any to satisfy the expected HttpRequest type for static checkers
        memoria = consultar_memoria_cosmos_directo(
            cast(Any, MockRequest(session_id)))
        if not memoria or not memoria.get("tiene_historial"):
            return None

        resumen = memoria.get("resumen_conversacion") or ""
        total = memoria.get("total_interacciones") or 0
        resumen_corto = f"🧠 Memoria: {total} interacciones. {resumen[:200]}"

        return {"resumen_corto": resumen_corto}
    except Exception as exc:
        logging.debug(
            f"No se pudo recuperar historial para {session_id}: {exc}")
        return None


def _obtener_ai_search_context(thread_id: Optional[str], response_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Consulta Azure AI Search para encontrar registros relacionados con el thread."""
    try:
        from services.azure_search_client import get_search_service

        query_parts: List[str] = []
        if thread_id:
            query_parts.append(thread_id)

        if isinstance(response_data, dict):
            for campo in ("mensaje", "texto_semantico", "error"):
                valor = response_data.get(campo)
                if valor and isinstance(valor, str):
                    query_parts.append(valor[:200])

        query = " ".join(query_parts).strip() or (
            thread_id or "thread historial")

        search_service = get_search_service()
        resultado = search_service.search(query, top=3)
        if not resultado.get("exito"):
            return None

        documentos = resultado.get("documentos") or []
        if not documentos:
            return None

        docs_resumidos = []
        for doc in documentos[:3]:
            if not isinstance(doc, dict):
                continue
            docs_resumidos.append({
                "id": doc.get("id"),
                "timestamp": doc.get("timestamp"),
                "endpoint": doc.get("endpoint") or doc.get("ruta") or doc.get("tipo"),
                "texto": (doc.get("texto_semantico") or doc.get("descripcion") or doc.get("mensaje") or "")[:280]
            })

        if not docs_resumidos:
            return None

        resumen_corto = f"🔎 AI Search: {len(docs_resumidos)} docs encontrados."

        return {"resumen_corto": resumen_corto}

    except Exception as exc:
        logging.debug(
            f"No se pudo consultar AI Search para thread {thread_id}: {exc}")
        return None


def generar_narrativa_contextual(
    session_id: Optional[str],
    thread_id: Optional[str] = None,
    query: str = "",
    fallback_memoria: Optional[Dict[str, Any]] = None,
    use_cache: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Pipeline optimizado: threads + Cosmos + AI Search.
    Retorna máximo 6KB de narrativa contextual, respaldado por Redis.
    """

    def _build_narrativa() -> Optional[Dict[str, Any]]:
        try:
            thread_data, blob_origen = _cargar_thread_desde_blob(
                thread_id, session_id)

            if not thread_data:
                thread_data = {
                    "id": thread_id or session_id or "ctx-auto",
                    "session_id": session_id,
                    "endpoint": "context_pipeline",
                    "response_data": {
                        "mensaje": query or "Contexto solicitado",
                        "resumen": (fallback_memoria or {}).get("resumen_conversacion", "")[:500]
                    }
                }
            else:
                if session_id and not thread_data.get("session_id"):
                    thread_data["session_id"] = session_id

            # Limitar mensajes a MAX_MENSAJES_THREAD
            mensajes_blob = thread_data.get("mensajes", [])
            mensajes = mensajes_blob[-MAX_MENSAJES_THREAD:
                                     ] if isinstance(mensajes_blob, list) else []

            if not mensajes:
                mensajes = _recuperar_mensajes_thread(thread_data.get("id"))
                mensajes = mensajes[-MAX_MENSAJES_THREAD:] if mensajes else []

            enriquecido = enriquecer_thread_data(thread_data, mensajes)
            resumen = (enriquecido or {}).get("resumen")

            if not resumen:
                return None

            # Truncar resumen a MAX_RESUMEN_CHARS
            if len(resumen) > MAX_RESUMEN_CHARS:
                resumen = resumen[:MAX_RESUMEN_CHARS] + "\n... (truncado)"

            # Solo últimos 3 mensajes formateados
            mensajes_fmt = (enriquecido or {}).get(
                "mensajes_formateados", [])[-3:]

            narrativa_payload = {
                "texto": resumen.strip(),
                "detalles": (enriquecido or {}).get("detalles", {}),
                "mensajes": mensajes_fmt,
                "thread_id": thread_data.get("id"),
                "session_id": thread_data.get("session_id"),
                "fuente_blob": blob_origen
            }
            return narrativa_payload
        except Exception as exc:
            logging.warning(f"Error generando narrativa: {exc}")
            return None

    if use_cache:
        narrativa_ctx, cache_hit, latency_ms = redis_buffer.get_or_compute_narrativa(
            session_id=session_id,
            thread_id=thread_id,
            compute_fn=_build_narrativa
        )
        logging.debug(
            f"[NarrativaCtx] cache_hit={cache_hit} latency={latency_ms:.2f}ms sesión={session_id} thread={thread_id}")
        return narrativa_ctx

    return _build_narrativa()


def _recuperar_mensajes_thread(thread_id: Optional[str]) -> List[Dict[str, Any]]:
    if not thread_id:
        return []

    try:
        from thread_memory_hook import get_thread_messages

        mensajes = get_thread_messages(thread_id) or []
        return mensajes
    except Exception as exc:
        logging.debug(
            f"No se pudieron recuperar mensajes del thread {thread_id}: {exc}")
        return []


def _cargar_thread_desde_blob(
    thread_id: Optional[str],
    session_id: Optional[str],
    top: int = 5
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Intenta cargar un thread almacenado en Blob Storage priorizando coincidencias con thread_id/session_id.
    """
    candidatos = []
    for raw in (thread_id, session_id):
        nombre = _normalizar_nombre_blob(raw)
        if nombre and nombre not in candidatos:
            candidatos.append(nombre)

    # 1) Intentar candidatos directos
    candidato_directo = _leer_primer_thread(candidatos, session_id)
    if candidato_directo:
        return candidato_directo

    # 2) Listar blobs recientes
    try:
        blob_service = BlobService.from_env()
        blobs = blob_service.listar_blobs(
            prefix="threads/", top=max(top, 5)) or []
    except Exception as exc:
        logging.debug(f"No se pudieron listar threads en blob: {exc}")
        return None, None

    blobs_ordenados = sorted(
        [b for b in blobs if b.get("name")],
        key=lambda b: _parse_blob_timestamp(b.get("last_modified")),
        reverse=True
    )

    preferidos: List[Tuple[Optional[Dict[str, Any]], Optional[str]]] = []
    for blob in blobs_ordenados:
        nombre = blob.get("name")
        if not nombre:
            continue
        data = _leer_thread_blob(nombre)
        if not data:
            continue
        if session_id and data.get("session_id") == session_id:
            return data, nombre
        preferidos.append((data, nombre))

    return preferidos[0] if preferidos else (None, None)


def _leer_primer_thread(candidatos: List[Optional[str]], session_id: Optional[str]) -> Optional[Tuple[Dict[str, Any], str]]:
    primer_valido: Optional[Tuple[Dict[str, Any], str]] = None
    for nombre in candidatos:
        if not nombre:
            continue
        data = _leer_thread_blob(nombre)
        if not data:
            continue
        if session_id and data.get("session_id") == session_id:
            return data, nombre  # coincidencia exacta
        if primer_valido is None:
            primer_valido = (data, nombre)
    return primer_valido


def _normalizar_nombre_blob(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    nombre = raw.strip()
    if not nombre:
        return None
    if not nombre.startswith("threads/"):
        nombre = f"threads/{nombre}"
    if not nombre.endswith(".json"):
        nombre = f"{nombre}.json"
    return nombre


def _leer_thread_blob(blob_name: Optional[str]) -> Optional[Dict[str, Any]]:
    if not blob_name:
        return None
    try:
        blob_service = BlobService.from_env()
        contenido = blob_service.leer_blob(blob_name)
        if not contenido:
            return None
        data = json.loads(contenido)
        if isinstance(data, dict):
            data.setdefault("id", data.get("thread_id"))
            return data
    except Exception as exc:
        logging.debug(f"No se pudo leer thread {blob_name}: {exc}")
    return None


def _parse_blob_timestamp(valor: Optional[str]) -> float:
    if not valor:
        return 0.0
    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0
