#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis CLI Service
-----------------
Fachada única para ejecución segura de comandos Redis.
Reutiliza la configuración de RedisBufferService y aplica allowlist + confirmación.
"""

import logging
import ssl
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass
import redis

logger = logging.getLogger(__name__)


@dataclass
class RedisCommandConfig:
    command: str
    category: str  # 'query', 'data', 'config', 'admin'
    description: str
    requires_confirmation: bool = False
    allowed_patterns: Optional[List[str]] = None


class RedisCLIService:
    """Servicio seguro para ejecutar comandos Redis via HTTP API."""

    COMMAND_ALLOWLIST = {
        # Consulta
        "PING": RedisCommandConfig("PING", "query", "Test de conectividad"),
        "INFO": RedisCommandConfig("INFO", "query", "Información del servidor"),
        "DBSIZE": RedisCommandConfig("DBSIZE", "query", "Número de claves"),
        "TIME": RedisCommandConfig("TIME", "query", "Hora del servidor"),
        "KEYS": RedisCommandConfig("KEYS", "query", "Listar claves", allowed_patterns=["*", "memoria:*", "thread:*"]),
        "SCAN": RedisCommandConfig("SCAN", "query", "Scan iterativo"),
        "TTL": RedisCommandConfig("TTL", "query", "Tiempo de vida restante"),
        "EXISTS": RedisCommandConfig("EXISTS", "query", "Verificar existencia"),
        "TYPE": RedisCommandConfig("TYPE", "query", "Tipo de dato"),
        # RedisJSON
        "JSON.GET": RedisCommandConfig("JSON.GET", "query", "Obtener documento JSON"),
        "JSON.TYPE": RedisCommandConfig("JSON.TYPE", "query", "Tipo de campo JSON"),
        "JSON.OBJKEYS": RedisCommandConfig("JSON.OBJKEYS", "query", "Claves de objeto JSON"),
        "JSON.ARRLEN": RedisCommandConfig("JSON.ARRLEN", "query", "Longitud de array JSON"),
        "JSON.STRLEN": RedisCommandConfig("JSON.STRLEN", "query", "Longitud de string JSON"),
        # Datos
        "GET": RedisCommandConfig("GET", "data", "Obtener valor"),
        "SET": RedisCommandConfig("SET", "data", "Establecer valor"),
        "DEL": RedisCommandConfig("DEL", "data", "Eliminar clave"),
        "EXPIRE": RedisCommandConfig("EXPIRE", "data", "Establecer TTL"),
        "JSON.SET": RedisCommandConfig("JSON.SET", "data", "Establecer documento JSON"),
        "JSON.DEL": RedisCommandConfig("JSON.DEL", "data", "Eliminar campo JSON"),
        # Config/admin (requieren confirmación)
        "CONFIG": RedisCommandConfig("CONFIG", "config", "Configuración del servidor", requires_confirmation=True),
        "BGSAVE": RedisCommandConfig("BGSAVE", "admin", "Background save", requires_confirmation=True),
        "FLUSHDB": RedisCommandConfig("FLUSHDB", "admin", "Limpiar base de datos", requires_confirmation=True),
        "FLUSHALL": RedisCommandConfig("FLUSHALL", "admin", "Limpiar todas las DBs", requires_confirmation=True),
        "MONITOR": RedisCommandConfig("MONITOR", "admin", "Monitoreo en tiempo real", requires_confirmation=True),
        "SHUTDOWN": RedisCommandConfig("SHUTDOWN", "admin", "Apagar servidor", requires_confirmation=True),
    }

    COMMAND_BLOCKLIST = {"DEBUG", "SYNC", "SLAVEOF", "REPLICAOF", "CLUSTER", "MODULE",
                         "SCRIPT", "SAVE", "MIGRATE", "RESTORE", "ACL"}

    def __init__(self, redis_host: str, redis_port: int, redis_password: str,
                 redis_db: int = 0, use_ssl: bool = True):
        self.host = redis_host
        self.port = redis_port
        self.password = redis_password
        self.db = redis_db
        self.use_ssl = use_ssl
        self._client: Optional[redis.Redis] = None
        self._last_audit: List[Dict[str, Any]] = []

    def _get_client(self) -> redis.Redis:
        if self._client is None:
            ssl_context = None
            if self.use_ssl:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                ssl=self.use_ssl,
                ssl_cert_reqs=ssl.CERT_NONE if self.use_ssl else None,
                decode_responses=False,
                encoding="utf-8",
                encoding_errors="replace",
                socket_timeout=10,
                socket_connect_timeout=10,
                retry_on_timeout=True,
                health_check_interval=30,
                ssl_context=ssl_context,
            )
            self._client.ping()
        return self._client

    def validate_command(self, command_str: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        if not command_str or not command_str.strip():
            return False, "Comando vacío", {}
        parts = command_str.strip().split()
        cmd = parts[0].upper()
        params = parts[1:] if len(parts) > 1 else []

        if cmd in self.COMMAND_BLOCKLIST:
            return False, f"Comando bloqueado por seguridad: {cmd}", {}

        if cmd.startswith("JSON."):
            json_cmd = "JSON." + cmd.split(".")[1].upper() if "." in cmd else cmd
            if json_cmd not in self.COMMAND_ALLOWLIST:
                return False, f"Comando RedisJSON no permitido: {cmd}", {}
            cmd = json_cmd

        if cmd not in self.COMMAND_ALLOWLIST:
            return False, f"Comando no permitido: {cmd}", {}

        config = self.COMMAND_ALLOWLIST[cmd]
        if cmd == "KEYS" and params:
            pattern = params[0]
            if config.allowed_patterns and pattern not in config.allowed_patterns:
                return False, f"Patrón no permitido para KEYS: {pattern}", {}

        return True, "OK", {
            "command": cmd,
            "original": command_str,
            "params": params,
            "category": config.category,
            "requires_confirmation": config.requires_confirmation,
            "description": config.description,
        }

    def execute_command(self, command_str: str, agent_id: str = "unknown", confirm: bool = False) -> Dict[str, Any]:
        is_valid, message, cmd_info = self.validate_command(command_str)
        if not is_valid:
            return {"success": False, "error": message, "command": command_str, "timestamp": datetime.utcnow().isoformat()}

        if cmd_info["requires_confirmation"] and not confirm:
            return {
                "success": False,
                "error": f"Comando requiere confirmación: {cmd_info['command']}",
                "confirmation_required": True,
                "command": cmd_info["command"],
                "description": cmd_info["description"],
                "timestamp": datetime.utcnow().isoformat(),
            }

        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            "command": cmd_info["command"],
            "params": cmd_info["params"],
            "original": cmd_info["original"],
            "confirmed": confirm,
        }
        self._last_audit.append(audit_entry)
        if len(self._last_audit) > 1000:
            self._last_audit = self._last_audit[-500:]

        try:
            client = self._get_client()
            result = self._execute_redis_command(client, cmd_info["original"])
            formatted = self._format_result(result, cmd_info["command"])
            return {
                "success": True,
                "result": formatted,
                "command": cmd_info["command"],
                "original": cmd_info["original"],
                "agent_id": agent_id,
                "timestamp": datetime.utcnow().isoformat(),
                "audit_id": len(self._last_audit) - 1,
                "requires_confirmation": cmd_info["requires_confirmation"],
            }
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error ejecutando {command_str}: {e}")
            return {"success": False, "error": f"Redis error: {str(e)}", "command": command_str, "timestamp": datetime.utcnow().isoformat()}
        except Exception as e:
            logger.error(f"Error ejecutando comando Redis '{command_str}': {e}")
            return {"success": False, "error": f"Error: {str(e)}", "command": command_str, "timestamp": datetime.utcnow().isoformat()}

    def _execute_redis_command(self, client: redis.Redis, command_str: str) -> Any:
        parts = command_str.strip().split()
        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        if cmd.upper() == "CONFIG":
            if len(args) >= 2 and args[0].upper() == "GET":
                return client.config_get(pattern=args[1])
            if len(args) >= 3 and args[0].upper() == "SET":
                return client.config_set(args[1], args[2])
            return getattr(client, cmd.lower())(*args)

        if cmd.upper() == "INFO":
            if args:
                return client.info(args[0])
            return client.info()

        if cmd.upper() == "KEYS":
            if not args:
                args = ["*"]
            return client.keys(args[0])

        if cmd.upper() == "SCAN":
            cursor = 0
            if args and args[0].isdigit():
                cursor = int(args[0])
            match_pattern = None
            count = 10
            i = 1 if args and args[0].isdigit() else 0
            while i < len(args):
                if args[i].upper() == "MATCH" and i + 1 < len(args):
                    match_pattern = args[i + 1]
                    i += 2
                elif args[i].upper() == "COUNT" and i + 1 < len(args) and args[i + 1].isdigit():
                    count = int(args[i + 1])
                    i += 2
                else:
                    i += 1
            return client.scan(cursor=cursor, match=match_pattern, count=count)

        return client.execute_command(command_str)

    def _format_result(self, result: Any, command: str) -> Any:
        if result is None:
            return None
        if isinstance(result, (int, float, str, bool)):
            return result
        if isinstance(result, bytes):
            try:
                decoded = result.decode("utf-8", errors="replace")
                if (decoded.startswith("{") and decoded.endswith("}")) or (decoded.startswith("[") and decoded.endswith("]")):
                    import json
                    try:
                        return json.loads(decoded)
                    except Exception:
                        pass
                return decoded
            except Exception:
                return str(result)
        if isinstance(result, dict):
            return {self._format_key(k): self._format_result(v, command) for k, v in result.items()}
        if isinstance(result, (list, tuple, set)):
            return [self._format_result(item, command) for item in result]
        if isinstance(result, tuple) and len(result) == 1:
            return self._format_result(result[0], command)
        return str(result)

    @staticmethod
    def _format_key(key: Any) -> str:
        if isinstance(key, bytes):
            try:
                return key.decode("utf-8", errors="replace")
            except Exception:
                return str(key)
        return str(key)

    def run_diagnostic(self) -> Dict[str, Any]:
        diagnostic: Dict[str, Any] = {"timestamp": datetime.utcnow().isoformat(), "tests": {}, "overall": "UNKNOWN"}
        try:
            client = self._get_client()
            diagnostic["tests"]["connection"] = {"ping": client.ping(), "success": True}
            try:
                test_key = f"diagnostic:json:{int(datetime.utcnow().timestamp())}"
                client.json().set(test_key, "$", {"test": True, "timestamp": diagnostic["timestamp"]})
                json_result = client.json().get(test_key)
                client.delete(test_key)
                diagnostic["tests"]["redisjson"] = {"available": json_result is not None, "success": True}
            except Exception as json_err:
                diagnostic["tests"]["redisjson"] = {"available": False, "success": False, "error": str(json_err)}
            try:
                memory_info = client.info("memory")
                diagnostic["tests"]["memory"] = {
                    "used_memory": memory_info.get("used_memory_human", "N/A"),
                    "used_memory_peak": memory_info.get("used_memory_peak_human", "N/A"),
                    "fragmentation_ratio": memory_info.get("mem_fragmentation_ratio", "N/A"),
                    "success": True,
                }
            except Exception as mem_err:
                diagnostic["tests"]["memory"] = {"success": False, "error": str(mem_err)}
            try:
                config = client.config_get("*")
                diagnostic["tests"]["configuration"] = {
                    "maxmemory": config.get("maxmemory", "N/A"),
                    "maxmemory_policy": config.get("maxmemory-policy", "N/A"),
                    "timeout": config.get("timeout", "N/A"),
                    "tcp_keepalive": config.get("tcp-keepalive", "N/A"),
                    "success": True,
                }
            except Exception as config_err:
                diagnostic["tests"]["configuration"] = {"success": False, "error": str(config_err)}
            try:
                stats = client.info("stats")
                total_hits = stats.get("keyspace_hits", 0)
                total_misses = stats.get("keyspace_misses", 0)
                hit_ratio = total_hits / max(1, total_hits + total_misses)
                diagnostic["tests"]["statistics"] = {
                    "total_commands": stats.get("total_commands_processed", 0),
                    "keyspace_hits": total_hits,
                    "keyspace_misses": total_misses,
                    "hit_ratio": hit_ratio,
                    "success": True,
                }
            except Exception as stats_err:
                diagnostic["tests"]["statistics"] = {"success": False, "error": str(stats_err)}
            all_ok = all(test.get("success", False) for test in diagnostic["tests"].values())
            diagnostic["overall"] = "HEALTHY" if all_ok else "DEGRADED"
        except Exception as e:
            diagnostic["overall"] = "FAILED"
            diagnostic["error"] = str(e)
        return diagnostic

    def get_audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._last_audit[-limit:] if self._last_audit else []

    def get_allowed_commands(self) -> Dict[str, Dict[str, Any]]:
        return {
            cmd: {
                "category": cfg.category,
                "description": cfg.description,
                "requires_confirmation": cfg.requires_confirmation,
                "allowed_patterns": cfg.allowed_patterns,
            }
            for cmd, cfg in self.COMMAND_ALLOWLIST.items()
        }


_redis_cli_instance: Optional[RedisCLIService] = None


def get_redis_cli_service() -> RedisCLIService:
    """Obtiene singleton reutilizando configuración del RedisBuffer."""
    global _redis_cli_instance
    if _redis_cli_instance is None:
        import os
        from services.redis_buffer_service import redis_buffer

        if hasattr(redis_buffer, "_host"):
            _redis_cli_instance = RedisCLIService(
                redis_host=getattr(redis_buffer, "_host", os.getenv("REDIS_HOST", "")),
                redis_port=getattr(redis_buffer, "_port", int(os.getenv("REDIS_PORT", "10000"))),
                redis_password=os.getenv("REDIS_KEY", ""),
                redis_db=getattr(redis_buffer, "_db", int(os.getenv("REDIS_DB", "0"))),
                use_ssl=getattr(redis_buffer, "_ssl", True),
            )
        else:
            _redis_cli_instance = RedisCLIService(
                redis_host=os.getenv("REDIS_HOST", ""),
                redis_port=int(os.getenv("REDIS_PORT", "10000")),
                redis_password=os.getenv("REDIS_KEY", ""),
                redis_db=int(os.getenv("REDIS_DB", "0")),
                use_ssl=bool(int(os.getenv("REDIS_SSL", "1"))),
            )
    return _redis_cli_instance
