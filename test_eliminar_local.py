#!/usr/bin/env python3
"""
Prueba local de la lógica de eliminación corregida
"""
import os
from pathlib import Path

def test_eliminar_logic():
    """Simula la lógica corregida de eliminación"""
    
    # Crear archivo de prueba
    test_file = "C:/temp/test_eliminar_local.txt"
    
    print(f"[TEST] Probando lógica de eliminación para: {test_file}")
    
    # Crear el archivo primero
    try:
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        with open(test_file, "w") as f:
            f.write("Archivo de prueba")
        print(f"[CREATE] Archivo creado: {test_file}")
    except Exception as e:
        print(f"[CREATE] Error: {e}")
        return
    
    # Simular la lógica corregida
    try:
        # TEMP WEB FIX: Usar ruta directa sin normalización restrictiva
        local_path = Path(test_file)
        
        print(f"[LOGIC] Verificando existencia: {local_path}")
        print(f"[LOGIC] Existe: {local_path.exists()}")
        
        if local_path.exists():
            local_path.unlink()
            result = {
                "exito": True,
                "mensaje": f"Archivo '{test_file}' eliminado exitosamente del sistema local.",
                "eliminado": "local",
                "ubicacion": str(local_path),
                "ruta": test_file,
                "tipo_operacion": "eliminar_archivo"
            }
            print(f"[SUCCESS] {result['mensaje']}")
            print(f"[RESULT] {result}")
        else:
            print(f"[INFO] Archivo no encontrado localmente: {local_path}")
            
    except Exception as e:
        print(f"[ERROR] Error en sistema local: {e}")

def test_eliminar_inexistente():
    """Prueba con archivo inexistente"""
    
    test_file = "C:/temp/archivo_inexistente.txt"
    
    print(f"\n[TEST] Probando archivo inexistente: {test_file}")
    
    try:
        local_path = Path(test_file)
        
        print(f"[LOGIC] Verificando existencia: {local_path}")
        print(f"[LOGIC] Existe: {local_path.exists()}")
        
        if local_path.exists():
            local_path.unlink()
            print(f"[SUCCESS] Archivo eliminado")
        else:
            print(f"[INFO] Archivo no encontrado - considerado eliminado")
            
    except Exception as e:
        print(f"[ERROR] Error: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("PRUEBA LOCAL DE LÓGICA DE ELIMINACIÓN")
    print("=" * 50)
    
    test_eliminar_logic()
    test_eliminar_inexistente()
    
    print("\n" + "=" * 50)
    print("PRUEBA LOCAL COMPLETADA")
    print("=" * 50)