# -*- coding: utf-8 -*-
"""
Script para corregir /api/copiloto y /api/historial-interacciones
Aplica las 6 correcciones críticas identificadas
"""
import re

def aplicar_correcciones():
    """Aplica correcciones al function_app.py"""
    
    with open("function_app.py", "r", encoding="utf-8") as f:
        contenido = f.read()
    
    # 1. Tolerancia a GET sin JSON en copiloto
    contenido = contenido.replace(
        """        # 💾 REGISTRAR INTERACCIÓN EN MEMORIA
        try:
            body = req.get_json() or {}
            comando = body.get("mensaje") or body.get("comando") or body.get("consulta") or "sin_comando\"""",
        """        # 💾 REGISTRAR INTERACCIÓN EN MEMORIA
        try:
            # Tolerancia a GET sin JSON
            try:
                body = req.get_json()
            except ValueError:
                body = {}
            
            comando = (
                (body or {}).get("mensaje") 
                or (body or {}).get("comando") 
                or (body or {}).get("consulta")
                or req.params.get("q")
                or req.params.get("mensaje")
                or "resumen"
            )"""
    )
    
    # 2. Filtrar basura meta en historial-interacciones (query dinámica)
    contenido = re.sub(
        r"# Formatear resultados\s+interacciones_formateadas = \[\]\s+for i, item in enumerate\(resultados\[:limit\]\):\s+interacciones_formateadas\.append\(\{",
        """# Formatear resultados filtrando meta
                interacciones_formateadas = []
                for i, item in enumerate(resultados[:limit]):
                    texto = item.get("texto_semantico", "")
                    # Filtrar basura meta
                    if texto and not any([
                        "consulta de historial completada" in texto.lower(),
                        "sin resumen de conversación" in texto.lower(),
                        "interacciones recientes:" in texto.lower()
                    ]):
                        interacciones_formateadas.append({""",
        contenido
    )
    
    # 3. Filtrar basura meta en historial-interacciones (flujo normal)
    contenido = re.sub(
        r"for i, interaccion in enumerate\(memoria_previa\.get\(\"interacciones_recientes\", \[\]\)\[:limit\]\):\s+validation_stats\[\"checked\"\] \+= 1\s+# Unificar la estructura \(compatibilidad entre versiones antiguas y nuevas\)\s+registro = interaccion\.get\(\"data\", interaccion\)",
        """for i, interaccion in enumerate(memoria_previa.get("interacciones_recientes", [])[:limit]):
                validation_stats["checked"] += 1
                
                # Filtrar basura meta antes de procesar
                texto_raw = (
                    interaccion.get("texto_semantico") or
                    interaccion.get("data", {}).get("texto_semantico") or
                    ""
                )
                if texto_raw and any([
                    "consulta de historial completada" in texto_raw.lower(),
                    "sin resumen de conversación" in texto_raw.lower(),
                    "interacciones recientes:" in texto_raw.lower()
                ]):
                    continue  # Saltar basura meta
                
                # Unificar la estructura
                registro = interaccion.get("data", interaccion)""",
        contenido
    )
    
    # 4. Agregar uso de Azure AI Search en historial-interacciones
    buscar_patron = r"# 🧠 SI HAY PARÁMETROS AVANZADOS, USAR QUERY BUILDER DINÁMICO"
    if buscar_patron in contenido:
        contenido = contenido.replace(
            buscar_patron,
            """# 🔍 USAR AZURE AI SEARCH PARA CONTEXTO SEMÁNTICO
        try:
            from services.azure_search_client import get_search_service
            search = get_search_service()
            
            query_usuario = (req.params.get("q") or req.params.get("mensaje") or "en que quedamos").strip()
            filtros = []
            if agent_id: filtros.append(f"agent_id eq '{agent_id}'")
            if session_id: filtros.append(f"session_id eq '{session_id}'")
            filter_str = " and ".join(filtros) if filtros else None
            
            busqueda = search.search(query=query_usuario, top=5, filters=filter_str)
            docs_sem = busqueda.get("documentos", []) if busqueda.get("exito") else []
            logging.info(f"🔍 Azure Search: {len(docs_sem)} docs relevantes")
        except Exception as e:
            logging.warning(f"⚠️ Azure Search no disponible: {e}")
            docs_sem = []
        
        # 🧠 SI HAY PARÁMETROS AVANZADOS, USAR QUERY BUILDER DINÁMICO"""
        )
    
    # 5. Agregar composer/sintetizador
    if "def sintetizar(" not in contenido:
        composer_code = '''
def sintetizar(docs_search, docs_cosmos):
    """Compone respuesta corta con lo último significativo"""
    partes = []
    if docs_search:
        ult = docs_search[0]
        partes.append(f"Último tema: {ult.get('endpoint','')} · {ult.get('texto_semantico','')[:240]}")
    
    # Agregar 2 recientes de cosmos sin basura
    utiles = [d for d in docs_cosmos if d.get("texto_semantico") and not any([
        "consulta de historial" in d.get("texto_semantico","").lower(),
        "sin resumen" in d.get("texto_semantico","").lower()
    ])][:2]
    for d in utiles:
        partes.append(f"- {d.get('texto_semantico','')[:240]}")
    
    if not partes:
        return "No encuentro actividad significativa reciente. ¿Quieres que revise por tema o endpoint?"
    return (
        "🧠 Resumen de la última actividad\\n"
        + "\\n".join(partes) +
        "\\n\\n🎯 Próximas acciones: • buscar detalle • listar endpoints recientes • generar plan corto"
    )

'''
        # Insertar antes de @app.function_name historial_interacciones
        contenido = contenido.replace(
            '@app.function_name(name="historial_interacciones")',
            composer_code + '@app.function_name(name="historial_interacciones")'
        )
    
    # Guardar cambios
    with open("function_app.py", "w", encoding="utf-8") as f:
        f.write(contenido)
    
    print("OK Correcciones aplicadas exitosamente")
    print("Cambios realizados:")
    print("  1. /api/copiloto tolerante a GET sin JSON")
    print("  2. Filtrado de basura meta en queries dinamicas")
    print("  3. Filtrado de basura meta en flujo normal")
    print("  4. Integracion de Azure AI Search")
    print("  5. Composer/sintetizador agregado")

if __name__ == "__main__":
    aplicar_correcciones()
