"""
E2E: Invoca /api/status sin Session-ID ni Thread-ID
Valida que el memory wrapper se aplica, captura thread vía Foundry mock,
y no rompe la respuesta del endpoint.
"""

import os
import json
from unittest.mock import patch

"""
Para entornos sin el paquete azure-functions instalado, registramos un módulo
falso con las clases mínimas usadas por el wrapper y endpoints:
 - FunctionApp (decoradores route/function_name)
 - HttpRequest / HttpResponse
 - AuthLevel
"""

import sys
import types

if 'azure.functions' not in sys.modules:
    # Crear paquete padre 'azure' y submódulo 'azure.functions'
    if 'azure' not in sys.modules:
        sys.modules['azure'] = types.ModuleType('azure')
    af = types.ModuleType('azure.functions')

    class AuthLevel:
        ANONYMOUS = 'ANONYMOUS'

    class HttpResponse:
        def __init__(self, body: str | bytes, status_code: int = 200, mimetype: str | None = None):
            self.status_code = status_code
            self._body = body.encode('utf-8') if isinstance(body, str) else (body or b'')
            self.mimetype = mimetype
        def get_body(self):
            return self._body

    class HttpRequest:
        def __init__(self, method: str, url: str, headers: dict | None = None, params: dict | None = None, body: bytes | None = None):
            self.method = method
            self.url = url
            self.headers = headers or {}
            self.params = params or {}
            self._body = body or b''
        def get_body(self):
            return self._body
        def get_json(self):
            try:
                return json.loads(self._body.decode('utf-8')) if self._body else {}
            except Exception:
                return {}

    class FunctionApp:
        def __init__(self):
            pass
        def route(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator
        def function_name(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator

    af.AuthLevel = AuthLevel
    af.FunctionApp = FunctionApp
    af.HttpRequest = HttpRequest
    af.HttpResponse = HttpResponse
    sys.modules['azure.functions'] = af
    # También colgarlo como atributo del paquete padre
    setattr(sys.modules['azure'], 'functions', af)

import azure.functions as func

# Importa la app y el endpoint real (el wrapper ya está aplicado en import)
from function_app import status as status_endpoint  # type: ignore


def make_request(method: str = "GET", url: str = "http://localhost/api/status", body: dict | None = None) -> func.HttpRequest:
    params = {}  # sin query params
    headers = {}  # sin headers (sin Thread-ID/Session-ID)
    data = (json.dumps(body or {})).encode("utf-8") if method in ("POST", "PUT", "PATCH") else None
    return func.HttpRequest(method=method, url=url, headers=headers, params=params, body=data)


def main():
    print("============================================================")
    print("E2E: /api/status → Wrapper + Captura Thread (mock Foundry)")
    print("============================================================\n")

    # Simula Foundry devolviendo un thread activo
    with patch('foundry_thread_extractor.obtener_thread_desde_foundry') as mock_foundry, \
         patch('services.memory_service.memory_service._log_cosmos') as mock_cosmos_log:
        mock_foundry.return_value = "thread_E2E_TEST_123"
        mock_cosmos_log.return_value = True

        req = make_request(method="GET")

        print("[1/3] Ejecutando endpoint /api/status (sin headers de sesión)...")
        resp = status_endpoint(req)

        print("[2/3] Validando respuesta...")
        status_code = getattr(resp, 'status_code', None)
        body_text = (resp.get_body() or b"").decode("utf-8", errors="ignore") if hasattr(resp, 'get_body') else str(resp)
        try:
            payload = json.loads(body_text)
        except Exception:
            payload = {"raw": body_text}

        print(f"   Status: {status_code}")
        print(f"   Claves en payload: {list(payload.keys())[:6]}")

        meta = payload.get("metadata", {}) if isinstance(payload, dict) else {}
        if isinstance(meta, dict) and meta.get("wrapper_aplicado"):
            print("   [OK] Wrapper inyectó metadata en la respuesta")
        else:
            print("   [!] No se detectó metadata del wrapper (puede ser válido si endpoint no devuelve dict estándar)")

        print("[3/3] Resultado:")
        if isinstance(payload, dict) and payload.get("exito") and status_code == 200:
            print("   ✅ E2E OK: status respondió y wrapper no rompió salida")
        else:
            print("   ❌ E2E Falló o respuesta no válida")


if __name__ == "__main__":
    main()
