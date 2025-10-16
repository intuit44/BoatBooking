"""
Fix Session Conflicts - Solución para conflictos de session_id duplicados
"""

import uuid
import hashlib
from datetime import datetime

def generar_session_id_unico(req_info: dict) -> str:
    """Genera session_id único garantizado sin conflictos"""
    
    # Usar timestamp con microsegundos + UUID para garantizar unicidad
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    unique_uuid = str(uuid.uuid4())[:8]
    
    # Combinar para session_id único
    session_id = f"session_{timestamp}_{unique_uuid}"
    
    return session_id

def usar_upsert_en_lugar_de_create():
    """Cambiar de create_item a upsert_item para evitar conflictos"""
    
    codigo_corregido = """
    # ANTES (causa conflictos):
    container.create_item(documento)
    
    # DESPUÉS (sin conflictos):
    container.upsert_item(documento)
    """
    
    return codigo_corregido

def agregar_timestamp_a_id():
    """Agregar timestamp único al ID del documento"""
    
    codigo_corregido = """
    # ID único con timestamp
    documento = {
        "id": f"{session_id}_{endpoint}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
        "session_id": session_id,
        # ... resto del documento
    }
    """
    
    return codigo_corregido

if __name__ == "__main__":
    print("Generando session_id únicos de prueba:")
    
    for i in range(5):
        session_id = generar_session_id_unico({})
        print(f"  {i+1}. {session_id}")
    
    print("\nSoluciones implementadas:")
    print("1. Session ID con timestamp + UUID")
    print("2. Usar upsert_item en lugar de create_item") 
    print("3. ID de documento único con microsegundos")