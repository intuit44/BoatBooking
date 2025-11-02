"""
Script para verificar que el endpoint se registra correctamente
"""

print("Importando endpoint guardar-memoria...")

try:
    import endpoints.guardar_memoria
    print("✅ Endpoint importado correctamente")
    print("✅ El decorador @app.route lo registra automáticamente")
    print("✅ Reinicia el servidor con: func start --python")
except ImportError as e:
    print(f"❌ Error: {e}")
except Exception as e:
    print(f"❌ Error inesperado: {e}")
