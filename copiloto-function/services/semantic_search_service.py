"""
🔍 Servicio de Búsqueda Semántica por Intención
Búsqueda híbrida: Vector + BM25 + Semantic Ranker
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
from azure.identity import get_bearer_token_provider

logging.basicConfig(level=logging.INFO)

class SemanticSearchService:
    def __init__(self):
        # Azure Search
        search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        search_key = os.getenv("AZURE_SEARCH_KEY")
        
        if search_key:
            self.search_client = SearchClient(
                endpoint=search_endpoint,
                index_name="agent-memory-index",
                credential=AzureKeyCredential(search_key)
            )
        else:
            self.search_client = SearchClient(
                endpoint=search_endpoint,
                index_name="agent-memory-index",
                credential=DefaultAzureCredential()
            )
        
        # OpenAI para embeddings
        if os.getenv("AZURE_OPENAI_KEY"):
            self.openai_client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_KEY"),
                api_version="2024-02-01",
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
        else:
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(),
                "https://cognitiveservices.azure.com/.default"
            )
            self.openai_client = AzureOpenAI(
                azure_ad_token_provider=token_provider,
                api_version="2024-02-01",
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
    
    def clasificar_intencion(self, consulta: str) -> str:
        """Clasifica intención de la consulta"""
        consulta_lower = consulta.lower()
        
        if any(w in consulta_lower for w in ["qué quedamos", "resumen", "últim", "reciente"]):
            return "recap"
        elif any(w in consulta_lower for w in ["error", "fallo", "problema", "crítico"]):
            return "errors"
        elif any(w in consulta_lower for w in ["ejecut", "deploy", "crear", "comando"]):
            return "task"
        elif any(w in consulta_lower for w in ["archivo", "código", "script", "función"]):
            return "doc"
        else:
            return "general"
    
    def generar_embedding(self, texto: str) -> List[float]:
        """Genera embedding con text-embedding-3-large"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=texto[:8000],
                dimensions=1536  # Ajustado al índice actual
            )
            return response.data[0].embedding
        except Exception as e:
            logging.error(f"Error generando embedding: {e}")
            return None
    
    def buscar_por_intencion(
        self,
        consulta: str,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        modo: Optional[str] = None,
        ignore_session: bool = True  # Por defecto, memoria persistente por agente
    ) -> List[Dict]:
        """
        Búsqueda híbrida por intención
        Vector + BM25 (sin filtros frágiles)
        Prioriza agent_id para memoria persistente
        """
        
        # Clasificar intención si no se proporciona
        if not modo:
            modo = self.clasificar_intencion(consulta)
        
        logging.info(f"🎯 Intención: {modo} | Agente: {agent_id or 'ninguno'}")
        
        # Generar embedding
        embedding = self.generar_embedding(consulta)
        if not embedding:
            logging.warning("⚠️ No se pudo generar embedding, búsqueda solo textual")
        
        # Construir filtros automáticos (mínimos)
        filtros = []
        
        # FILTRO PRINCIPAL: agent_id (memoria persistente del agente)
        if agent_id:
            filtros.append(f"agent_id eq '{agent_id}'")
        
        # FILTRO OPCIONAL: session_id (solo si se requiere contexto de sesión específica)
        if session_id and not ignore_session:
            filtros.append(f"session_id eq '{session_id}'")
        
        # Filtro temporal solo para recap/errors (últimos 7 días)
        if modo in ["recap", "errors"]:
            limite = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat().replace("+00:00", "Z")
            filtros.append(f"timestamp ge {limite}")
        
        filtro_final = " and ".join(filtros) if filtros else None
        
        logging.info(f"🔍 Filtros aplicados: {filtro_final or 'ninguno'}")
        
        # Búsqueda híbrida (sin límite artificial, Azure Search ordena por relevancia)
        try:
            search_params = {
                "search_text": consulta,
                "select": ["id", "texto_semantico", "endpoint", "timestamp", "agent_id", "tipo", "exito"]
            }
            
            if embedding:
                search_params["vectors"] = [{
                    "value": embedding,
                    "fields": "vector",
                    "k": 20
                }]
            
            if filtro_final:
                search_params["filter"] = filtro_final
            
            results = self.search_client.search(**search_params)
            
            documentos = []
            for doc in results:
                documentos.append({
                    "id": doc.get("id"),
                    "texto_semantico": doc.get("texto_semantico"),
                    "endpoint": doc.get("endpoint"),
                    "timestamp": doc.get("timestamp"),
                    "agent_id": doc.get("agent_id"),
                    "tipo": doc.get("tipo"),
                    "exito": doc.get("exito"),
                    "score": doc.get("@search.score", 0)
                })
            
            logging.info(f"✅ Encontrados {len(documentos)} documentos relevantes")
            return documentos[:5]  # Top 5
            
        except Exception as e:
            logging.error(f"❌ Error en búsqueda: {e}")
            return []

# Instancia global
semantic_search = SemanticSearchService()
