import os
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential

class MemoryService:
    def __init__(self):
        # Configurar Cosmos DB directamente
        endpoint = os.environ.get('COSMOSDB_ENDPOINT') or ""
        key = os.environ.get('COSMOSDB_KEY')
        database_name = os.environ.get('COSMOSDB_DATABASE', 'agentMemory')
        
        try:
            if key:
                client = CosmosClient(endpoint, key)
            else:
                credential = DefaultAzureCredential()
                client = CosmosClient(endpoint, credential)
            
            database = client.get_database_client(database_name)
            self.memory_container = database.get_container_client('memory')
            self.cosmos_available = True
        except Exception as e:
            logging.warning(f"Cosmos DB no disponible: {e}")
            self.cosmos_available = False
            self.memory_container = None
        
        # Fallback local
        self.local_enabled = True
        self.scripts_dir = Path(__file__).parent.parent / "scripts"
        self.scripts_dir.mkdir(exist_ok=True)
        self.semantic_log_file = self.scripts_dir / "semantic_log.jsonl"
    
    def log_event(self, event_type: str, data: Dict[str, Any], session_id: Optional[str] = None) -> bool:
        """Registra evento en local + Cosmos DB"""
        timestamp = datetime.utcnow().isoformat()
        session_id = session_id or f"session_{int(datetime.utcnow().timestamp())}"
        
        # Estructura unificada
        event = {
            "id": f"{session_id}_{event_type}_{int(datetime.utcnow().timestamp())}",
            "session_id": session_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "data": data
        }
        
        success_local = self._log_local(event)
        success_cosmos = self._log_cosmos(event)
        
        return success_local or success_cosmos
    
    def _log_local(self, event: Dict[str, Any]) -> bool:
        """Escribe en archivo local JSONL"""
        if not self.local_enabled:
            return False
        
        try:
            with open(self.semantic_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
            return True
        except Exception as e:
            logging.error(f"Error escribiendo log local: {e}")
            return False
    
    def _log_cosmos(self, event: Dict[str, Any]) -> bool:
        """Escribe en Cosmos DB contenedor memory"""
        if not self.cosmos_available or not self.memory_container:
            return False
        
        try:
            self.memory_container.upsert_item(event)
            return True
        except Exception as e:
            logging.error(f"Error escribiendo en Cosmos memory: {e}")
            return False
    
    def save_pending_fix(self, fix_data: Dict[str, Any]) -> bool:
        """Guarda fix pendiente en local + Cosmos"""
        return self.log_event("pending_fix", fix_data)
    
    def log_alert(self, alert_data: Dict[str, Any], run_id: str) -> bool:
        """Registra alerta"""
        return self.log_event("alert", alert_data, session_id=run_id)
    
    def log_semantic_event(self, event_data: Dict[str, Any]) -> bool:
        """Registra evento semántico general"""
        return self.log_event("semantic", event_data)
    
    def get_session_history(self, session_id: str, limit: int = 100) -> list:
        """Obtiene historial de sesión desde Cosmos"""
        if not self.cosmos_available or not self.memory_container:
            return []
        
        try:
            query = "SELECT * FROM c WHERE c.session_id = @session_id ORDER BY c._ts DESC"
            items = list(self.memory_container.query_items(
                query,
                parameters=[{"name": "@session_id", "value": session_id}],
                max_item_count=limit,
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            logging.error(f"Error consultando historial: {e}")
            return []
    
    def record_interaction(self, agent_id: str, source: str, input_data: Any, output_data: Any) -> bool:
        """Registra interacción de agente"""
        interaction = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            "source": source,
            "input": input_data,
            "output": output_data,
            "session_id": f"agent_{agent_id}_{int(datetime.utcnow().timestamp())}"
        }
        
        return self.log_event("agent_interaction", interaction)

# Instancia global
memory_service = MemoryService()