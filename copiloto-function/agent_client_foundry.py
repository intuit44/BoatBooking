"""
Cliente del agente de Azure AI Foundry con registro automático de memoria.
Este archivo debe usarse como plantilla en Foundry.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
env_path = Path('c:/ProyectosSimbolicos/boat-rental-app/copiloto-function/.env')
if env_path.exists():
    load_dotenv(env_path)

# Agregar path para imports
sys.path.insert(0, 'c:/ProyectosSimbolicos/boat-rental-app/copiloto-function')

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder

try:
    from services.agent_output_logger import registrar_output_agente
except ImportError:
    registrar_output_agente = None

project = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint="https://AgenteOpenAi.services.ai.azure.com/api/projects/AgenteOpenAi-project")

agent = project.agents.get_agent("asst_MjPrm7kpfPODo2ntofJ1oys0")

thread = project.agents.threads.create()
print(f"Created thread, ID: {thread.id}")

message = project.agents.messages.create(
    thread_id=thread.id,
    role="user",
    content="Hello Agent"
)

run = project.agents.runs.create_and_process(
    thread_id=thread.id,
    agent_id=agent.id)

if run.status == "failed":
    print(f"Run failed: {run.last_error}")
else:
    messages = project.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)

    for message in messages:
        if message.text_messages:
            respuesta = message.text_messages[-1].text.value
            
            # Registrar output del agente en memoria
            if message.role == "assistant" and registrar_output_agente:
                try:
                    registrar_output_agente(respuesta, session_id=thread.id, agent_id=agent.id)
                except Exception:
                    pass  # No bloquear si falla
            
            print(f"{message.role}: {respuesta}")
