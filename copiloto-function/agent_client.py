"""
Cliente del agente de Azure AI Foundry con registro automático de memoria.
Este script debe ejecutarse en Azure con Managed Identity.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar path para imports
sys.path.insert(0, str(Path(__file__).parent))

from azure.ai.agents.models import ListSortOrder
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from services.agent_output_logger import registrar_output_agente

# Configurar cliente
project = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint=os.getenv("FOUNDRY_ENDPOINT", "https://AgenteOpenAi.services.ai.azure.com/api/projects/AgenteOpenAi-project")
)

agent = project.agents.get_agent(os.getenv("AGENT_ID", "asst_MjPrm7kpfPODo2ntofJ1oys0"))

# Crear thread
thread = project.agents.threads.create()
print(f"Created thread, ID: {thread.id}")

# Enviar mensaje
message = project.agents.messages.create(
    thread_id=thread.id,
    role="user",
    content="Hello Agent"
)

# Ejecutar agente
run = project.agents.runs.create_and_process(
    thread_id=thread.id,
    agent_id=agent.id
)

if run.status == "failed":
    print(f"Run failed: {run.last_error}")
else:
    messages = project.agents.messages.list(
        thread_id=thread.id, 
        order=ListSortOrder.ASCENDING
    )

    for message in messages:
        if message.text_messages:
            respuesta = message.text_messages[-1].text.value

            # Registrar output del agente en memoria
            if message.role == "assistant":
                try:
                    registrar_output_agente(
                        respuesta, 
                        session_id=thread.id, 
                        agent_id=agent.id
                    )
                    print(f"[OK] Respuesta registrada en memoria")
                except Exception as e:
                    print(f"[ERROR] No se pudo registrar: {e}")

            print(f"{message.role}: {respuesta}")
