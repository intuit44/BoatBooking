# -*- coding: utf-8 -*-
"""
Servicio Cosmos DB para gestión de fixes y eventos semánticos
"""
import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from azure.cosmos import CosmosClient, PartitionKey
from azure.identity import DefaultAzureCredential

class CosmosFixesService:
    def __init__(self):
        self.endpoint = os.environ.get('COSMOSDB_ENDPOINT')
        self.key = os.environ.get('COSMOSDB_KEY')
        self.database_name = os.environ.get('COSMOSDB_DATABASE', 'agentMemory')
        
        # Inicializar cliente
        if self.key:
            self.client = CosmosClient(self.endpoint, self.key)
        else:
            credential = DefaultAzureCredential()
            self.client = CosmosClient(self.endpoint, credential)
        
        self.database = self.client.get_database_client(self.database_name)
        
        # Contenedores
        self.fixes_container = self._get_or_create_container(
            'fixes', 
            partition_key='/estado',
            ttl_seconds=2592000  # 30 días
        )
        
        self.events_container = self._get_or_create_container(
            'semantic_events',
            partition_key='/tipo', 
            ttl_seconds=604800  # 7 días
        )

    def _get_or_create_container(self, name: str, partition_key: str, ttl_seconds: int):
        """Crea contenedor si no existe"""
        try:
            return self.database.get_container_client(name)
        except:
            return self.database.create_container(
                id=name,
                partition_key=PartitionKey(path=partition_key),
                default_ttl=ttl_seconds,
                indexing_policy={
                    "indexingMode": "consistent",
                    "includedPaths": [
                        {"path": "/id/?"},
                        {"path": "/estado/?"},
                        {"path": "/prioridad/?"},
                        {"path": "/target/?"},
                        {"path": "/timestamp/?"},
                        {"path": "/run_id/?"}
                    ],
                    "excludedPaths": [{"path": "/*"}]
                }
            )

    def upsert_fix(self, fix_data: Dict[str, Any]) -> Dict[str, Any]:
        """Inserta o actualiza un fix con ETag para concurrencia"""
        # Generar idempotency key
        fix_data['idempotencyKey'] = self._generate_idempotency_key(fix_data)
        fix_data['timestamp'] = datetime.now().isoformat()
        
        try:
            # Verificar duplicados por idempotencyKey
            existing = list(self.fixes_container.query_items(
                "SELECT * FROM c WHERE c.idempotencyKey = @key",
                parameters=[{"name": "@key", "value": fix_data['idempotencyKey']}],
                enable_cross_partition_query=True
            ))
            
            if existing:
                return {"exito": False, "error": "Fix duplicado", "existing_id": existing[0]['id']}
            
            # Upsert con ETag
            result = self.fixes_container.upsert_item(fix_data)
            return {"exito": True, "fix": result}
            
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def update_fix_status(self, fix_id: str, new_status: str, etag: str = None) -> Dict[str, Any]:
        """Actualiza estado de fix con ETag para evitar race conditions"""
        try:
            # Leer fix actual
            fix = self.fixes_container.read_item(fix_id, partition_key=new_status)
            
            # Verificar ETag si se proporciona
            if etag and fix.get('_etag') != etag:
                return {"exito": False, "error": "Conflicto de concurrencia"}
            
            # Actualizar
            fix['estado'] = new_status
            fix['updated_at'] = datetime.now().isoformat()
            
            result = self.fixes_container.replace_item(fix_id, fix)
            return {"exito": True, "fix": result}
            
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def get_pending_fixes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene fixes pendientes"""
        query = "SELECT * FROM c WHERE c.estado = 'pendiente'"
        
        return list(self.fixes_container.query_items(
            query, 
            partition_key='pendiente',
            max_item_count=limit
        ))

    def log_semantic_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Registra evento semántico"""
        event = {
            'id': f"{event_type}_{int(datetime.now().timestamp())}",
            'tipo': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        try:
            result = self.events_container.create_item(event)
            return {"exito": True, "event": result}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def _generate_idempotency_key(self, fix_data: Dict[str, Any]) -> str:
        """Genera clave de idempotencia basada en acción, target y propuesta"""
        key_data = f"{fix_data.get('accion', '')}{fix_data.get('target', '')}{fix_data.get('propuesta', '')}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

# Instancia global
cosmos_fixes_service = CosmosFixesService() if os.environ.get('COSMOSDB_ENDPOINT') else None