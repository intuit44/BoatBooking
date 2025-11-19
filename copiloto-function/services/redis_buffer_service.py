# -*- coding: utf-8 -*-
"""
Redis Buffer Service
--------------------
Singleton ligero que mantiene un cliente Redis TLS y helpers de caché para
memoria semántica, threads y resultados pesados (narrativas, respuestas, LLM).

Se prioriza RedisJSON cuando está disponible.
"""
import json
import logging
import os
import threading
import time
import hashlib
import ssl
from typing import Any, Callable, Dict, Optional, Tuple
import redis

# Intento de importar credenciales de Azure
try:
    from azure.identity import DefaultAzureCredential, AzureCliCredential
except Exception:  # pragma: no cover
    DefaultAzureCredential = None
    AzureCliCredential = None

# Estrategia de TTLs (segundos) por tipo de payload
CACHE_STRATEGY: Dict[str, Dict[str, int]] = {
    # 5 min
    "memoria": {"ttl": int(os.getenv("REDIS_MEMORIA_TTL", "300"))},
    # 5 min
    "thread": {"ttl": int(os.getenv("REDIS_THREAD_TTL", "300"))},
    # 1 h
    "narrativa": {"ttl": int(os.getenv("REDIS_NARRATIVA_TTL", "3600"))},
    # 60 min
    "response": {"ttl": int(os.getenv("REDIS_RESPONSE_TTL", "3600"))},
    # 30 min
    "search": {"ttl": int(os.getenv("REDIS_SEARCH_TTL", "1800"))},
    # 90 min
    "llm": {"ttl": int(os.getenv("REDIS_LLM_TTL", "5400"))},
}


class RedisBufferService:
    """Pequeño wrapper sobre redis.Redis configurado para Azure Cache for Redis."""

    _instance_lock = threading.Lock()
    _instance: Optional["RedisBufferService"] = None

    def __new__(cls, *args, **kwargs):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self._initialized = True
        self._client: Optional["redis.Redis"] = None
        # Host de la instancia Redis (ejemplo: name.redis.cache.windows.net)
        self._host = os.getenv(
            "REDIS_HOST", "Managed-redis-copiloto.eastus2.redis.azure.net")
        self._port = int(os.getenv("REDIS_PORT", "10000"))
        # Eliminada la ruta basada en REDIS_KEY: ahora intentamos MSI y fallback a clave si es necesario
        self._db = int(os.getenv("REDIS_DB", "0"))
        # Forzamos SSL por defecto para entornos Azure, pero el fallback por clave puede respetar REDIS_SSL
        self._ssl = True
        self._aad_scope = os.getenv(
            "REDIS_AAD_SCOPE", "https://redis.azure.com/.default")
        # Enabled si redis-py está instalado y hay host configurado (MSI será opcional)
        self._enabled = bool(redis and self._host)
        if not DefaultAzureCredential:
            logging.warning(
                "[RedisBuffer] azure-identity no está instalado; se intentará fallback con REDIS_KEY si existe.")
        self._connect()

    # ------------------------------------------------------------------ #
    # Conexión (AAD vía MSI/CLI / fallback por clave)
    # ------------------------------------------------------------------ #
    def _connect(self) -> None:
        # Si ya hay cliente, no hacer nada
        if self._client is not None:
            return

        if not redis:
            logging.warning(
                "redis-py no está instalado; RedisBuffer inhabilitado.")
            self._enabled = False
            return

        def _try_token_credential(label: str, credential) -> bool:
            try:
                token = credential.get_token(self._aad_scope)
                bearer = getattr(token, "token", None)
                if not bearer:
                    raise ValueError(
                        "Token AAD vacío; no se puede autenticar contra Redis.")

                username = os.getenv("REDIS_AAD_USERNAME", "") or None

                self._client = redis.Redis(
                    host=self._host,
                    port=self._port,
                    username=username,
                    password=bearer,
                    db=self._db,
                    ssl=self._ssl,
                    ssl_cert_reqs=ssl.CERT_REQUIRED,
                    socket_timeout=2,
                    socket_connect_timeout=2,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                self._client.ping()
                self._enabled = True
                logging.info(
                    f"[RedisBuffer] Conectado a {self._host}:{self._port} usando {label} (ssl={self._ssl})")
                return True
            except Exception as exc:
                logging.warning(
                    f"[RedisBuffer] {label} no pudo obtener token para Redis: {exc}")
                self._client = None
                return False

        # Intentar DefaultAzureCredential (incluye MSI y otros proveedores AAD)
        if DefaultAzureCredential:
            credential = DefaultAzureCredential(
                exclude_interactive_browser_credential=True)
            if _try_token_credential("DefaultAzureCredential", credential):
                return

        # Intentar Azure CLI explícitamente para escenarios locales
        if AzureCliCredential:
            credential = AzureCliCredential()
            if _try_token_credential("AzureCliCredential", credential):
                return

        # Fallback: usar REDIS_KEY / REDIS_SSL si AAD no está disponible
        key = os.getenv("REDIS_KEY")
        if not key:
            logging.error(
                "[RedisBuffer] No se pudo obtener token AAD y no hay REDIS_KEY configurada; Redis quedará inhabilitado.")
            self._client = None
            self._enabled = False
            return
        try:
            ssl_flag = bool(int(os.getenv("REDIS_SSL", "0")))
            logging.info(
                f"[RedisBuffer] Usando fallback REDIS_KEY (host={self._host}, ssl={ssl_flag})")
            self._client = redis.Redis(
                host=self._host,
                port=self._port,
                password=key,
                db=self._db,
                ssl=ssl_flag,
                socket_timeout=2,
                socket_connect_timeout=2,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            self._client.ping()
            self._enabled = True
            logging.info(
                f"[RedisBuffer] Conectado a {self._host}:{self._port} usando REDIS_KEY/REDIS_SSL (ssl={ssl_flag})")
        except Exception as exc:  # pragma: no cover - depende de entorno
            logging.warning(
                f"[RedisBuffer] No se pudo conectar (AAD y fallback): {exc}")
            self._client = None
            self._enabled = False

    @property
    def is_enabled(self) -> bool:
        return self._client is not None

    def _get_ttl(self, bucket: str) -> int:
        return CACHE_STRATEGY.get(bucket, {}).get("ttl", 300)

    def _json_set(self, key: str, payload: Any, ttl: Optional[int] = None) -> None:
        if not self.is_enabled or payload is None:
            return
        try:
            client = self._client
            if not client:
                return
            client.json().set(key, "$", payload)
            if ttl:
                client.expire(key, ttl)
        except Exception:
            try:
                serialized = json.dumps(payload, ensure_ascii=False)
                client = self._client
                if client:
                    client.setex(key, ttl or self._get_ttl("memoria"),
                                 serialized.encode("utf-8"))
            except Exception as err:  # pragma: no cover
                logging.debug(f"[RedisBuffer] set {key} falló: {err}")

    def _json_get(self, key: str) -> Optional[Any]:
        if not self.is_enabled:
            return None
        try:
            client = self._client
            if not client:
                return None
            value = client.json().get(key)
            if value is not None:
                return value
        except Exception:
            try:
                client = self._client
                if client:
                    raw = client.get(key)
                    if raw and isinstance(raw, bytes):
                        return json.loads(raw.decode("utf-8"))
            except Exception as err:  # pragma: no cover
                logging.debug(f"[RedisBuffer] get {key} falló: {err}")
        return None

    def _format_key(self, prefix: str, *parts: str) -> str:
        norm_parts = [p for p in parts if p]
        return f"{prefix}:{':'.join(norm_parts)}" if norm_parts else prefix

    @staticmethod
    def stable_hash(payload: str) -> str:
        """SHA-256 deterministic hash to build cache keys for prompts/queries."""
        if not payload:
            return "empty"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------ #
    # Memoria y threads
    # ------------------------------------------------------------------ #
    def get_memoria_cache(self, session_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not session_id:
            return None
        key = self._format_key("memoria", session_id)
        return self._json_get(key)

    def cache_memoria_contexto(
        self,
        session_id: Optional[str],
        memoria_payload: Optional[Dict[str, Any]],
        thread_id: Optional[str] = None,
    ) -> None:
        if not session_id or not memoria_payload:
            return

        memoria_key = self._format_key("memoria", session_id)
        self._json_set(memoria_key, memoria_payload,
                       ttl=self._get_ttl("memoria"))
        logging.info(f"[RedisBuffer] cache WRITE: {memoria_key}")

        if thread_id:
            thread_key = self._format_key("thread", thread_id)
            self._json_set(thread_key, memoria_payload,
                           ttl=self._get_ttl("thread"))
            logging.info(f"[RedisBuffer] cache WRITE: {thread_key}")

    def get_thread_cache(self, thread_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not thread_id:
            return None
        key = self._format_key("thread", thread_id)
        return self._json_get(key)

    def cache_thread_snapshot(self, thread_id: Optional[str], thread_payload: Dict[str, Any]) -> None:
        if not thread_id or not thread_payload:
            return
        key = self._format_key("thread", thread_id)
        self._json_set(key, thread_payload, ttl=self._get_ttl("thread"))

    # ------------------------------------------------------------------ #
    # Narrativa contextual
    # ------------------------------------------------------------------ #
    def get_or_compute_narrativa(
        self,
        session_id: Optional[str],
        thread_id: Optional[str],
        compute_fn: Callable[[], Optional[Dict[str, Any]]]
    ) -> Tuple[Optional[Dict[str, Any]], bool, float]:
        """
        Retorna (payload, hit, latency_ms).
        compute_fn se ejecuta únicamente cuando no hay caché.
        """
        cache_key = self._format_key(
            "narrativa", session_id or "anon", thread_id or "default")
        start = time.perf_counter()
        cached = self._json_get(cache_key)
        if cached:
            logging.info(f"[RedisBuffer] cache HIT: {cache_key}")
            return cached, True, (time.perf_counter() - start) * 1000

        logging.info(f"[RedisBuffer] cache MISS: {cache_key}")

        payload = None
        try:
            payload = compute_fn()
        except Exception as exc:  # pragma: no cover
            logging.warning(f"[RedisBuffer] compute narrativa falló: {exc}")

        latency_ms = (time.perf_counter() - start) * 1000
        if payload:
            self._json_set(cache_key, payload, ttl=self._get_ttl("narrativa"))
            logging.info(f"[RedisBuffer] cache WRITE: {cache_key}")
        return payload, False, latency_ms

    # ------------------------------------------------------------------ #
    # Payloads pesados: respuestas completas / búsquedas / LLM
    # ------------------------------------------------------------------ #
    def get_cached_payload(self, bucket: str, payload_hash: str) -> Optional[Any]:
        key = self._format_key(bucket, payload_hash)
        cached = self._json_get(key)
        if cached is not None:
            logging.info(f"[RedisBuffer] cache HIT: {key}")
        else:
            logging.info(f"[RedisBuffer] cache MISS: {key}")
        return cached

    def cache_response(self, bucket: str, payload_hash: str, payload: Any) -> None:
        if not bucket or not payload_hash or payload is None:
            return
        ttl = self._get_ttl(bucket)
        key = self._format_key(bucket, payload_hash)
        self._json_set(key, payload, ttl=ttl)
        logging.info(f"[RedisBuffer] cache WRITE: {key}")


# Instancia global para importar como redis_buffer
redis_buffer = RedisBufferService()
