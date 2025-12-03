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
from typing import Any, Callable, Dict, Optional, Tuple, cast
import redis
from datetime import datetime
from redis import exceptions as redis_exceptions

CUSTOM_EVENT_LOGGER = logging.getLogger("appinsights.customEvents")

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
    # 15 min
    "logs_analysis": {"ttl": int(os.getenv("REDIS_LOGS_TTL", "900"))},
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

        # ⭐ ACTUALIZADO: Usar el host correcto de Redis Enterprise
        self._host = os.getenv(
            "REDIS_HOST",
            "managed-redis-copiloto.eastus2.redis.azure.net"  # Modificado
        )

        # ⭐ ACTUALIZADO: Puerto correcto para Redis Enterprise
        self._port = int(os.getenv("REDIS_PORT", "10000")
                         )  # Puerto 10000, no 6380

        self._db = int(os.getenv("REDIS_DB", "0"))

        # ⭐ IMPORTANTE: Configuración específica para Azure Redis Enterprise
        self._ssl = True  # Siempre True para Azure
        self._ssl_cert_reqs = ssl.CERT_NONE  # ⭐ NUEVO: Azure Redis requiere esto

        self._aad_scope = os.getenv(
            "REDIS_AAD_SCOPE", "https://redis.azure.com/.default")

        # Cluster awareness y control de fallos RedisJSON
        self._is_cluster = False
        self._cluster_mode = os.getenv("REDIS_CLUSTER_MODE", "oss").lower()
        self._json_failures: Dict[str, int] = {}

        self._enabled = bool(redis and self._host)
        if not DefaultAzureCredential:
            logging.warning(
                "[RedisBuffer] azure-identity no está instalado; se intentará fallback con REDIS_KEY si existe.")

        # ⭐ NUEVO: Configuración de timeout específica para Redis Enterprise
        self._socket_timeout = int(os.getenv("REDIS_SOCKET_TIMEOUT", "10"))
        self._socket_connect_timeout = int(
            os.getenv("REDIS_CONNECT_TIMEOUT", "10"))

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

        # ⭐ NUEVA: Primero verificar si RedisJSON está disponible
        self._has_redisjson = False

        # Intentar primero con REDIS_KEY (más directo para Redis Enterprise)
        key = os.getenv("REDIS_KEY")
        if key:
            try:
                ssl_flag = bool(int(os.getenv("REDIS_SSL", "1")))
                logging.info(
                    f"[RedisBuffer] Intentando conexión con REDIS_KEY (host={self._host}, ssl={ssl_flag})")

                redis_params = {
                    "host": self._host,
                    "port": self._port,
                    "password": key.strip(),  # ⭐ .strip() para limpiar espacios
                    "db": self._db,
                    "ssl": ssl_flag,
                    "ssl_cert_reqs": ssl.CERT_NONE,  # ⭐ IMPORTANTE para Azure
                    "socket_timeout": self._socket_timeout,
                    "socket_connect_timeout": self._socket_connect_timeout,
                    "decode_responses": False,  # Evitar issues de encoding, usar bytes
                    "encoding": "utf-8",
                    "encoding_errors": "replace",
                    "retry_on_timeout": True,
                    "health_check_interval": 30,  # ⭐ NUEVO: Health check
                }

                self._client = redis.Redis(**redis_params)

                # ⭐ NUEVO: Testeo más robusto
                self._client.ping()

                # Detectar si hay cluster habilitado
                try:
                    info_cluster = self._client.info("cluster")
                    try:
                        self._is_cluster = int(
                            info_cluster.get("cluster_enabled", 0)) == 1
                    except (ValueError, TypeError):
                        self._is_cluster = False
                    logging.info(
                        f"[RedisBuffer] Cluster mode detected: {self._is_cluster}")
                except Exception:
                    self._is_cluster = False

                # ⭐ NUEVO: Verificar si RedisJSON está disponible
                try:
                    # Intentar un comando simple de RedisJSON
                    test_key = f"test:redisjson:{int(time.time())}"
                    self._client.json().set(test_key, '$', {"test": True})
                    result = self._client.json().get(test_key)
                    self._client.delete(test_key)
                    if result:
                        self._has_redisjson = True
                        logging.info(
                            "[RedisBuffer] ✅ RedisJSON está disponible")
                except Exception as json_err:
                    logging.warning(
                        f"[RedisBuffer] RedisJSON no disponible: {json_err}")
                    self._has_redisjson = False

                self._enabled = True
                logging.info(
                    f"[RedisBuffer] ✅ Conectado usando REDIS_KEY: {self._host}:{self._port} (RedisJSON: {self._has_redisjson})")
                return

            except redis.exceptions.AuthenticationError as auth_err:
                logging.error(
                    f"[RedisBuffer] ❌ Error de autenticación: {auth_err}")
                # Verificar si la key necesita el = al final
                if not key.endswith('='):
                    logging.info(
                        "[RedisBuffer] Intentando agregar '=' a la key...")
                    key = key + '='
                    # Podrías reintentar aquí
            except Exception as exc:
                logging.error(
                    f"[RedisBuffer] ❌ Falló conexión con REDIS_KEY: {exc}")
                self._client = None

        # Si REDIS_KEY falló, intentar AAD
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
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    health_check_interval=30,
                )
                self._client.ping()
                self._enabled = True
                logging.info(
                    f"[RedisBuffer] ✅ Conectado usando {label}: {self._host}:{self._port}")
                return True
            except Exception as exc:
                logging.warning(
                    f"[RedisBuffer] ⚠️ {label} falló: {exc}")
                self._client = None
                return False

        # Intentar DefaultAzureCredential
        if DefaultAzureCredential:
            credential = DefaultAzureCredential(
                exclude_interactive_browser_credential=True)
            if _try_token_credential("DefaultAzureCredential", credential):
                return

        # Intentar Azure CLI para desarrollo local
        if AzureCliCredential:
            credential = AzureCliCredential()
            if _try_token_credential("AzureCliCredential", credential):
                return

        # Si todo falló, deshabilitar Redis
        logging.error(
            "[RedisBuffer] ❌ No se pudo conectar con ningún método; Redis inhabilitado.")
        self._client = None
        self._enabled = False

    @property
    def is_enabled(self) -> bool:
        return self._client is not None

    def _get_ttl(self, bucket: str) -> int:
        return CACHE_STRATEGY.get(bucket, {}).get("ttl", 300)

    def _json_set(self, key: str, payload: Any, ttl: Optional[int] = None) -> None:
        """Escritura robusta: intenta RedisJSON, maneja cluster y hace fallback serializado."""
        if not self.is_enabled or payload is None:
            return
        client = self._client
        if not client:
            return

        processed_key = self._prepare_cluster_key(key)
        ttl_value = ttl or self._get_ttl("memoria")

        failure_count = self._json_failures.get(processed_key, 0)
        redisjson_failed = False

        if getattr(self, "_has_redisjson", False) and failure_count < 3:
            try:
                client.json().set(processed_key, "$", payload)
                if ttl_value:
                    client.expire(processed_key, ttl_value)
                if processed_key in self._json_failures:
                    del self._json_failures[processed_key]
                return
            except redis.exceptions.ResponseError as e:
                msg = str(e)
                redisjson_failed = True
                self._json_failures[processed_key] = failure_count + 1
                if failure_count == 0 or "MOVED" in msg or "ASK" in msg or "4200" in msg or "8501" in msg:
                    logging.warning(
                        f"[RedisBuffer] RedisJSON falló para {processed_key}: {msg}")
            except Exception as e:
                redisjson_failed = True
                self._json_failures[processed_key] = failure_count + 1
                if failure_count == 0:
                    logging.warning(
                        f"[RedisBuffer] RedisJSON error para {processed_key}: {e}")
        else:
            redisjson_failed = True

        # Fallback serializado
        try:
            serialized = json.dumps(payload, ensure_ascii=False,
                                    separators=(",", ":"), default=str)
            encoded = serialized.encode("utf-8", "replace")
            client.setex(processed_key, ttl_value, encoded)
            if failure_count == 0:
                logging.info(
                    f"[RedisBuffer] Fallback serializado aplicado para {processed_key}")
        except Exception as err:  # pragma: no cover
            logging.error(
                f"[RedisBuffer] setex fallback falló para {processed_key}: {err}")

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

    def _prepare_cluster_key(self, key: str) -> str:
        """Para cluster OSS, agrupa claves relacionadas con hash tags."""
        if not self._is_cluster:
            return key
        if "{" in key and "}" in key:
            return key
        if key.startswith("memoria:"):
            parts = key.split(":")
            if len(parts) >= 2:
                return f"{{memoria}}:{':'.join(parts[1:])}"
        if key.startswith("thread:"):
            parts = key.split(":")
            if len(parts) >= 2:
                return f"{{thread}}:{':'.join(parts[1:])}"
        if key.startswith("narrativa:"):
            parts = key.split(":")
            if len(parts) >= 2:
                return f"{{narrativa}}:{':'.join(parts[1:])}"
        return key

    def _refresh_ttl(self, key: str, bucket: str) -> None:
        if not self.is_enabled:
            return
        ttl = self._get_ttl(bucket)
        if not ttl:
            return
        try:
            client = self._client
            if client:
                client.expire(key, ttl)
        except Exception:
            logging.debug(
                f"[RedisBuffer] No se pudo refrescar TTL de {key}.", exc_info=True)

    def _emit_cache_event(self, action: str, bucket: str, key: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Envía evento estructurado a App Insights para auditoría de caché."""
        if not key:
            return
        try:
            hashed_key = self.stable_hash(key)
            dims = {
                "component": "redis_buffer",
                "bucket": bucket or key.split(":")[0],
                "action": action,
                "key_hash": hashed_key,
                "redis_enabled": self.is_enabled
            }
            if extra:
                dims.update(extra)
            CUSTOM_EVENT_LOGGER.info(
                f"redis_buffer_{action}",
                extra={"custom_dimensions": dims}
            )
        except Exception:
            logging.debug(
                "No se pudo emitir evento custom de Redis.", exc_info=True)

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
        payload = self._json_get(key)
        if payload is not None:
            logging.info(f"[RedisBuffer] cache HIT: {key}")
            self._refresh_ttl(key, "memoria")
            self._emit_cache_event("hit", "memoria", key)
        else:
            logging.info(f"[RedisBuffer] cache MISS: {key}")
            self._emit_cache_event("miss", "memoria", key)
        return payload

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
        self._emit_cache_event(
            "write", "memoria", memoria_key, {"thread_id_present": bool(thread_id)})

        if thread_id:
            thread_key = self._format_key("thread", thread_id)
            self._json_set(thread_key, memoria_payload,
                           ttl=self._get_ttl("thread"))
            logging.info(f"[RedisBuffer] cache WRITE: {thread_key}")
            self._emit_cache_event("write", "thread", thread_key)

    def get_thread_cache(self, thread_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not thread_id:
            return None
        key = self._format_key("thread", thread_id)
        payload = self._json_get(key)
        if payload is not None:
            logging.info(f"[RedisBuffer] cache HIT: {key}")
            self._refresh_ttl(key, "thread")
            self._emit_cache_event("hit", "thread", key)
        else:
            logging.info(f"[RedisBuffer] cache MISS: {key}")
            self._emit_cache_event("miss", "thread", key)
        return payload

    def cache_thread_snapshot(self, thread_id: Optional[str], thread_payload: Dict[str, Any]) -> None:
        if not thread_id or not thread_payload:
            return
        key = self._format_key("thread", thread_id)
        self._json_set(key, thread_payload, ttl=self._get_ttl("thread"))
        self._emit_cache_event("write", "thread", key)

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
            self._refresh_ttl(cache_key, "narrativa")
            self._emit_cache_event("hit", "narrativa", cache_key)
            return cached, True, (time.perf_counter() - start) * 1000

        logging.info(f"[RedisBuffer] cache MISS: {cache_key}")
        self._emit_cache_event("miss", "narrativa", cache_key)

        payload = None
        try:
            payload = compute_fn()
        except Exception as exc:  # pragma: no cover
            logging.warning(f"[RedisBuffer] compute narrativa falló: {exc}")

        latency_ms = (time.perf_counter() - start) * 1000
        if payload:
            self._json_set(cache_key, payload, ttl=self._get_ttl("narrativa"))
            logging.info(f"[RedisBuffer] cache WRITE: {cache_key}")
            self._emit_cache_event(
                "write", "narrativa", cache_key, {"latency_ms": round(latency_ms, 2)})
        return payload, False, latency_ms

    # ------------------------------------------------------------------ #
    # Payloads pesados: respuestas completas / búsquedas / LLM
    # ------------------------------------------------------------------ #
    def get_cached_payload(self, bucket: str, payload_hash: str) -> Optional[Any]:
        key = self._format_key(bucket, payload_hash)
        cached = self._json_get(key)
        if cached is not None:
            logging.info(f"[RedisBuffer] cache HIT: {key}")
            self._refresh_ttl(key, bucket)
            self._emit_cache_event("hit", bucket, key)
        else:
            logging.info(f"[RedisBuffer] cache MISS: {key}")
            self._emit_cache_event("miss", bucket, key)
        return cached

    def cache_response(self, bucket: str, payload_hash: str, payload: Any) -> None:
        if not bucket or not payload_hash or payload is None:
            return
        ttl = self._get_ttl(bucket)
        key = self._format_key(bucket, payload_hash)
        self._json_set(key, payload, ttl=ttl)
        logging.info(f"[RedisBuffer] cache WRITE: {key}")
        self._emit_cache_event("write", bucket, key, {"ttl": ttl})

    def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna snapshot de métricas básicas del cliente Redis."""
        stats: Dict[str, Any] = {
            "enabled": self.is_enabled,
            "db": getattr(self, "_db", 0)
        }
        client = self._client
        if not client:
            return stats
        try:
            stats["dbsize"] = client.dbsize()
        except Exception as exc:
            stats["dbsize_error"] = str(exc)
        try:
            info = cast(Dict[str, Any], client.info())
            stats["used_memory_human"] = info.get("used_memory_human")
            stats["keyspace_hits"] = info.get("keyspace_hits")
            stats["keyspace_misses"] = info.get("keyspace_misses")
            if stats["keyspace_hits"] and stats["keyspace_misses"]:
                total = stats["keyspace_hits"] + stats["keyspace_misses"]
                stats["hit_ratio"] = stats["keyspace_hits"] / \
                    total if total > 0 else 0
        except Exception as exc:
            stats["info_error"] = str(exc)
        return stats

    def test_connection(self) -> Dict[str, Any]:
        """Prueba de conectividad y RedisJSON para diagnósticos rápidos."""
        result: Dict[str, Any] = {
            "connected": False,
            "redisjson_available": False,
            "ping": False,
            "info": {},
            "error": None,
        }

        if not self.is_enabled or not self._client:
            result["error"] = "Cliente no inicializado"
            return result

        try:
            client = self._client
            result["ping"] = bool(client.ping())

            # Probar RedisJSON
            test_key = f"test:connection:{int(time.time())}"
            try:
                client.json().set(test_key, "$",
                                  {"test": True, "timestamp": time.time()})
                json_result = client.json().get(test_key)
                result["redisjson_available"] = bool(json_result)
            except Exception:
                result["redisjson_available"] = False
            finally:
                try:
                    client.delete(test_key)
                except Exception:
                    pass

            try:
                info = cast(Dict[str, Any], client.info())
                result["info"] = {
                    "version": info.get("redis_version"),
                    "memory": info.get("used_memory_human"),
                    "clients": info.get("connected_clients"),
                    "role": info.get("role"),
                    "uptime": info.get("uptime_in_seconds"),
                }
            except Exception:
                result["info"] = {}

            result["connected"] = True
        except Exception as e:
            result["error"] = str(e)

        return result

    def keys(self, pattern: str = "*") -> list:
        """Retorna lista de claves que coinciden con el patrón."""
        if not self.is_enabled or not self._client:
            return []

        try:
            result = cast(list, self._client.keys(pattern))
            return result if result else []
        except Exception as e:
            logging.error(
                f"[RedisBuffer] Error obteniendo keys con patrón '{pattern}': {e}")
            return []

    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor directo desde Redis."""
        if not self.is_enabled or not self._client:
            return None

        try:
            # Intentar RedisJSON primero
            if hasattr(self._client, 'json') and callable(getattr(self._client, 'json', None)):
                try:
                    return self._client.json().get(key, '.')
                except Exception:
                    pass

            # Fallback a GET normal con deserialización JSON
            raw_value = cast(Optional[bytes], self._client.get(key))
            if raw_value is None:
                return None

            # Si es bytes, decodificar
            decoded_value = raw_value.decode(
                'utf-8') if isinstance(raw_value, bytes) else str(raw_value)

            # Intentar deserializar JSON
            try:
                return json.loads(decoded_value)
            except (json.JSONDecodeError, TypeError):
                return decoded_value

        except Exception as e:
            logging.error(f"[RedisBuffer] Error obteniendo clave '{key}': {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Alias para get_cache_stats para compatibilidad."""
        return self.get_cache_stats()

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """
        Método directo para set (compatibilidad con tests)
        """
        if not self.is_enabled:
            return False

        try:
            if isinstance(value, (dict, list)):
                # Para objetos JSON, usar JSON.SET si está disponible
                self._json_set(key, value, ttl=ex)
            else:
                # Para strings/datos simples
                if self._client:
                    self._client.set(key, value, ex=ex)
            return True
        except Exception as e:
            logging.error(f"[RedisBuffer] Error en set({key}): {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Método directo para delete (compatibilidad con tests)
        """
        if not self.is_enabled:
            return False

        try:
            if self._client:
                return bool(self._client.delete(key))
            return False
        except Exception as e:
            logging.error(f"[RedisBuffer] Error en delete({key}): {e}")
            return False


# Instancia global para importar como redis_buffer
redis_buffer = RedisBufferService()
