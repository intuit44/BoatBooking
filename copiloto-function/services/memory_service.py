import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from .cosmos_store import CosmosMemoryStore

class MemoryService:
    def __init__(self):
        self.cosmos_store = CosmosMemoryStore()
        self.local_enabled = True
        self.scripts_dir = Path(__file__).parent.parent / "scripts"
        self.scripts_dir.mkdir(exist_ok=True)
        
        # Archivos locales
        self.pending_fixes_file = self.scripts_dir / "pending_fixes.json"
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
        """Escribe en Cosmos DB"""
        return self.cosmos_store.upsert(event)
    
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
        return self.cosmos_store.query(session_id, limit)

# Instancia global
memory_service = MemoryService()