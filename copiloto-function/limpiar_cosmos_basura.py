#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Limpieza de Cosmos DB - Elimina interacciones basura
"""

import os
import logging
from azure.cosmos import CosmosClient

logging.basicConfig(level=logging.INFO)

def limpiar_basura_cosmos():
    """Elimina todas las interacciones meta-operacionales de Cosmos"""
    
    endpoint = os.environ.get("COSMOSDB_ENDPOINT", "https://copiloto-cosmos.documents.azure.com:443/")
    key = os.environ.get("COSMOSDB_KEY")
    database_name = os.environ.get("COSMOSDB_DATABASE", "agentMemory")
    container_name = "memory"
    
    if not key:
        print("[ERROR] COSMOSDB_KEY no configurada")
        return
    
    client = CosmosClient(endpoint, key)
    database = client.get_database_client(database_name)
    container = database.get_container_client(container_name)
    
    # Query para encontrar basura
    query = """
    SELECT c.id, c.session_id, c.endpoint, c.texto_semantico, c._ts
    FROM c
    WHERE CONTAINS(c.endpoint, 'historial-interacciones')
       OR CONTAINS(c.endpoint, 'verificar-')
       OR CONTAINS(c.endpoint, 'health')
       OR CONTAINS(c.texto_semantico, 'CONSULTA DE HISTORIAL')
       OR CONTAINS(c.texto_semantico, 'Se encontraron')
       OR CONTAINS(c.texto_semantico, 'interacciones recientes')
    """
    
    print("[INFO] Buscando items basura en Cosmos...")
    items_basura = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    
    print(f"[INFO] Encontrados {len(items_basura)} items basura")
    
    if len(items_basura) == 0:
        print("[OK] No hay basura para limpiar")
        return
    
    # Confirmar
    respuesta = input(f"\n[CONFIRM] Eliminar {len(items_basura)} items? (si/no): ")
    if respuesta.lower() != 'si':
        print("[CANCEL] Operacion cancelada")
        return
    
    # Eliminar
    eliminados = 0
    errores = 0
    
    for item in items_basura:
        try:
            # Usar session_id como partition key si existe, sino usar id
            pk = item.get('session_id', item['id'])
            container.delete_item(item['id'], partition_key=pk)
            eliminados += 1
            if eliminados % 10 == 0:
                print(f"[PROGRESS] Eliminados {eliminados}/{len(items_basura)}...")
        except Exception as e:
            errores += 1
            if errores <= 5:  # Solo mostrar primeros 5 errores
                print(f"[ERROR] No se pudo eliminar {item['id']}: {e}")
    
    print(f"\n[SUMMARY] Limpieza completada:")
    print(f"  - Eliminados: {eliminados}")
    print(f"  - Errores: {errores}")
    print(f"  - Total procesados: {len(items_basura)}")

if __name__ == "__main__":
    limpiar_basura_cosmos()
