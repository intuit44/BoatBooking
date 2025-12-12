#!/usr/bin/env python3
"""
Script minimalista para probar carga de function_app
"""
import sys
import time
import traceback


def main():
    print("🚀 Testing function_app.py import...")
    start_time = time.time()

    try:
        print("📄 Importing function_app module...")
        import function_app
        elapsed = time.time() - start_time
        print(f"✅ SUCCESS: function_app imported in {elapsed:.2f} seconds")

        # Contar funciones registradas
        if hasattr(function_app, 'app'):
            functions_count = len(
                getattr(function_app.app, '_function_registry', {}))
            print(f"📊 Functions registered: {functions_count}")

        return True

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ FAILED: function_app failed after {elapsed:.2f}s")
        print(f"Error: {e}")
        print(f"Traceback:\n{traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
