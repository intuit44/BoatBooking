import { AIProjectClient } from "@azure/ai-projects";
import { DefaultAzureCredential } from "@azure/identity";

function logInfo(message, data = {}) {
  console.log(JSON.stringify({ level: "info", message, data }));
}

function logError(message, error) {
  console.error(JSON.stringify({ level: "error", message, error }));
}

/**
 * Ejecuta una conversación con un agente de IA utilizando un cliente de proyecto.
 *
 * Este flujo realiza los siguientes pasos:
 * 1. Lee el contexto del agente desde un archivo JSON de configuración.
 * 2. Valida que las propiedades requeridas (`endpoint`, `project`, `agentId`) estén presentes.
 * 3. Inicializa el cliente del proyecto de IA y recupera la información del agente.
 * 4. Crea un nuevo hilo de conversación.
 * 5. Envía un mensaje inicial al agente.
 * 6. Inicia una ejecución ("run") del agente y espera hasta que finalice o falle.
 * 7. Si la ejecución falla, registra el error.
 * 8. Al finalizar, recupera y muestra todos los mensajes del hilo.
 *
 * Bloques críticos y posibles errores:
 * - **Lectura del contexto:** Si el archivo no existe o está malformado, se lanzará un error de lectura o de parseo JSON.
 * - **Validación de propiedades:** Si falta alguna propiedad requerida, se lanza un error indicando la ausencia.
 * - **Inicialización del cliente y recuperación del agente:** Si el agente no existe o hay problemas de autenticación, se lanzarán errores desde el cliente.
 * - **Creación y polling del run:** Si la ejecución tarda más de 60 segundos, se lanza un error de timeout. Si la ejecución falla, se registra el error específico.
 * - **Recuperación de mensajes:** Si hay problemas al listar los mensajes, podrían lanzarse errores desde el cliente.
 *
 * @async
 * @function runAgentConversation
 * @throws {Error} Si faltan propiedades requeridas en el contexto, si ocurre un timeout durante la ejecución, o si hay errores al interactuar con el cliente del proyecto.
 */
async function runAgentConversation() {
  const endpoint = process.env.ENDPOINT || "default_endpoint";
  const project = process.env.PROJECT || "default_project";
  const agentId = process.env.AGENT_ID || "default_agentId";

  const projectClient = new AIProjectClient(
    `${endpoint}/api/projects/${project}`,
    new DefaultAzureCredential());

  const agent = await projectClient.agents.getAgent(agentId);
  logInfo(`Retrieved agent: ${agent.name}`);

  const thread = await createThread(projectClient);

  const message = await projectClient.agents.messages.create(thread.id, "user", "Hello Agent");
  logInfo(`Created message, ID: ${message.id}`);

  // Create run
  let run = await projectClient.agents.runs.create(thread.id, agent.id);

  // Poll until the run reaches a terminal status
  const MAX_WAIT_TIME = 60000; // 60 seconds
  let elapsedTime = 0;

  while (run.status === "queued" || run.status === "in_progress") {
    if (elapsedTime >= MAX_WAIT_TIME) {
      logError("Run timed out");
      throw new Error("Run timed out");
    }
    // Wait for a second
    await new Promise((resolve) => setTimeout(resolve, 1000));
    elapsedTime += 1000;
    run = await projectClient.agents.runs.get(thread.id, run.id);
  }

  if (run.status === "failed") {
    logError(`Run failed: `, run.lastError);
  }

  logInfo(`Run completed with status: ${run.status}`);

  // Retrieve messages
  const messages = await projectClient.agents.messages.list(thread.id, { order: "asc" });
  messages.forEach((m) => {
    const content = m.content.find((c) => c.type === "text" && "text" in c);
    if (content) {
      console.log(`${m.role}: ${content.text.value}`);
    }
  });
}

async function createThread(projectClient) {
  try {
    const thread = await projectClient.agents.threads.create();
    logInfo(`Created thread, ID: ${thread.id}`);
    return thread;
  } catch (error) {
    logError("Failed to create thread:", error);
    throw error;
  }
}

// Main execution
runAgentConversation().catch(error => {
  logError("An error occurred:", error);
});
