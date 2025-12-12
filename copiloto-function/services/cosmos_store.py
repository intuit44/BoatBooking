import os
import json
import logging
import threading
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from azure.identity import DefaultAzureCredential
    from azure.cosmos import CosmosClient, PartitionKey
    from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosHttpResponseError
    from azure.core.exceptions import ClientAuthenticationError
    COSMOS_AVAILABLE = True
except ImportError:
    COSMOS_AVAILABLE = False
    # Define dummy classes for when imports fail
    DefaultAzureCredential = None
    CosmosClient = None
    PartitionKey = None
    CosmosResourceNotFoundError = Exception
    CosmosHttpResponseError = Exception
    ClientAuthenticationError = Exception


class CosmosMemoryStore:
    def __init__(self):
        self.endpoint = os.environ.get("COSMOSDB_ENDPOINT")
        self.database_name = os.environ.get("COSMOSDB_DATABASE", "agentMemory")
        self.container_name = os.environ.get("COSMOSDB_CONTAINER", "memory")

        # Debug logging
        logging.info(f"[COSMOS_DEBUG] COSMOS_AVAILABLE: {COSMOS_AVAILABLE}")
        logging.info(f"[COSMOS_DEBUG] COSMOSDB_ENDPOINT: {self.endpoint}")
        logging.info(f"[COSMOS_DEBUG] COSMOSDB_DATABASE: {self.database_name}")
        logging.info(f"[COSMOS_DEBUG] COSMOSDB_CONTAINER: {self.container_name}")

        self.client = None
        self.database = None
        self.container = None
        self.enabled = bool(COSMOS_AVAILABLE and self.endpoint)
        self._initialized = False
        self._init_lock = threading.Lock()

        if not COSMOS_AVAILABLE:
            logging.warning(
                "Azure Cosmos SDK not available - Cosmos DB logging disabled.")
        elif not self.endpoint:
            logging.warning(
                "COSMOSDB_ENDPOINT not configured - Cosmos DB logging disabled.")

    def _ensure_initialized(self) -> bool:
        """Lazy initializer to avoid blocking the import path."""
        if not COSMOS_AVAILABLE or not self.endpoint:
            self.enabled = False
            return False

        if self._initialized and self.container:
            return True

        with self._init_lock:
            if self._initialized and self.container:
                return True
            self._initialize()

        return self._initialized and self.container is not None

    def _initialize(self):
        if not COSMOS_AVAILABLE or not self.endpoint:
            self.enabled = False
            self._initialized = False
            return

        try:
            if not DefaultAzureCredential or not CosmosClient or not PartitionKey:
                raise ImportError("Azure SDK components are not available.")
            credential = DefaultAzureCredential()
            self.client = CosmosClient(self.endpoint, credential=credential)
            self.database = self.client.create_database_if_not_exists(
                id=self.database_name)
            self.container = self.database.create_container_if_not_exists(
                id=self.container_name,
                partition_key=PartitionKey(path="/session_id"),
                offer_throughput=400
            )
            logging.info(
                "Cosmos DB initialized successfully using Managed Identity.")
            self.enabled = True
            self._initialized = True
        except (ClientAuthenticationError, Exception) as e:
            logging.error(f"Error initializing Cosmos DB: {e}")
            self.enabled = False
            self._initialized = False
            self.client = None
            self.database = None
            self.container = None

    def upsert(self, data: Dict[str, Any]) -> bool:
        if not self._ensure_initialized():
            return False

        try:
            # Ensure required fields
            if "id" not in data:
                data["id"] = f"{data.get('session_id', 'unknown')}_{int(datetime.utcnow().timestamp())}"
            if "session_id" not in data:
                data["session_id"] = "default"
            if "timestamp" not in data:
                data["timestamp"] = datetime.utcnow().isoformat()

            self.container.upsert_item(data)
            return True
        except Exception as e:
            logging.error(f"Error writing to Cosmos: {e}")
            return False

    def query_all(self, limit=5):
        if not self._ensure_initialized():
            logging.warning(
                "[COSMOS_DEBUG] Cosmos DB not enabled or container missing.")
            return []
        try:
            query = f"SELECT TOP {limit} * FROM c ORDER BY c._ts DESC"
            return list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
        except Exception as e:
            logging.error(f"Error querying Cosmos DB (global): {e}")
            return []
