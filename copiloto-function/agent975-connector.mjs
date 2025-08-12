// agent975-connector.mjs
// Conector bidireccional Agent975 ↔ Copiloto Semántico
// Versión 2.0 - Comunicación Real

import { AIProjectClient } from "@azure/ai-projects";
import { DefaultAzureCredential } from "@azure/identity";
import { config } from "dotenv";
import fetch from "node-fetch";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

config({ path: path.resolve(__dirname, "../../.env") });

class Agent975CopilotoConnector {
  constructor() {
    // Configuración de Agent975
    this.agent975Config = {
      endpoint: process.env.AZURE_AI_FOUNDRY_ENDPOINT,
      project: process.env.AZURE_AI_FOUNDRY_PROJECT,
      agentId: process.env.AGENT975_ID || "Agent975"
    };

    // Configuración del Copiloto
    this.copilotoConfig = {
      functionApp: "copiloto-semantico-func",
      baseUrl: "https://copiloto-semantico-func.azurewebsites.net/api",
      logicAppUrl: "https://prod-15.eastus.logic.azure.com:443/workflows/4711b810bb5f478aa4d8dc5662c61c53/triggers/When_a_HTTP_request_is_received/paths/invoke",
      logicAppParams: "?api-version=2019-05-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=IUqo-n0TnqdRiQF7qSGSBnofI5LZPmuzdYHCdmsahss"
    };

    this.masterKey = null;
    this.aiClient = null;
    this.debug = process.env.DEBUG === 'true';
  }

  // ============= LOGGING =============

  log(message, level = 'info') {
    const prefix = {
      'info': '📋',
      'success': '✅',
      'error': '❌',
      'debug': '🔍',
      'warning': '⚠️',
      'agent': '🤖',
      'copilot': '🚁'
    };

    if (level === 'debug' && !this.debug) return;

    const timestamp = new Date().toISOString().slice(11, 19);
    console.log(`[${timestamp}] ${prefix[level] || '•'} ${message}`);
  }

  // ============= INICIALIZACIÓN =============

  async initialize() {
    this.log("Inicializando conector Agent975 ↔ Copiloto", 'info');

    try {
      // 1. Inicializar cliente AI Foundry
      const credential = new DefaultAzureCredential();
      this.aiClient = new AIProjectClient(
        this.agent975Config.endpoint,
        credential
      );
      this.log("Cliente AI Foundry inicializado", 'success');

      // 2. Obtener MasterKey (si tienes Azure CLI configurado)
      try {
        const { execSync } = await import('child_process');
        this.masterKey = execSync(
          `az functionapp keys list -n ${this.copilotoConfig.functionApp} -g boat-rental-app-group --query masterKey -o tsv`,
          { encoding: 'utf8' }
        ).trim();
        this.log("MasterKey obtenida", 'success');
      } catch (e) {
        this.log("No se pudo obtener MasterKey automáticamente", 'warning');
        // Usa una key hardcodeada o del .env si es necesario
        this.masterKey = process.env.COPILOTO_MASTER_KEY || "";
      }

      // 3. Verificar conectividad
      await this.testConnectivity();

      this.log("Conector inicializado correctamente", 'success');

    } catch (error) {
      this.log(`Error en inicialización: ${error.message}`, 'error');
      throw error;
    }
  }

  // ============= COMUNICACIÓN CON COPILOTO =============

  async invokeCopiloto(command) {
    this.log(`Invocando Copiloto: ${JSON.stringify(command)}`, 'copilot');

    // Determinar endpoint y método
    const endpoint = command.endpoint || "ejecutar";
    const method = command.method || "POST";

    try {
      let url = `${this.copilotoConfig.baseUrl}/${endpoint}`;
      let options = {
        method: method,
        headers: {
          'Content-Type': 'application/json'
        }
      };

      // Agregar autenticación si tenemos MasterKey
      if (this.masterKey && endpoint !== 'health') {
        options.headers['x-functions-key'] = this.masterKey;
      }

      // Configurar según el endpoint
      switch (endpoint) {
        case 'copiloto':
          if (command.mensaje) {
            url += `?mensaje=${encodeURIComponent(command.mensaje)}`;
          }
          options.method = 'GET';
          break;

        case 'ejecutar':
          options.body = JSON.stringify({
            intencion: command.intencion,
            parametros: command.parametros || {},
            modo: command.modo || 'normal',
            contexto: command.contexto || {}
          });
          break;

        case 'invocar':
          options.body = JSON.stringify(command);
          break;

        case 'status':
        case 'health':
          options.method = 'GET';
          break;

        default:
          // Para endpoints personalizados
          if (command.body) {
            options.body = JSON.stringify(command.body);
          }
      }

      this.log(`Llamando a: ${url}`, 'debug');

      const response = await fetch(url, options);
      const data = await response.json();

      if (response.ok) {
        this.log("Respuesta del Copiloto recibida", 'success');
        return data;
      } else {
        throw new Error(`HTTP ${response.status}: ${JSON.stringify(data)}`);
      }

    } catch (error) {
      this.log(`Error invocando Copiloto: ${error.message}`, 'error');

      // Intentar via Logic App como fallback
      if (endpoint !== 'health') {
        this.log("Intentando via Logic App...", 'warning');
        return await this.invokeViaLogicApp(command);
      }

      throw error;
    }
  }

  async invokeViaLogicApp(command) {
    const url = this.copilotoConfig.logicAppUrl + this.copilotoConfig.logicAppParams;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(command)
      });

      const data = await response.json();

      if (response.ok) {
        this.log("Respuesta via Logic App recibida", 'success');
        return data;
      } else {
        throw new Error(`Logic App error: ${JSON.stringify(data)}`);
      }
    } catch (error) {
      this.log(`Error con Logic App: ${error.message}`, 'error');
      throw error;
    }
  }

  // ============= COMUNICACIÓN CON AGENT975 =============

  async processWithAgent975(input, mode = 'analyze') {
    this.log(`Procesando con Agent975: ${mode}`, 'agent');

    try {
      // Crear thread de conversación
      const thread = await this.aiClient.agents.createThread();

      // Agregar mensaje
      await this.aiClient.agents.createMessage(thread.id, {
        role: "user",
        content: input
      });

      // Ejecutar agente
      const run = await this.aiClient.agents.createRun(thread.id, {
        assistantId: this.agent975Config.agentId
      });

      // Esperar respuesta
      const runStatus = await this.waitForCompletion(thread.id, run.id);

      if (runStatus.status === 'completed') {
        // Obtener mensajes
        const messages = await this.aiClient.agents.listMessages(thread.id);
        const response = this.extractAgentResponse(messages);

        this.log("Agent975 procesó exitosamente", 'success');
        return response;
      } else {
        throw new Error(`Agent975 terminó con estado: ${runStatus.status}`);
      }

    } catch (error) {
      this.log(`Error con Agent975: ${error.message}`, 'error');
      throw error;
    }
  }

  async waitForCompletion(threadId, runId, maxAttempts = 30) {
    for (let i = 0; i < maxAttempts; i++) {
      const run = await this.aiClient.agents.getRun(threadId, runId);

      if (['completed', 'failed', 'cancelled', 'expired'].includes(run.status)) {
        return run;
      }

      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    throw new Error("Timeout esperando Agent975");
  }

  extractAgentResponse(messages) {
    const assistantMessages = messages.data
      .filter(m => m.role === 'assistant')
      .map(m => m.content
        .filter(c => c.type === 'text')
        .map(c => c.text.value)
        .join('\n')
      );

    return assistantMessages.join('\n\n');
  }

  // ============= PIPELINE BIDIRECCIONAL =============

  async executeFullPipeline(userRequest, options = {}) {
    this.log("═══════════════════════════════════════", 'info');
    this.log(`PIPELINE COMPLETO: ${userRequest}`, 'info');
    this.log("═══════════════════════════════════════", 'info');

    const results = {
      request: userRequest,
      timestamp: new Date().toISOString(),
      steps: []
    };

    try {
      // PASO 1: Interpretar con Agent975
      this.log("Paso 1: Interpretación con Agent975", 'agent');

      const interpretationPrompt = `
        Analiza esta solicitud del usuario y genera un comando JSON para el Copiloto Semántico:
        "${userRequest}"
        
        Responde SOLO con el JSON, sin texto adicional.
        Ejemplo: {"endpoint": "ejecutar", "method": "POST", "intencion": "dashboard"}
      `;

      const agentResponse = await this.processWithAgent975(interpretationPrompt);

      // Intentar parsear la respuesta
      let command;
      try {
        // Buscar JSON en la respuesta
        const jsonMatch = agentResponse.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          command = JSON.parse(jsonMatch[0]);
        } else {
          // Si no hay JSON, crear comando por defecto
          command = this.createDefaultCommand(userRequest);
        }
      } catch (e) {
        this.log("No se pudo parsear JSON del agente, usando comando por defecto", 'warning');
        command = this.createDefaultCommand(userRequest);
      }

      results.steps.push({
        step: "interpretation",
        agent: "Agent975",
        output: command
      });

      // PASO 2: Ejecutar en Copiloto
      this.log("Paso 2: Ejecución en Copiloto Semántico", 'copilot');

      const copilotoResponse = await this.invokeCopiloto(command);

      results.steps.push({
        step: "execution",
        system: "Copiloto",
        output: copilotoResponse
      });

      // PASO 3: Análisis de resultado (opcional)
      if (options.analyzeResult && copilotoResponse) {
        this.log("Paso 3: Análisis del resultado", 'agent');

        const analysisPrompt = `
          Analiza este resultado del Copiloto Semántico y proporciona:
          1. Un resumen ejecutivo
          2. Puntos clave
          3. Próximas acciones recomendadas
          
          Resultado:
          ${JSON.stringify(copilotoResponse, null, 2)}
        `;

        const analysis = await this.processWithAgent975(analysisPrompt);

        results.steps.push({
          step: "analysis",
          agent: "Agent975",
          output: analysis
        });
      }

      // PASO 4: Ejecutar acciones sugeridas (opcional)
      if (options.executeNextActions && copilotoResponse.proximas_acciones) {
        this.log("Paso 4: Ejecutando próximas acciones", 'info');

        for (const action of copilotoResponse.proximas_acciones.slice(0, 2)) {
          this.log(`Ejecutando: ${action}`, 'debug');

          const nextCommand = this.parseActionToCommand(action);
          if (nextCommand) {
            const nextResult = await this.invokeCopiloto(nextCommand);

            results.steps.push({
              step: "next_action",
              action: action,
              output: nextResult
            });
          }
        }
      }

      results.success = true;

    } catch (error) {
      results.success = false;
      results.error = error.message;
      this.log(`Error en pipeline: ${error.message}`, 'error');
    }

    return results;
  }

  createDefaultCommand(userRequest) {
    // Mapeo básico de intenciones
    const lowerRequest = userRequest.toLowerCase();

    if (lowerRequest.includes('dashboard')) {
      return {
        endpoint: "ejecutar",
        method: "POST",
        intencion: "dashboard",
        parametros: {}
      };
    } else if (lowerRequest.includes('estado') || lowerRequest.includes('status')) {
      return {
        endpoint: "status",
        method: "GET"
      };
    } else if (lowerRequest.includes('lee') || lowerRequest.includes('leer')) {
      const fileMatch = userRequest.match(/[\w\-]+\.\w+/);
      return {
        endpoint: "copiloto",
        method: "GET",
        mensaje: `leer:${fileMatch ? fileMatch[0] : 'archivo'}`
      };
    } else if (lowerRequest.includes('busca') || lowerRequest.includes('buscar')) {
      return {
        endpoint: "copiloto",
        method: "GET",
        mensaje: `buscar:*`
      };
    } else {
      return {
        endpoint: "ejecutar",
        method: "POST",
        intencion: "sugerir",
        parametros: { consulta: userRequest }
      };
    }
  }

  parseActionToCommand(action) {
    // Parsear acciones como "leer:archivo.py" a comandos
    if (action.startsWith('leer:')) {
      return {
        endpoint: "copiloto",
        method: "GET",
        mensaje: action
      };
    } else if (action.startsWith('analizar:')) {
      return {
        endpoint: "copiloto",
        method: "GET",
        mensaje: action
      };
    } else if (action.startsWith('buscar:')) {
      return {
        endpoint: "copiloto",
        method: "GET",
        mensaje: action
      };
    } else if (action.includes(':')) {
      const [intencion, ...resto] = action.split(':');
      return {
        endpoint: "ejecutar",
        method: "POST",
        intencion: action,
        parametros: {}
      };
    }

    return null;
  }

  // ============= PRUEBAS Y VERIFICACIÓN =============

  async testConnectivity() {
    this.log("Verificando conectividad...", 'info');

    const tests = [];

    // Test 1: Copiloto Health
    try {
      const health = await this.invokeCopiloto({ endpoint: 'health', method: 'GET' });
      tests.push({
        component: "Copiloto Health",
        status: health.status === 'healthy' ? '✅' : '⚠️',
        details: health.version
      });
    } catch (e) {
      tests.push({
        component: "Copiloto Health",
        status: '❌',
        details: e.message
      });
    }

    // Test 2: Copiloto Status
    if (this.masterKey) {
      try {
        const status = await this.invokeCopiloto({ endpoint: 'status', method: 'GET' });
        tests.push({
          component: "Copiloto Status",
          status: '✅',
          details: status.version
        });
      } catch (e) {
        tests.push({
          component: "Copiloto Status",
          status: '❌',
          details: e.message
        });
      }
    }

    // Test 3: Agent975
    try {
      const agent = await this.aiClient.agents.getAgent(this.agent975Config.agentId);
      tests.push({
        component: "Agent975",
        status: '✅',
        details: agent.name || this.agent975Config.agentId
      });
    } catch (e) {
      tests.push({
        component: "Agent975",
        status: '❌',
        details: e.message
      });
    }

    // Mostrar resultados
    console.table(tests);

    const allOk = tests.every(t => t.status !== '❌');
    if (!allOk) {
      this.log("Algunos componentes no están disponibles", 'warning');
    }

    return tests;
  }

  async runTestScenarios() {
    this.log("🧪 EJECUTANDO ESCENARIOS DE PRUEBA", 'info');

    const scenarios = [
      {
        name: "Estado del sistema",
        request: "muéstrame el estado del sistema",
        options: {}
      },
      {
        name: "Dashboard con análisis",
        request: "quiero ver el dashboard",
        options: { analyzeResult: true }
      },
      {
        name: "Leer archivo",
        request: "lee el archivo function_app.py",
        options: {}
      },
      {
        name: "Búsqueda con acciones",
        request: "busca archivos python en el proyecto",
        options: { executeNextActions: true }
      }
    ];

    const results = [];

    for (const scenario of scenarios) {
      this.log(`\n📝 Escenario: ${scenario.name}`, 'info');

      try {
        const result = await this.executeFullPipeline(
          scenario.request,
          scenario.options
        );

        results.push({
          scenario: scenario.name,
          status: result.success ? '✅' : '❌',
          steps: result.steps.length,
          time: new Date().toISOString()
        });

        if (this.debug) {
          console.log("Resultado completo:", JSON.stringify(result, null, 2));
        }

      } catch (error) {
        results.push({
          scenario: scenario.name,
          status: '❌',
          error: error.message
        });
      }

      // Pausa entre escenarios
      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    this.log("\n📊 RESULTADOS DE PRUEBAS:", 'info');
    console.table(results);

    return results;
  }
}

// ============= FUNCIÓN PRINCIPAL =============

async function main() {
  const connector = new Agent975CopilotoConnector();

  try {
    // Inicializar
    await connector.initialize();

    // Verificar argumentos
    const args = process.argv.slice(2);

    if (args.includes('--test')) {
      // Modo prueba completa
      await connector.runTestScenarios();

    } else if (args.includes('--check')) {
      // Solo verificar conectividad
      await connector.testConnectivity();

    } else if (args.includes('--execute')) {
      // Ejecutar solicitud específica
      const requestIndex = args.indexOf('--execute') + 1;
      const request = args[requestIndex] || "muéstrame el dashboard";

      const result = await connector.executeFullPipeline(request, {
        analyzeResult: true,
        executeNextActions: false
      });

      console.log("\n📋 RESULTADO FINAL:");
      console.log(JSON.stringify(result, null, 2));

    } else {
      // Modo interactivo
      console.log(`
╔══════════════════════════════════════════════════════════╗
║     🤖 CONECTOR AGENT975 ↔ COPILOTO SEMÁNTICO          ║
║                    Versión 2.0                           ║
╚══════════════════════════════════════════════════════════╝

USO:
  node agent975-connector.mjs [opciones]

OPCIONES:
  --test              Ejecutar todos los escenarios de prueba
  --check             Solo verificar conectividad
  --execute "texto"   Ejecutar una solicitud específica

EJEMPLOS:
  node agent975-connector.mjs --test
  node agent975-connector.mjs --execute "lee function_app.py"
  node agent975-connector.mjs --check

`);

      // Ejecutar un ejemplo
      await connector.testConnectivity();
    }

    console.log("\n✅ Proceso completado");

  } catch (error) {
    console.error("\n❌ Error fatal:", error.message);
    if (connector.debug) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

// Ejecutar si es el módulo principal
main();


export default Agent975CopilotoConnector;