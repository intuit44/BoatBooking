"""
Test local: valida extraer_session_info() con mock de Foundry
- Sin necesidad de azure-functions instalado (inyecta stub)
- Sin headers/params/body de thread
"""

import sys
import types
import json
from unittest.mock import patch

# Inyectar stub mínimo de azure.functions para los type hints
if 'azure' not in sys.modules:
    sys.modules['azure'] = types.ModuleType('azure')
if 'azure.functions' not in sys.modules:
    af = types.ModuleType('azure.functions')
    class HttpRequest: ...
    class HttpResponse: ...
    class FunctionApp: ...
    class AuthLevel: ANONYMOUS = 'ANONYMOUS'
    af.HttpRequest = HttpRequest
    af.HttpResponse = HttpResponse
    af.FunctionApp = FunctionApp
    af.AuthLevel = AuthLevel
    sys.modules['azure.functions'] = af
    setattr(sys.modules['azure'], 'functions', af)
if 'azure.identity' not in sys.modules:
    aid = types.ModuleType('azure.identity')
    class DefaultAzureCredential:
        def __init__(self, *args, **kwargs):
            pass
        def get_token(self, *args, **kwargs):
            class T: token = 'fake'
            return T()
    aid.DefaultAzureCredential = DefaultAzureCredential
    sys.modules['azure.identity'] = aid
    setattr(sys.modules['azure'], 'identity', aid)
if 'azure.ai' not in sys.modules:
    sys.modules['azure.ai'] = types.ModuleType('azure.ai')
if 'azure.ai.projects' not in sys.modules:
    ap = types.ModuleType('azure.ai.projects')
    class AIProjectClient:
        def __init__(self, *args, **kwargs):
            pass
        class agents:
            class threads:
                @staticmethod
                def list(limit=1):
                    return []
    ap.AIProjectClient = AIProjectClient
    sys.modules['azure.ai.projects'] = ap
    setattr(sys.modules['azure.ai'], 'projects', ap)


class MockReq:
    def __init__(self):
        self.headers = {}
        self.params = {}
        self.method = 'POST'
        self._body = json.dumps({
            "input": "Consulta el estado del sistema",
            "function": {"name": "CopilotoFunctionApp_getStatus", "arguments": "{}"}
        }).encode('utf-8')
    def get_json(self):
        try:
            return json.loads(self._body.decode('utf-8'))
        except Exception:
            return {}


def main():
    print("============================================================")
    print("TEST LOCAL: extraer_session_info() con Foundry mock")
    print("============================================================\n")

    from memory_helpers import extraer_session_info

    # Parchear tanto el módulo original como el alias importado en memory_helpers
    with patch('foundry_thread_extractor.obtener_thread_desde_foundry') as mock_foundry, \
         patch('memory_helpers.obtener_thread_desde_foundry') as mock_foundry_alias:
        mock_foundry.return_value = 'thread_LOCAL_TEST_ABC123'
        mock_foundry_alias.return_value = 'thread_LOCAL_TEST_ABC123'
        req = MockReq()
        info = extraer_session_info(req)
        print(f"session_id: {info.get('session_id')}")
        print(f"agent_id: {info.get('agent_id')}")
        print(f"foundry_api_called: {mock_foundry.called or mock_foundry_alias.called}")
        ok = bool(info.get('session_id') and str(info['session_id']).startswith('thread_'))
        print("Resultado:", "OK" if ok else "FALLA")


if __name__ == '__main__':
    main()
