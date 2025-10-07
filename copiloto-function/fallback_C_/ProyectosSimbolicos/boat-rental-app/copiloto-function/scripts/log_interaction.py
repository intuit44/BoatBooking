# -*- coding: utf-8 -*-
from azure.cosmos import CosmosClient
import datetime

# Configuración de Cosmos DB
url = 'your_cosmos_db_url'
key = 'your_key'
database_name = 'your_database_name'
container_name = 'your_container_name'

# Crear cliente de Cosmos DB
client = CosmosClient(url, key)
database = client.get_database_client(database_name)
container = database.get_container_client(container_name)

# Datos de interacción
interaction_data = {
    'id': str(datetime.datetime.now()),  # ID único basado en timestamp
    'timestamp': datetime.datetime.now().isoformat(),
    'action': 'log_interaction',
    'status': 'success',
    'details': 'Interacción registrada exitosamente'
}

# Guardar en Cosmos DB
container.upsert_item(interaction_data)

print("Interacción registrada en Cosmos DB:", interaction_data)