# -*- coding: utf-8 -*-
"""
Test simple del memory_service
"""
from dotenv import load_dotenv
load_dotenv()

from services.memory_service import memory_service

def test_memory():
    print("TESTING MEMORY SERVICE")
    print("=" * 40)
    
    # Test 1: Registrar interacción
    print("\n1. Registrando interacción...")
    success = memory_service.record_interaction(
        agent_id="AI-FOUNDATION",
        source="test_script", 
        input_data={"action": "test"},
        output_data={"result": "success"}
    )
    print(f"Resultado: {'OK' if success else 'ERROR'}")
    
    # Test 2: Log evento
    print("\n2. Registrando evento...")
    success = memory_service.log_event("test_event", {"test": "data"})
    print(f"Resultado: {'OK' if success else 'ERROR'}")

if __name__ == "__main__":
    test_memory()