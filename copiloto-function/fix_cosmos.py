#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fix para memoria consistente en Cosmos DB"""

with open('cosmos_memory_direct.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """        raw_items = _recuperar_interacciones_prioritarias(
            container, session_id_hint, agent_filter)
        agent_id = agent_filter
        session_id = session_id_hint or (raw_items[0].get(
            "session_id") if raw_items else None)
        if not session_id:
            session_id = "fallback_session\""""

new = """        # ✅ CONSISTENCIA: Query directa si hay session_override
        if session_override:
            query = \"\"\"
            SELECT TOP 150 c.id, c.agent_id, c.session_id, c.endpoint, c.timestamp,
                   c.event_type, c.texto_semantico, c.contexto_conversacion,
                   c.metadata, c.resumen_conversacion, c.data.respuesta_resumen,
                   c.data.interpretacion_semantica, c.data.contexto_inteligente,
                   c.data.response_data.respuesta_usuario, c._ts
            FROM c
            WHERE c.session_id = @session_id
              AND IS_DEFINED(c.texto_semantico) 
              AND LENGTH(c.texto_semantico) > 30
            ORDER BY c._ts DESC
            \"\"\"
            raw_items = list(container.query_items(
                query=query,
                parameters=[{"name": "@session_id", "value": session_override}],
                enable_cross_partition_query=True
            ))
            session_id = session_override
            agent_id = agent_filter or "GlobalAgent"
            logging.info(f"🎯 Query directa: {len(raw_items)} items para session={session_id}")
        else:
            # Estrategia progresiva para casos exploratorios
            raw_items = _recuperar_interacciones_prioritarias(
                container, session_id_hint, agent_filter)
            agent_id = agent_filter
            session_id = session_id_hint or (raw_items[0].get(
                "session_id") if raw_items else None)
            if not session_id:
                session_id = "fallback_session\""""

content = content.replace(old, new)

with open('cosmos_memory_direct.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("OK - Fix aplicado")
