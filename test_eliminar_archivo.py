#!/usr/bin/env python3
"""
Prueba del endpoint eliminar-archivo corregido
"""
import requests
import json

def test_eliminar_archivo():
    """Prueba eliminación de archivo con ruta absoluta"""
    
    # Primero crear un archivo de prueba
    print("[TEST] Creando archivo de prueba...")
    
    create_url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/escribir-archivo"
    create_payload = {
        "ruta": "C:/services/test_eliminar.txt",
        "contenido": "Archivo de prueba para eliminación"
    }
    
    try:
        create_response = requests.post(
            create_url,
            json=create_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"[CREATE] Status: {create_response.status_code}")
        
        if create_response.status_code == 200:
            create_data = create_response.json()
            print(f"[CREATE] Éxito: {create_data.get('exito')}")
            
            # Ahora intentar eliminar el archivo
            print("\n[TEST] Eliminando archivo...")
            
            delete_url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/eliminar-archivo"
            delete_payload = {
                "ruta": "C:/services/test_eliminar.txt"
            }
            
            delete_response = requests.post(
                delete_url,
                json=delete_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"[DELETE] Status: {delete_response.status_code}")
            
            if delete_response.status_code == 200:
                delete_data = delete_response.json()
                print(f"[DELETE] Éxito: {delete_data.get('exito')}")
                print(f"[DELETE] Mensaje: {delete_data.get('mensaje')}")
                print(f"[DELETE] Eliminado: {delete_data.get('eliminado')}")
                
                if delete_data.get('exito'):
                    print("✅ CORRECCIÓN EXITOSA: El archivo se eliminó correctamente")
                else:
                    print("❌ PROBLEMA PERSISTE: El archivo no se pudo eliminar")
                    print(f"[ERROR] {delete_data.get('error')}")
            else:
                print(f"[DELETE] Error HTTP: {delete_response.text}")
        else:
            print(f"[CREATE] Error: {create_response.text}")
            
    except Exception as e:
        print(f"[EXCEPTION] {e}")

def test_eliminar_archivo_inexistente():
    """Prueba eliminación de archivo que no existe"""
    print("\n[TEST] Probando eliminación de archivo inexistente...")
    
    delete_url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/eliminar-archivo"
    delete_payload = {
        "ruta": "C:/services/archivo_que_no_existe.txt"
    }
    
    try:
        delete_response = requests.post(
            delete_url,
            json=delete_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"[DELETE] Status: {delete_response.status_code}")
        
        if delete_response.status_code == 200:
            delete_data = delete_response.json()
            print(f"[DELETE] Éxito: {delete_data.get('exito')}")
            print(f"[DELETE] Mensaje: {delete_data.get('mensaje')}")
            
            # Debería ser exitoso porque "no existe = eliminado"
            if delete_data.get('exito'):
                print("✅ COMPORTAMIENTO CORRECTO: Archivo inexistente considerado eliminado")
            else:
                print("⚠️ Comportamiento inesperado")
        else:
            print(f"[DELETE] Error HTTP: {delete_response.text}")
            
    except Exception as e:
        print(f"[EXCEPTION] {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("PRUEBA DE CORRECCIÓN: ELIMINAR-ARCHIVO")
    print("=" * 60)
    
    test_eliminar_archivo()
    test_eliminar_archivo_inexistente()
    
    print("\n" + "=" * 60)
    print("PRUEBAS COMPLETADAS")
    print("=" * 60)