"""
Script para registrar /api/guardar-memoria en function_app.py
"""

import sys

# Importar el endpoint
try:
    from register_guardar_memoria import register_endpoint
    from function_app import app
    
    # Registrar el endpoint
    register_endpoint(app)
    
    print("✅ Endpoint /api/guardar-memoria registrado correctamente")
    print("✅ El servidor debe reiniciarse para aplicar cambios")
    
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("   Asegúrate de que los archivos existan:")
    print("   - endpoint_guardar_memoria.py")
    print("   - register_guardar_memoria.py")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error registrando endpoint: {e}")
    sys.exit(1)
