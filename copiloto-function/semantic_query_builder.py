"""
Constructor Semántico de Queries para Cosmos DB
Genera queries dinámicas basadas en intención del agente
"""
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


def interpretar_fecha_natural(expresion: str) -> Optional[int]:
    """Convierte expresiones naturales a timestamp Unix"""
    ahora = datetime.now()
    expresion = expresion.lower().strip()

    patrones = {
        r"últimas?\s+(\d+)\s+horas?": lambda m: int((ahora - timedelta(hours=int(m.group(1)))).timestamp()),
        r"últimos?\s+(\d+)\s+días?": lambda m: int((ahora - timedelta(days=int(m.group(1)))).timestamp()),
        r"última\s+semana": lambda m: int((ahora - timedelta(weeks=1)).timestamp()),
        r"último\s+mes": lambda m: int((ahora - timedelta(days=30)).timestamp()),
        r"ayer": lambda m: int((ahora - timedelta(days=1)).timestamp()),
        r"hoy": lambda m: int(ahora.replace(hour=0, minute=0, second=0).timestamp()),
    }

    for patron, func in patrones.items():
        match = re.search(patron, expresion)
        if match:
            return func(match)

    # Intentar parsear ISO
    try:
        return int(datetime.fromisoformat(expresion).timestamp())
    except:
        return None


def construir_query_dinamica(
    session_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    tipo: Optional[str] = None,
    contiene: Optional[str] = None,
    endpoint: Optional[str] = None,
    exito: Optional[bool] = None,
    fecha_inicio: Optional[str] = "ultimas 48h",
    fecha_fin: Optional[str] = None,
    orden: str = "desc",
    limite: int = 20,
    intencion_detectada: Optional[str] = None
) -> str:
    """
    Genera query SQL de Cosmos DB interpretando parámetros del agente

    Args:
        session_id: ID de sesión (requerido)
        agent_id: ID del agente
        tipo: Tipo de interacción (interaccion_usuario, sistema, etc)
        contiene: Texto a buscar en texto_semantico
        endpoint: Filtrar por endpoint específico
        exito: Filtrar por éxito/fallo
        fecha_inicio: Fecha inicio (ISO o natural: "últimas 24h")
        fecha_fin: Fecha fin (ISO o natural)
        orden: "asc" o "desc"
        limite: Máximo de resultados
        intencion_detectada: Intención semántica detectada

    Returns:
        Query SQL para Cosmos DB
    """
    condiciones = []

    # Filtro por session_id SOLO si NO es generico
    if session_id and session_id not in ["assistant", "test_session", "unknown", "global", None]:
        condiciones.append(f"c.session_id = '{session_id}'")

    # Filtro por agent_id SOLO si NO es generico
    if agent_id and agent_id not in ["unknown", "unknown_agent", None]:
        condiciones.append(f"c.agent_id = '{agent_id}'")

    # Filtro por tipo/event_type (buscar en ambos campos)
    if tipo:
        condiciones.append(f"(c.tipo = '{tipo}' OR c.event_type = '{tipo}')")

    # Filtro por endpoint
    if endpoint:
        # Normalizar endpoint
        endpoint_norm = endpoint.strip("/").lower()
        condiciones.append(f"CONTAINS(LOWER(c.endpoint), '{endpoint_norm}')")

    # Búsqueda semántica en texto
    if contiene:
        # Normalizar y escapar
        terminos = contiene.lower().strip().split()
        for termino in terminos:
            condiciones.append(
                f"CONTAINS(LOWER(c.texto_semantico), '{termino}')")

    # Filtro por éxito
    if exito is not None:
        condiciones.append(f"c.exito = {str(exito).lower()}")

    # Filtros temporales (SIEMPRE aplicar por defecto)
    if fecha_inicio:
        ts_inicio = interpretar_fecha_natural(fecha_inicio)
        if ts_inicio:
            condiciones.append(f"c._ts >= {ts_inicio}")

    if fecha_fin:
        ts_fin = interpretar_fecha_natural(fecha_fin)
        if ts_fin:
            condiciones.append(f"c._ts <= {ts_fin}")

    # Construir query
    where_clause = " AND ".join(condiciones) if condiciones else "1=1"
    orden_sql = "DESC" if orden.lower() == "desc" else "ASC"

    query = f"""
    SELECT TOP {limite} 
        c.id,
        c.session_id,
        c.agent_id,
        c.endpoint,
        c.texto_semantico,
        c.exito,
        c.tipo,
        c.timestamp,
        c._ts
    FROM c 
    WHERE {where_clause}
    ORDER BY c._ts {orden_sql}
    """.strip()

    logging.info(f"🔍 Query generada con event_type: {query[:200]}...")
    return query


def detectar_query_tecnica(query: str) -> Optional[Dict[str, Any]]:
    """
    Detecta si la query es técnica (UUID, IDs) y debe usar búsqueda literal
    
    Returns:
        Dict con tipo de query técnica y valor extraído, o None si no es técnica
    """
    query_lower = query.lower()
    
    # Patrón UUID estándar
    uuid_pattern = r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
    uuid_match = re.search(uuid_pattern, query, re.IGNORECASE)
    
    if uuid_match:
        return {
            "tipo": "uuid_literal",
            "valor": uuid_match.group(0),
            "modo_busqueda": "literal_cosmos"
        }
    
    # Detectar solicitudes de IDs técnicos
    id_keywords = [
        "client id", "clientid", "client-id",
        "tenant id", "tenantid", "tenant-id",
        "principal id", "principalid", "principal-id",
        "subscription id", "subscriptionid",
        "resource id", "resourceid",
        "application id", "applicationid"
    ]
    
    for keyword in id_keywords:
        if keyword in query_lower:
            return {
                "tipo": "id_request",
                "campo": keyword.replace(" ", "_"),
                "modo_busqueda": "literal_cosmos"
            }
    
    return None


def interpretar_intencion_agente(mensaje_agente: str, headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Interpreta la intención del agente y extrae parámetros

    Args:
        mensaje_agente: Mensaje/query del agente
        headers: Headers HTTP del request

    Returns:
        Dict con parámetros interpretados
    """
    params = {
        "session_id": headers.get("Session-ID", "unknown"),
        "agent_id": headers.get("Agent-ID"),
    }

    msg_lower = mensaje_agente.lower()
    
    # 🔍 DETECTAR QUERY TÉCNICA (prioridad máxima)
    query_tecnica = detectar_query_tecnica(mensaje_agente)
    if query_tecnica:
        params["query_tecnica"] = query_tecnica
        params["usar_busqueda_literal"] = True
        logging.info(f"🔧 Query técnica detectada: {query_tecnica['tipo']}")
        return params

    # Detectar intención temporal
    if any(x in msg_lower for x in ["últimas", "ayer", "hoy", "semana", "mes"]):
        # Extraer expresión temporal
        for patron in [r"últimas?\s+\d+\s+\w+", r"última\s+semana", r"último\s+mes", r"ayer", r"hoy"]:
            match = re.search(patron, msg_lower)
            if match:
                params["fecha_inicio"] = match.group(0)
                break

    # Detectar búsqueda de contenido
    if any(x in msg_lower for x in ["relacionado", "sobre", "menciona", "contiene"]):
        # Extraer términos clave
        palabras_clave = ["cosmos", "azure",
                          "error", "fallo", "éxito", "diagnóstico"]
        for palabra in palabras_clave:
            if palabra in msg_lower:
                params["contiene"] = palabra
                break

    # Detectar filtro por endpoint
    if "endpoint" in msg_lower or "api" in msg_lower:
        match = re.search(r"/api/[\w-]+", mensaje_agente)
        if match:
            params["endpoint"] = match.group(0)

    # Detectar filtro por éxito/fallo
    if any(x in msg_lower for x in ["falló", "error", "fallo"]):
        params["exito"] = False
    elif any(x in msg_lower for x in ["exitoso", "éxito", "correcto"]):
        params["exito"] = True

    # 🔥 DERIVAR event_type DESDE INTENCIÓN SEMÁNTICA
    if any(x in msg_lower for x in ["análisis", "resumen", "contextual", "semántico"]):
        params["tipo"] = "respuesta_semantica"
    elif any(x in msg_lower for x in ["diagnóstico", "diagnostico", "recursos"]):
        params["tipo"] = "diagnostico"
    elif "usuario" in msg_lower or "comandos" in msg_lower:
        params["tipo"] = "interaccion_usuario"
    elif any(x in msg_lower for x in ["error", "fallo", "falló"]):
        params["tipo"] = "error"

    # Detectar límite
    match = re.search(r"(\d+)\s+(últimos?|primeros?|resultados?)", msg_lower)
    if match:
        params["limite"] = int(match.group(1))

    logging.info(f"🧠 Parámetros interpretados: {params}")
    return params


def buscar_literal_cosmos(query_tecnica: Dict[str, Any], cosmos_container, session_id: Optional[str] = None, agent_id: Optional[str] = None) -> List[Dict]:
    """
    Ejecuta búsqueda literal en Cosmos DB para queries técnicas (UUIDs, IDs)
    
    Args:
        query_tecnica: Dict con tipo y valor de query técnica
        cosmos_container: Cliente del contenedor de Cosmos
        session_id: ID de sesión (opcional)
        agent_id: ID del agente (opcional)
    
    Returns:
        Lista de documentos encontrados
    """
    try:
        condiciones = []
        
        if query_tecnica["tipo"] == "uuid_literal":
            # Búsqueda literal del UUID en texto_semantico
            valor = query_tecnica["valor"]
            condiciones.append(f"CONTAINS(c.texto_semantico, '{valor}')")
            logging.info(f"🔍 Búsqueda literal UUID: {valor}")
        
        elif query_tecnica["tipo"] == "id_request":
            # Búsqueda de campos ID en texto_semantico
            campo = query_tecnica["campo"]
            # Buscar patrones como "principalId", "clientId", etc.
            condiciones.append(f"(CONTAINS(c.texto_semantico, 'principalId') OR CONTAINS(c.texto_semantico, 'clientId') OR CONTAINS(c.texto_semantico, 'tenantId'))")
            logging.info(f"🔍 Búsqueda literal campo ID: {campo}")
        
        # Aplicar session widening: primero sesión específica, luego agent_id, luego universal
        resultados = []
        
        # Nivel 1: Sesión específica
        if session_id and session_id not in ["assistant", "test_session", "unknown", "global", None]:
            where_clause = " AND ".join(condiciones + [f"c.session_id = '{session_id}'"])
            query = f"SELECT * FROM c WHERE {where_clause} ORDER BY c._ts DESC"
            resultados = list(cosmos_container.query_items(query=query, enable_cross_partition_query=True))
            if resultados:
                logging.info(f"✅ Nivel 1 literal: {len(resultados)} resultados en sesión {session_id}")
                return resultados
        
        # Nivel 2: Agent-wide
        if agent_id and agent_id not in ["unknown", "unknown_agent", None]:
            where_clause = " AND ".join(condiciones + [f"c.agent_id = '{agent_id}'"])
            query = f"SELECT * FROM c WHERE {where_clause} ORDER BY c._ts DESC"
            resultados = list(cosmos_container.query_items(query=query, enable_cross_partition_query=True))
            if resultados:
                logging.info(f"✅ Nivel 2 literal: {len(resultados)} resultados para agent_id {agent_id}")
                return resultados
        
        # Nivel 3: Universal
        where_clause = " AND ".join(condiciones)
        query = f"SELECT * FROM c WHERE {where_clause} ORDER BY c._ts DESC"
        resultados = list(cosmos_container.query_items(query=query, enable_cross_partition_query=True))
        logging.info(f"✅ Nivel 3 literal: {len(resultados)} resultados (universal)")
        return resultados
        
    except Exception as e:
        logging.error(f"❌ Error en búsqueda literal: {e}")
        return []


def ejecutar_query_cosmos(query: str, cosmos_container) -> List[Dict]:
    """
    Ejecuta query en Cosmos DB y devuelve resultados

    Args:
        query: Query SQL generada
        cosmos_container: Cliente del contenedor de Cosmos

    Returns:
        Lista de resultados
    """
    try:
        items = list(cosmos_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        logging.info(f"✅ Query ejecutada: {len(items)} resultados")
        return items
    except Exception as e:
        logging.error(f"❌ Error ejecutando query: {e}")
        return []
