#!/usr/bin/env python3
"""
Limpia la cola de indexación de Azure Storage Queue
para eliminar mensajes corruptos con 'timestacontainer =mp'
"""

import os
from azure.storage.queue import QueueClient
from dotenv import load_dotenv

load_dotenv()

def limpiar_cola():
    """Limpia todos los mensajes de la cola de indexación"""
    
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    queue_name = "memory-indexing-queue"
    
    if not connection_string:
        print("ERROR: AZURE_STORAGE_CONNECTION_STRING no configurado")
        return False
    
    try:
        queue_client = QueueClient.from_connection_string(
            connection_string, 
            queue_name
        )
        
        # Obtener propiedades de la cola
        properties = queue_client.get_queue_properties()
        message_count = properties.approximate_message_count
        
        print(f"Cola '{queue_name}' tiene {message_count} mensajes")
        
        if message_count == 0:
            print("Cola ya esta vacia")
            return True
        
        # Limpiar todos los mensajes
        print(f"Limpiando {message_count} mensajes...")
        
        deleted = 0
        while True:
            # Recibir mensajes en lotes
            messages = queue_client.receive_messages(messages_per_page=32, visibility_timeout=10)
            
            batch = list(messages)
            if not batch:
                break
            
            for message in batch:
                try:
                    queue_client.delete_message(message)
                    deleted += 1
                    if deleted % 10 == 0:
                        print(f"   Eliminados: {deleted}/{message_count}")
                except Exception as e:
                    print(f"Error eliminando mensaje: {e}")
        
        print(f"Cola limpiada: {deleted} mensajes eliminados")
        return True
        
    except Exception as e:
        print(f"ERROR limpiando cola: {e}")
        return False

if __name__ == "__main__":
    print("Limpiador de Cola de Indexacion")
    print("=" * 50)
    limpiar_cola()
