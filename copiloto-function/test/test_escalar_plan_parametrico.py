import pytest
import json
import os
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path
import sys
import subprocess

# Import the function app module
from function_app import (
    get_blob_client,
    diagnosticar_function_app,
    crear_archivo,
    modificar_archivo,
    ejecutar_script,
    mover_archivo,
    copiar_archivo,
    leer_archivo_http,
    escribir_archivo_http,
    modificar_archivo_http,
    eliminar_archivo_http,
    mover_archivo_http,
    copiar_archivo_http,
    info_archivo_http,
    ejecutar_script_http,
    ejecutar_cli_http,
    configurar_cors_http,
    configurar_app_settings_http,
    escalar_plan_http,
    preparar_script_http,
    health,
    CACHE,
    PROJECT_ROOT,
    IS_AZURE
)

# Mock Azure Functions classes


class MockHttpRequest:
    def __init__(self, method="GET", body=None, params=None, headers=None):
        self.method = method
        self._body = body.encode('utf-8') if isinstance(body, str) else body
        self.params = params or {}
        self.headers = headers or {}

    def get_body(self):
        return self._body

    def get_json(self):
        if self._body:
            return json.loads(self._body.decode('utf-8'))
        return None


class MockHttpResponse:
    def __init__(self, body, status_code=200, mimetype="text/plain"):
        self.body = body
        self.status_code = status_code
        self.mimetype = mimetype

# Test data fixtures


@pytest.fixture
def mock_blob_client():
    """Mock Azure Blob Storage client"""
    mock_client = Mock()
    mock_container = Mock()
    mock_blob = Mock()

    mock_client.get_container_client.return_value = mock_container
    mock_container.get_blob_client.return_value = mock_blob
    mock_container.exists.return_value = True
    mock_blob.exists.return_value = True
    mock_blob.download_blob.return_value.readall.return_value = b"test content"

    return mock_client


@pytest.fixture
def sample_file_content():
    return "# Test File\nThis is a test file content."


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing"""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    return test_file


class TestGetBlobClient:
    """Tests for get_blob_client function"""

    @patch.dict(os.environ, {'AZURE_STORAGE_CONNECTION_STRING': 'test_connection'})
    @patch('function_app.BlobServiceClient')
    def test_get_blob_client_with_connection_string(self, mock_blob_service):
        """Test blob client creation with connection string"""
        mock_client = Mock()
        mock_blob_service.from_connection_string.return_value = mock_client

        result = get_blob_client()

        assert result == mock_client
        mock_blob_service.from_connection_string.assert_called_once_with(
            'test_connection')

    @patch.dict(os.environ, {}, clear=True)
    def test_get_blob_client_no_connection_string(self):
        """Test blob client when no connection string is available"""
        result = get_blob_client()
        assert result is None


class TestDiagnosticarFunctionApp:
    """Tests for diagnosticar_function_app function"""

    @patch('function_app.get_blob_client')
    def test_diagnosticar_function_app_success(self, mock_get_blob_client):
        """Test successful diagnostics"""
        mock_get_blob_client.return_value = Mock()

        result = diagnosticar_function_app()

        assert isinstance(result, dict)
        assert "timestamp" in result
        assert "checks" in result
        assert "configuracion" in result["checks"]

    @patch('function_app.get_blob_client')
    def test_diagnosticar_function_app_no_blob_client(self, mock_get_blob_client):
        """Test diagnostics when blob client is not available"""
        mock_get_blob_client.return_value = None

        result = diagnosticar_function_app()

        assert isinstance(result, dict)
        assert result["checks"]["configuracion"]["blob_storage"] is False


class TestArchivoOperations:
    """Tests for file operations"""

    def test_crear_archivo_success(self, tmp_path):
        """Test successful file creation"""
        with patch('function_app.PROJECT_ROOT', tmp_path):
            result = crear_archivo("test.txt", "test content")

            assert result["exito"] is True
            assert "test.txt" in result["mensaje"]
            assert (tmp_path / "test.txt").read_text() == "test content"

    def test_crear_archivo_existing_file(self, tmp_path):
        """Test creating file that already exists"""
        test_file = tmp_path / "existing.txt"
        test_file.write_text("existing content")

        with patch('function_app.PROJECT_ROOT', tmp_path):
            result = crear_archivo("existing.txt", "new content")

            assert result["exito"] is False
            assert "ya existe" in result["error"]

    def test_modificar_archivo_agregar_final(self, tmp_path):
        """Test modifying file by appending content"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")

        with patch('function_app.PROJECT_ROOT', tmp_path):
            result = modificar_archivo(
                "test.txt", "agregar_final", "\nnew line")

            assert result["exito"] is True
            content = test_file.read_text()
            assert "original content\nnew line" == content

    def test_modificar_archivo_not_found(self, tmp_path):
        """Test modifying non-existent file"""
        with patch('function_app.PROJECT_ROOT', tmp_path):
            result = modificar_archivo(
                "nonexistent.txt", "agregar_final", "content")

            assert result["exito"] is False
            assert "no existe" in result["error"]


class TestHttpEndpoints:
    """Tests for HTTP endpoints"""

    def test_health_endpoint(self):
        """Test health endpoint"""
        request = MockHttpRequest()

        response = health(request)

        assert isinstance(response.body, str)
        data = json.loads(response.body)
        assert data["ok"] is True
        assert "timestamp" in data

    @patch('function_app.get_blob_client')
    def test_leer_archivo_http_success(self, mock_get_blob_client):
        """Test successful file reading via HTTP"""
        mock_client = Mock()
        mock_container = Mock()
        mock_blob = Mock()

        mock_get_blob_client.return_value = mock_client
        mock_client.get_container_client.return_value = mock_container
        mock_container.get_blob_client.return_value = mock_blob
        mock_blob.exists.return_value = True
        mock_blob.download_blob.return_value.readall.return_value = b"test content"

        request = MockHttpRequest(params={"ruta": "test.txt"})

        response = leer_archivo_http(request)

        assert response.status_code == 200
        data = json.loads(response.body)
        assert data["exito"] is True

    def test_leer_archivo_http_missing_ruta(self):
        """Test file reading without ruta parameter"""
        request = MockHttpRequest(params={})

        response = leer_archivo_http(request)

        assert response.status_code == 400
        data = json.loads(response.body)
        assert data["exito"] is False
        assert "ruta" in data["error"]

    def test_escribir_archivo_http_success(self):
        """Test successful file writing via HTTP"""
        body = json.dumps({"ruta": "test.txt", "contenido": "test content"})
        request = MockHttpRequest(method="POST", body=body)

        with patch('function_app.crear_archivo') as mock_crear:
            mock_crear.return_value = {
                "exito": True, "mensaje": "Archivo creado"}

            response = escribir_archivo_http(request)

            assert response.status_code == 200
            mock_crear.assert_called_once_with("test.txt", "test content")

    def test_escribir_archivo_http_invalid_json(self):
        """Test file writing with invalid JSON"""
        request = MockHttpRequest(method="POST", body="invalid json")

        response = escribir_archivo_http(request)

        assert response.status_code == 400
        data = json.loads(response.body)
        assert data["exito"] is False

    def test_modificar_archivo_http_success(self):
        """Test successful file modification via HTTP"""
        body = json.dumps({
            "ruta": "test.txt",
            "operacion": "agregar_final",
            "contenido": "new content"
        })
        request = MockHttpRequest(method="POST", body=body)

        with patch('function_app.modificar_archivo') as mock_modificar:
            mock_modificar.return_value = {
                "exito": True, "mensaje": "Archivo modificado"}

            response = modificar_archivo_http(request)

            assert response.status_code == 200
            mock_modificar.assert_called_once()

    def test_mover_archivo_http_success(self):
        """Test successful file moving via HTTP"""
        body = json.dumps({
            "origen": "source.txt",
            "destino": "dest.txt",
            "overwrite": False
        })
        request = MockHttpRequest(method="POST", body=body)

        with patch('function_app.mover_archivo') as mock_mover:
            mock_mover.return_value = {
                "exito": True, "mensaje": "Archivo movido"}

            response = mover_archivo_http(request)

            assert response.status_code == 200
            data = json.loads(response.body)
            assert data["ok"] is True

    def test_mover_archivo_http_missing_params(self):
        """Test file moving with missing parameters"""
        body = json.dumps({"origen": "source.txt"})  # Missing destino
        request = MockHttpRequest(method="POST", body=body)

        response = mover_archivo_http(request)

        assert response.status_code == 400
        data = json.loads(response.body)
        assert data["ok"] is False
        assert "destino" in data["error"]

    def test_copiar_archivo_http_success(self):
        """Test successful file copying via HTTP"""
        body = json.dumps({
            "origen": "source.txt",
            "destino": "copy.txt",
            "overwrite": False
        })
        request = MockHttpRequest(method="POST", body=body)

        with patch('function_app.copiar_archivo') as mock_copiar:
            mock_copiar.return_value = {
                "exito": True, "mensaje": "Archivo copiado"}

            response = copiar_archivo_http(request)

            assert response.status_code == 200
            data = json.loads(response.body)
            assert data["exito"] is True

    def test_info_archivo_http_success(self):
        """Test successful file info retrieval via HTTP"""
        request = MockHttpRequest(params={"ruta": "test.txt"})

        with patch('function_app.get_blob_client') as mock_get_client:
            mock_client = Mock()
            mock_container = Mock()
            mock_blob = Mock()
            mock_props = Mock()

            mock_get_client.return_value = mock_client
            mock_client.get_container_client.return_value = mock_container
            mock_container.get_blob_client.return_value = mock_blob
            mock_container.exists.return_value = True
            mock_blob.exists.return_value = True
            mock_blob.get_blob_properties.return_value = mock_props
            mock_props.size = 1024
            mock_props.last_modified = None

            response = info_archivo_http(request)

            assert response.status_code == 200
            data = json.loads(response.body)
            assert data["ok"] is True


class TestScriptExecution:
    """Tests for script execution functionality"""

    @patch('subprocess.run')
    def test_ejecutar_script_success(self, mock_run):
        """Test successful script execution"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Success output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        with patch('function_app._resolve_local_script_path') as mock_resolve:
            mock_resolve.return_value = Path("/tmp/test.sh")

            result = ejecutar_script("test.sh", [])

            assert result["exito"] is True
            assert "Success output" in result["stdout"]

    @patch('subprocess.run')
    def test_ejecutar_script_timeout(self, mock_run):
        """Test script execution timeout"""
        mock_run.side_effect = subprocess.TimeoutExpired("test", 60)

        with patch('function_app._resolve_local_script_path') as mock_resolve:
            mock_resolve.return_value = Path("/tmp/test.sh")

            result = ejecutar_script("test.sh", [])

            assert result["exito"] is False
            assert "tiempo límite" in result["error"]

    def test_ejecutar_script_http_success(self):
        """Test successful script execution via HTTP"""
        body = json.dumps({"script": "test.sh", "args": ["param1"]})
        request = MockHttpRequest(method="POST", body=body)

        with patch('function_app.ejecutar_script') as mock_ejecutar:
            mock_ejecutar.return_value = {
                "exito": True,
                "stdout": "Script executed",
                "stderr": "",
                "codigo_salida": 0
            }

            response = ejecutar_script_http(request)

            assert response is not None, "La función devolvió None"
            assert response.status_code == 200

    def test_preparar_script_http_success(self):
        """Test successful script preparation via HTTP"""
        body = json.dumps({"ruta": "scripts/setup.sh"})
        request = MockHttpRequest(method="POST", body=body)

        with patch('function_app.preparar_script_desde_blob') as mock_preparar:
            mock_preparar.return_value = {
                "exito": True,
                "local_path": "/tmp/setup.sh"
            }

            response = preparar_script_http(request)

            assert response is not None, "La función devolvió None"
            assert response.status_code in [200, 201]
            data = json.loads(response.body)
            assert data["exito"] is True

    def test_preparar_script_http_missing_ruta(self):
        """Test script preparation with missing ruta"""
        body = json.dumps({})
        request = MockHttpRequest(method="POST", body=body)

        response = preparar_script_http(request)

        assert response is not None, "La función devolvió None"
        assert response.status_code == 400
        data = json.loads(response.body)
        assert data["exito"] is False
        assert "ruta" in data["error"]


class TestAzureCLI:
    """Tests for Azure CLI functionality"""

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_ejecutar_cli_http_success(self, mock_which, mock_run):
        """Test successful Azure CLI execution"""
        mock_which.return_value = "/usr/bin/az"
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"value": []}'
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        body = json.dumps({"comando": "group list"})
        request = MockHttpRequest(method="POST", body=body)

        response = ejecutar_cli_http(request)

        assert response is not None, "La función devolvió None"
        assert response.status_code == 200
        data = json.loads(response.body)
        assert data["exito"] is True

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_ejecutar_cli_http_command_failure(self, mock_which, mock_run):
        """Test Azure CLI command failure"""
        mock_which.return_value = "/usr/bin/az"
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Command failed"
        mock_run.return_value = mock_result

        body = json.dumps({"comando": "invalid command"})
        request = MockHttpRequest(method="POST", body=body)

        response = ejecutar_cli_http(request)

        assert response is not None, "La función devolvió None"
        assert response.status_code == 200  # Still 200 for agent to read error
        data = json.loads(response.body)
        assert data["exito"] is False
        assert "Command failed" in data["error"]

    def test_ejecutar_cli_http_missing_comando(self):
        """Test Azure CLI execution without command"""
        body = json.dumps({})
        request = MockHttpRequest(method="POST", body=body)

        response = ejecutar_cli_http(request)

        assert response is not None, "La función devolvió None"
        assert response.status_code == 400
        data = json.loads(response.body)
        assert data["exito"] is False
        assert "comando" in data["error"]


class TestAzureConfiguration:
    """Tests for Azure configuration endpoints"""

    @patch('function_app.set_cors')
    def test_configurar_cors_http_success(self, mock_set_cors):
        """Test successful CORS configuration"""
        mock_set_cors.return_value = {"ok": True, "message": "CORS configured"}

        body = json.dumps({
            "function_app": "test-app",
            "resource_group": "test-rg",
            "allowed_origins": ["https://example.com"]
        })
        request = MockHttpRequest(method="POST", body=body)

        response = configurar_cors_http(request)

        assert response is not None, "La función devolvió None"
        assert response.status_code == 200
        data = json.loads(response.body)
        assert data["ok"] is True

    def test_configurar_cors_http_missing_params(self):
        """Test CORS configuration with missing parameters"""
        body = json.dumps({"allowed_origins": ["*"]})
        request = MockHttpRequest(method="POST", body=body)

        # Clear environment variables to force missing params
        with patch.dict(os.environ, {}, clear=True):
            response = configurar_cors_http(request)

            assert response is not None, "La función devolvió None"
            assert response.status_code == 400
            data = json.loads(response.body)
            assert data["ok"] is False

    @patch('function_app.set_app_settings')
    def test_configurar_app_settings_http_success(self, mock_set_settings):
        """Test successful app settings configuration"""
        mock_set_settings.return_value = {
            "ok": True, "message": "Settings updated"}

        body = json.dumps({
            "function_app": "test-app",
            "resource_group": "test-rg",
            "settings": {"KEY1": "value1", "KEY2": "value2"}
        })
        request = MockHttpRequest(method="POST", body=body)

        response = configurar_app_settings_http(request)

        assert response is not None, "La función devolvió None"
        assert response.status_code == 200
        data = json.loads(response.body)
        assert data["ok"] is True

    def test_configurar_app_settings_http_empty_settings(self):
        """Test app settings configuration with empty settings"""
        body = json.dumps({
            "function_app": "test-app",
            "resource_group": "test-rg",
            "settings": {}
        })
        request = MockHttpRequest(method="POST", body=body)

        response = configurar_app_settings_http(request)

        assert response is not None, "La función devolvió None"
        assert response.status_code == 400
        data = json.loads(response.body)
        assert data["ok"] is False
        assert "vacío" in data["error"]

    @patch('function_app.update_app_service_plan')
    def test_escalar_plan_http_success(self, mock_update_plan):
        """Test successful app service plan scaling"""
        mock_update_plan.return_value = {"ok": True, "plan_updated": "EP1"}

        body = json.dumps({
            "plan_name": "boat-rental-app-plan",
            "resource_group": "boat-rental-rg",
            "sku": "EP1"
        })
        request = MockHttpRequest(method="POST", body=body)

        response = escalar_plan_http(request)

        assert response is not None, "La función devolvió None"
        assert response.status_code == 200
        data = json.loads(response.body)
        assert data["ok"] is True

    def test_escalar_plan_http_invalid_sku(self):
        """Test app service plan scaling with invalid SKU"""
        body = json.dumps({
            "plan_name": "test-plan",
            "resource_group": "test-rg",
            "sku": "INVALID_SKU"
        })
        request = MockHttpRequest(method="POST", body=body)

        response = escalar_plan_http(request)

        assert response is not None, "La función devolvió None"
        assert response.status_code == 400
        data = json.loads(response.body)
        assert data["ok"] is False
        assert "válido" in data["error"]

    def test_escalar_plan_http_invalid_plan_name(self):
        """Test app service plan scaling with invalid plan name"""
        body = json.dumps({
            "plan_name": "test",  # This should be detected as invalid
            "resource_group": "test-rg",
            "sku": "EP1"
        })
        request = MockHttpRequest(method="POST", body=body)

        response = escalar_plan_http(request)

        assert response is not None, "La función devolvió None"
        assert response.status_code == 400
        data = json.loads(response.body)
        assert data["ok"] is False
        assert "test" in data["error"]


class TestUtilityFunctions:
    """Tests for utility functions"""

    def test_cache_functionality(self):
        """Test cache operations"""
        # Clear cache first
        CACHE.clear()

        # Add some test data
        CACHE["test_key"] = {"data": "test_value"}

        assert "test_key" in CACHE
        assert CACHE["test_key"]["data"] == "test_value"

        # Clear cache
        CACHE.clear()
        assert len(CACHE) == 0

    @patch('function_app.Path')
    def test_project_root_detection(self, mock_path):
        """Test PROJECT_ROOT detection"""
        mock_path.cwd.return_value = Path("/test/path")

        # The actual PROJECT_ROOT is determined at import time
        # So we just verify it's a Path object
        assert isinstance(PROJECT_ROOT, Path)


class TestErrorHandling:
    """Tests for error handling scenarios"""

    def test_invalid_json_handling(self):
        """Test handling of invalid JSON requests"""
        request = MockHttpRequest(method="POST", body="invalid json")

        response = escribir_archivo_http(request)

        assert response.status_code == 400
        data = json.loads(response.body)
        assert data["exito"] is False

    def test_missing_request_body(self):
        """Test handling of missing request body"""
        request = MockHttpRequest(method="POST", body=None)

        response = escribir_archivo_http(request)

        assert response.status_code == 400
        data = json.loads(response.body)
        assert data["exito"] is False

    def test_file_not_found_error(self):
        """Test file not found error handling"""
        with patch('function_app.PROJECT_ROOT', Path("/nonexistent")):
            result = crear_archivo("test.txt", "content")

            # Should handle the error gracefully
            assert isinstance(result, dict)
            assert "exito" in result


class TestFileOperations:
    """Additional tests for file operations"""

    def test_mover_archivo_success(self, tmp_path):
        """Test successful file moving"""
        source = tmp_path / "source.txt"
        source.write_text("test content")

        with patch('function_app.PROJECT_ROOT', tmp_path):
            with patch('function_app.IS_AZURE', False):
                result = mover_archivo("source.txt", "dest.txt")

                assert result["exito"] is True
                assert (tmp_path / "dest.txt").exists()
                assert not source.exists()

    def test_copiar_archivo_success(self, tmp_path):
        """Test successful file copying"""
        source = tmp_path / "source.txt"
        source.write_text("test content")

        with patch('function_app.PROJECT_ROOT', tmp_path):
            with patch('function_app.IS_AZURE', False):
                result = copiar_archivo("source.txt", "copy.txt")

                assert result["exito"] is True
                assert (tmp_path / "copy.txt").exists()
                assert source.exists()  # Original should still exist

    def test_file_operations_with_azure_blob(self, mock_blob_client):
        """Test file operations when using Azure Blob Storage"""
        with patch('function_app.get_blob_client', return_value=mock_blob_client):
            with patch('function_app.IS_AZURE', True):
                result = mover_archivo("source.txt", "dest.txt")

                # Should attempt blob operations
                assert isinstance(result, dict)
                assert "exito" in result


if __name__ == "__main__":
    pytest.main([__file__])
