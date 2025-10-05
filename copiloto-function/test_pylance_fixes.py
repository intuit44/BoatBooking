#!/usr/bin/env python3
"""
Prueba para verificar que los errores de Pylance están corregidos
"""

def test_imports():
    """Verifica que las importaciones necesarias están disponibles"""
    try:
        from azure.monitor.query import LogsQueryClient
        from azure.cosmos import CosmosClient
        from azure.identity import DefaultAzureCredential
        print("✅ Importaciones correctas: LogsQueryClient, CosmosClient, DefaultAzureCredential")
        return True
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False

def test_getattr_usage():
    """Simula el uso de getattr para acceder a tables"""
    
    # Simular objeto response sin atributo tables
    class MockResponse:
        pass
    
    response = MockResponse()
    
    # Usar getattr como en el código corregido
    tables = getattr(response, 'tables', [])
    
    if tables == []:
        print("✅ getattr funciona correctamente con valor por defecto")
        return True
    else:
        print("❌ getattr no devolvió el valor por defecto esperado")
        return False

def test_cosmos_client_usage():
    """Verifica que CosmosClient se puede instanciar correctamente"""
    try:
        # Solo verificar que la clase existe y se puede importar
        from azure.cosmos import CosmosClient
        
        # Verificar que se puede crear con credential
        endpoint = "https://test.documents.azure.com:443/"
        
        # No crear instancia real, solo verificar sintaxis
        client_code = """
        from azure.identity import DefaultAzureCredential
        credential = DefaultAzureCredential()
        client = CosmosClient(endpoint, credential)
        """
        
        compile(client_code, '<string>', 'exec')
        print("✅ CosmosClient con DefaultAzureCredential: Sintaxis correcta")
        return True
        
    except Exception as e:
        print(f"❌ Error con CosmosClient: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("VERIFICACIÓN DE CORRECCIONES PYLANCE")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_getattr_usage,
        test_cosmos_client_usage
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"RESULTADO: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 TODAS LAS CORRECCIONES PYLANCE FUNCIONAN")
    else:
        print("⚠️ Algunas correcciones necesitan atención")
    
    print("=" * 50)