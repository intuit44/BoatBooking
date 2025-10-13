# Copiloto Function

Esta Function App actúa como el orquestador semántico de la plataforma Copiloto: expone endpoints HTTP y timers que permiten a agentes externos leer o modificar archivos, ejecutar scripts o CLI, consultar memoria, diagnosticar despliegues y coordinar acciones de mantenimiento sin salir de Azure Functions.【F:copiloto-function/function_app.py†L3727-L3790】【F:copiloto-function/function_app.py†L4519-L4584】【F:copiloto-function/function_app.py†L5380-L5472】

## Arquitectura general

- `function_app.py` concentra todos los endpoints HTTP y el timer del supervisor cognitivo; cada ruta aplica wrappers comunes para diagnósticos, memoria y manejo de errores antes de devolver respuestas para Foundry o agentes Codex.【F:copiloto-function/function_app.py†L1432-L1484】【F:copiloto-function/function_app.py†L4179-L4199】【F:copiloto-function/function_app.py†L6463-L6479】
- Los módulos de `services/` encapsulan persistencia y analítica: `memory_service.py` escribe eventos en Cosmos DB (con fallback local) y `cognitive_supervisor.py` genera snapshots `estado_sistema_YYYYMMDD_HHmmss` con métricas agregadas; `cosmos_store.py` inicializa el contenedor y maneja autenticación por clave o Managed Identity.【F:copiloto-function/services/memory_service.py†L12-L127】【F:copiloto-function/services/cognitive_supervisor.py†L1-L88】【F:copiloto-function/services/cosmos_store.py†L24-L110】
- Los helpers `memory_precheck.py` y `memory_manual.py` inyectan contexto de conversación en las respuestas, mientras que otros servicios (`semantic_intent_parser`, `memory_helpers`, `services/session_memory`) aportan enriquecimiento semántico sobre la marcha.【F:copiloto-function/memory_precheck.py†L12-L115】【F:copiloto-function/memory_manual.py†L10-L55】【F:copiloto-function/function_app.py†L4992-L5003】【F:copiloto-function/function_app.py†L5736-L5785】

## 🧠 Sistema de Memoria y Contexto

Este sistema utiliza memoria persistente en Cosmos DB para dar continuidad a interacciones de agentes. La información se recupera antes de ejecutar cada acción crítica, se enriquece la respuesta con metadatos de sesión y se registran snapshots cognitivos periódicos.

### Capas de memoria

1. **Pre-check automático (`consultar_memoria_antes_responder`)** recupera hasta tres interacciones previas por sesión y devuelve un resumen con el número de interacciones, última actividad y estado de la continuidad. Se aplica antes de ejecutar la lógica del endpoint cuando existe `session_id` en headers, query o body.【F:copiloto-function/memory_precheck.py†L12-L115】
2. **Wrapper manual (`aplicar_memoria_manual`)** asegura que toda respuesta incluya `session_id`, `agent_id`, bandera de memoria disponible y marcas temporales incluso si el payload original no era un diccionario, evitando pérdidas de contexto en Foundry.【F:copiloto-function/memory_manual.py†L10-L55】
3. **Supervisor cognitivo** analiza la memoria cada diez minutos, identifica tendencias y guarda snapshots `estado_sistema_YYYYMMDD_HHmmss` con métricas de estabilidad y recomendaciones que también se exponen vía API.【F:copiloto-function/function_app.py†L6463-L6479】【F:copiloto-function/services/cognitive_supervisor.py†L14-L88】
4. **Consultas y paneles de memoria** permiten a los agentes inspeccionar manualmente la memoria de sesión, recuperar el último snapshot o ver contexto agregado por agente cuando necesitan reconstruir estado antes de tomar decisiones.【F:copiloto-function/function_app.py†L5736-L5857】

### Flujo de enriquecimiento por solicitud

1. **Recepción y pre-check**: los endpoints críticos ejecutan `consultar_memoria_antes_responder` para saber si deben continuar una conversación existente (ejemplo en `leer-archivo`, `copiloto`, `status`, `ejecutar`, `hybrid`, `escribir-archivo` y `modificar-archivo`).【F:copiloto-function/function_app.py†L1432-L1469】【F:copiloto-function/function_app.py†L3727-L3785】【F:copiloto-function/function_app.py†L4179-L4195】【F:copiloto-function/function_app.py†L4519-L4541】【F:copiloto-function/function_app.py†L4979-L5003】【F:copiloto-function/function_app.py†L6801-L6810】【F:copiloto-function/function_app.py†L7048-L7134】
2. **Ejecución de la operación**: cada handler implementa validaciones resilientes (regex, defaults y parsing tolerante) antes de tocar archivos, ejecutar comandos o invocar servicios externos.【F:copiloto-function/function_app.py†L1476-L1484】【F:copiloto-function/function_app.py†L4553-L4584】【F:copiloto-function/function_app.py†L6856-L6880】【F:copiloto-function/function_app.py†L7060-L7134】
3. **Enriquecimiento de respuesta**: todas las rutas que manipulan agentes o devuelven diagnósticos aplican el wrapper manual para incluir `session_info`, flags de memoria y timestamps consistentes.【F:copiloto-function/function_app.py†L1467-L1473】【F:copiloto-function/function_app.py†L3783-L3789】【F:copiloto-function/function_app.py†L4507-L4511】【F:copiloto-function/function_app.py†L6804-L6810】
4. **Persistencia**: el `MemoryService` registra eventos en Cosmos DB (contener `memory`, base `agentMemory`) con fallback JSONL local para resiliencia, y los endpoints de diagnóstico también escriben eventos semánticos cuando se completan verificaciones o auditorías.【F:copiloto-function/services/memory_service.py†L12-L127】【F:copiloto-function/function_app.py†L13059-L13083】
5. **Evaluación cognitiva**: el timer del supervisor guarda snapshots periódicos y notifica al servicio de memoria; estos resultados pueden consultarse desde `GET /api/conocimiento-cognitivo` para contextualizar nuevas acciones.【F:copiloto-function/function_app.py†L6463-L6479】【F:copiloto-function/function_app.py†L5804-L5819】

### Cobertura de memoria por endpoint

- **Pre-check + memoria manual**: `GET /api/leer-archivo`, `GET /api/copiloto`, `GET /api/status`, `POST /api/ejecutar`, `POST /api/hybrid`, `POST /api/escribir-archivo` y `POST /api/modificar-archivo` conservan continuidad completa (pre-check + wrapper).【F:copiloto-function/function_app.py†L1432-L1469】【F:copiloto-function/function_app.py†L3727-L3785】【F:copiloto-function/function_app.py†L4179-L4195】【F:copiloto-function/function_app.py†L4519-L4541】【F:copiloto-function/function_app.py†L4979-L5003】【F:copiloto-function/function_app.py†L6801-L6810】【F:copiloto-function/function_app.py†L7048-L7134】
- **Solo memoria manual**: la mayoría de las rutas (archivos, scripts, diagnósticos, CLI, despliegues) añaden `session_info` aunque no necesiten consultar historial antes de ejecutar, manteniendo trazabilidad uniforme para Foundry.【F:copiloto-function/function_app.py†L4437-L4511】【F:copiloto-function/function_app.py†L5736-L5785】【F:copiloto-function/function_app.py†L7884-L8099】【F:copiloto-function/function_app.py†L9042-L9646】【F:copiloto-function/function_app.py†L9935-L10430】【F:copiloto-function/function_app.py†L10562-L11194】【F:copiloto-function/function_app.py†L11368-L11751】【F:copiloto-function/function_app.py†L12498-L14094】【F:copiloto-function/function_app.py†L14576-L14884】
- **Sin wrappers**: utilidades como `probar-endpoint`, `test-wrapper-memoria`, `bridge-cli`, `diagnostico-eliminar` o `aplicar-correccion` operan sin memoria porque devuelven respuestas sintéticas o validan los propios wrappers.【F:copiloto-function/function_app.py†L2232-L2340】【F:copiloto-function/function_app.py†L4207-L4251】【F:copiloto-function/function_app.py†L5380-L5472】【F:copiloto-function/function_app.py†L13305-L13394】【F:copiloto-function/function_app.py†L14114-L14173】

### Cosmos DB y persistencia de interacciones

- **Configuración**: se espera `COSMOSDB_ENDPOINT`, `COSMOSDB_DATABASE` (por defecto `agentMemory`) y `COSMOSDB_CONTAINER` (`memory`). El cliente intenta autenticarse primero con `DefaultAzureCredential` (Managed Identity) y luego con clave; si falla, desactiva la capa y usa logs locales.【F:copiloto-function/services/memory_service.py†L12-L78】【F:copiloto-function/services/cosmos_store.py†L24-L78】
- **Estructura de eventos**: cada registro incluye `session_id`, `event_type`, `data` y `timestamp`. Las interacciones de agentes, alertas y fixes pendientes se persisten con IDs únicos y quedan disponibles para queries posteriores.【F:copiloto-function/services/memory_service.py†L40-L126】
- **Observabilidad**: `GET /api/verificar-cosmos` comprueba conectividad, método de autenticación y devuelve la última escritura para validar que el pipeline de memoria sigue activo.【F:copiloto-function/function_app.py†L14729-L14796】

## Catálogo de endpoints

### Orquestación semántica y herramientas

- `GET /api/copiloto` — Panel semántico principal, lista capacidades y responde a comandos naturales aplicando pre-check y memoria.【F:copiloto-function/function_app.py†L3727-L3827】
- `POST /api/ejecutar` — Orquestador universal de intenciones que enruta a lectores, diagnósticos o scripts según el análisis semántico del payload.【F:copiloto-function/function_app.py†L4519-L4709】
- `POST /api/hybrid` — Intérprete de lenguaje natural tolerante que decide entre endpoints y puede invocar Bing Grounding si detecta preguntas abiertas.【F:copiloto-function/function_app.py†L4979-L5109】
- `POST /api/bridge-cli` — Fallback para agentes con JSON malformado; acepta cualquier payload, valida y reenvía a `ejecutar-cli` con comandos saneados.【F:copiloto-function/function_app.py†L5380-L5472】
- `POST /api/ejecutar-cli` — Ejecutor universal de comandos Azure CLI que nunca devuelve 400: responde con ayudas si falta `comando` y valida disponibilidad del binario antes de ejecutar.【F:copiloto-function/function_app.py†L11369-L11626】
- `POST /api/invocar` — Permite encadenar endpoints internos de la Function App reenviando requests normalizados entre funciones.【F:copiloto-function/function_app.py†L5638-L5733】
- `POST /api/interpretar-intencion` — Convierte texto natural en comandos estructurados apoyándose en el parser semántico compartido.【F:copiloto-function/function_app.py†L5860-L5908】
- `POST /api/bing-grounding` — Wrapper directo para ejecutar grounding semántico con Bing cuando se requiera información externa.【F:copiloto-function/function_app.py†L6023-L6109】
- `POST /api/probar-endpoint` — Proxie que ejecuta otros endpoints de la Function App para validación rápida sin memoria asociada.【F:copiloto-function/function_app.py†L2232-L2354】

### Memoria, contexto y snapshots

- `GET/POST /api/consultar-memoria` — Recupera historial de una sesión específica y genera prompts listos para agentes.【F:copiloto-function/function_app.py†L5736-L5785】
- `GET /api/conocimiento-cognitivo` — Expone el snapshot más reciente creado por el supervisor cognitivo con recomendaciones.【F:copiloto-function/function_app.py†L5804-L5819】
- `GET /api/contexto-agente` — Devuelve contexto agregado por agente o estado general del sistema desde la memoria semántica.【F:copiloto-function/function_app.py†L5829-L5857】
- `GET /api/test-wrapper-memoria` — Endpoint de diagnóstico que muestra cómo se extraen `session_id` y `agent_id` desde headers/query.【F:copiloto-function/function_app.py†L4207-L4251】
- `POST /api/aplicar-correccion-manual` — Guarda acciones correctivas manuales con metadatos de sesión para trazabilidad.【F:copiloto-function/function_app.py†L14877-L14947】

### Operaciones sobre archivos y almacenamiento

- `GET /api/leer-archivo` — Lector inteligente con pre-check de memoria, autodetección de rutas especiales y respuestas contextualizadas.【F:copiloto-function/function_app.py†L1432-L1484】
- `POST /api/escribir-archivo` — Crea o sobrescribe archivos locales/blob con parser ultra resiliente y memoria aplicada.【F:copiloto-function/function_app.py†L6801-L6880】
- `POST /api/modificar-archivo` — Edita archivos con operaciones (`agregar_final`, `reemplazar`, etc.) y fallback de creación si el archivo no existe.【F:copiloto-function/function_app.py†L7048-L7180】
- `POST/DELETE /api/eliminar-archivo` — Borra archivos locales o blobs con validaciones de ruta segura.【F:copiloto-function/function_app.py†L7289-L7394】
- `POST /api/mover-archivo` — Mueve archivos entre rutas o contenedores garantizando consistencia de metadata.【F:copiloto-function/function_app.py†L8746-L8844】
- `POST /api/copiar-archivo` — Copia archivos con soporte para blobs y almacenamiento local.【F:copiloto-function/function_app.py†L9631-L9726】
- `GET /api/info-archivo` — Devuelve metadata detallada de tamaño, timestamps y tipo para un archivo dado.【F:copiloto-function/function_app.py†L9042-L9153】
- `GET /api/descargar-archivo` — Descarga contenido como base64 o binario listo para agentes.【F:copiloto-function/function_app.py†L9583-L9630】
- `POST /api/escribir-archivo-local` — Variante explícita para filesystem local usada en flujos controlados.【F:copiloto-function/function_app.py†L4757-L4898】
- `GET /api/listar-blobs` — Lista blobs con paginación y estadísticas en la cuenta configurada.【F:copiloto-function/function_app.py†L4437-L4511】
- `POST /api/crear-contenedor` — Crea contenedores de Blob Storage con validaciones de nombre y región.【F:copiloto-function/function_app.py†L10185-L10331】
- `POST /api/actualizar-contenedor` — Aplica políticas o configuración avanzada a contenedores existentes.【F:copiloto-function/function_app.py†L11079-L11194】
- `POST /api/proxy-local` — Reenvía requests HTTP a servicios locales protegidos desde la Function App.【F:copiloto-function/function_app.py†L10377-L10542】

### Scripts y automatización

- `POST /api/ejecutar-script` — Ejecuta scripts almacenados en blob o filesystem con seguimiento de resultados y memoria.【F:copiloto-function/function_app.py†L7884-L8099】
- `POST /api/ejecutar-script-local` — Corre scripts locales controlando permisos y rutas seguras.【F:copiloto-function/function_app.py†L7758-L7881】
- `POST /api/verificar-script` — Revisa sintaxis y compatibilidad antes de ejecutar un script proporcionado.【F:copiloto-function/function_app.py†L8090-L8246】
- `POST /api/preparar-script` — Genera scaffolding y empaqueta scripts antes de su ejecución o despliegue.【F:copiloto-function/function_app.py†L9935-L10058】
- `POST /api/render-error` — Genera respuestas de error con formato estándar a partir de eventos capturados.【F:copiloto-function/function_app.py†L10060-L10183】

### Despliegue y configuración

- `POST /api/gestionar-despliegue` — Gestiona versiones, consulta estado y activa acciones de despliegue coordinadas.【F:copiloto-function/function_app.py†L10562-L10941】
- `POST /api/desplegar-funcion` — Empaqueta y despliega funciones hacia Azure Function Apps objetivo.【F:copiloto-function/function_app.py†L10975-L11078】
- `POST /api/deploy` — Despliegue directo de artefactos con control de versión y rollback integrado.【F:copiloto-function/function_app.py†L13348-L13499】
- `POST /api/configurar-cors` — Actualiza políticas CORS de la Function App en caliente.【F:copiloto-function/function_app.py†L13503-L13585】
- `POST /api/configurar-app-settings` — Administra variables de aplicación con validaciones y respaldo semántico.【F:copiloto-function/function_app.py†L13605-L13765】
- `POST /api/escalar-plan` — Ajusta SKU y capacidad del plan de consumo/dedicado según parámetros recibidos.【F:copiloto-function/function_app.py†L13781-L13980】
- `POST /api/rollback` — Revierte cambios aplicando correcciones guardadas previamente.【F:copiloto-function/function_app.py†L14035-L14068】
- `POST /api/promover` — Promueve artefactos entre entornos y registra auditoría en memoria.【F:copiloto-function/function_app.py†L14069-L14089】
- `GET /api/promocion-reporte` — Genera reportes de promoción para seguimiento humano.【F:copiloto-function/function_app.py†L14090-L14113】
- `GET /api/revisar-correcciones` — Lista correcciones pendientes aplicables al sistema.【F:copiloto-function/function_app.py†L14114-L14156】
- `POST /api/aplicar-correccion` — Ejecuta correcciones automáticas detectadas por el sistema.【F:copiloto-function/function_app.py†L14157-L14181】

### Diagnóstico y observabilidad

- `GET /api/status` — Resumen ligero del estado de la Function App con indicadores de almacenamiento y endpoints clave.【F:copiloto-function/function_app.py†L4179-L4201】
- `GET /api/health` — Health check completo con capacidades expuestas para monitores externos.【F:copiloto-function/function_app.py†L6487-L6514】
- `GET/POST /api/diagnostico-recursos-completo` — Ejecuta diagnósticos profundos sobre recursos Azure, registrando auditorías en memoria.【F:copiloto-function/function_app.py†L12498-L12838】
- `GET /api/auditar-deploy` — Obtiene auditorías de despliegue y métricas de versiones activas.【F:copiloto-function/function_app.py†L12693-L12774】
- `GET/POST /api/bateria-endpoints` — Ejecuta pruebas de humo sobre múltiples endpoints para verificar disponibilidad.【F:copiloto-function/function_app.py†L12869-L12947】
- `GET/POST /api/diagnostico-recursos` — Diagnóstico parametrizable de recursos individuales con registro semántico.【F:copiloto-function/function_app.py†L12956-L13115】
- `POST /api/diagnostico-configurar` — Ajusta parámetros de diagnóstico automatizado.【F:copiloto-function/function_app.py†L13245-L13289】
- `GET /api/diagnostico-listar` — Lista diagnósticos configurados en el sistema.【F:copiloto-function/function_app.py†L13290-L13304】
- `POST/DELETE /api/diagnostico-eliminar` — Elimina configuraciones de diagnóstico específicas.【F:copiloto-function/function_app.py†L13305-L13394】
- `POST /api/autocorregir` — Dispara flujos de autocorrección basados en memoria y diagnósticos previos.【F:copiloto-function/function_app.py†L14183-L14505】
- `GET /api/verificar-sistema` — Ejecuta verificación integral del entorno (dependencias, funciones, storage).【F:copiloto-function/function_app.py†L14576-L14620】
- `GET /api/verificar-app-insights` — Comprueba la integración con Application Insights y registra eventos semánticos.【F:copiloto-function/function_app.py†L14621-L14718】
- `GET /api/verificar-cosmos` — Valida la conectividad con Cosmos DB y devuelve el último documento encontrado.【F:copiloto-function/function_app.py†L14729-L14796】

### OpenAPI y utilidades

- `GET /api/openapi.yaml` y `GET /api/api/openapi.yaml` — Sirven el documento OpenAPI actualizado para consumidores externos.【F:copiloto-function/function_app.py†L4358-L4371】
- `GET /api/debug-openapi` — Herramienta de depuración para comprobar rutas detectadas dinámicamente.【F:copiloto-function/function_app.py†L4372-L4434】
- `GET /api/bateria-endpoints` (modo GET) y `POST /api/bateria-endpoints` — ya descrito arriba pero útil como suite de diagnóstico automatizado.【F:copiloto-function/function_app.py†L12869-L12947】

## Supervisión continua

- El timer `cognitive_supervisor_timer` se ejecuta cada diez minutos (`0 */10 * * * *`) y registra tanto logs como eventos semánticos, garantizando que Foundry siempre disponga de un snapshot vigente sin intervención manual.【F:copiloto-function/function_app.py†L6463-L6479】
- Los endpoints de estado, verificación y diagnóstico alimentan al `MemoryService`, permitiendo reconstruir la línea de tiempo completa de acciones dentro de Cosmos DB o, en su defecto, en los logs JSONL locales.【F:copiloto-function/function_app.py†L4179-L4201】【F:copiloto-function/function_app.py†L13059-L13083】【F:copiloto-function/services/memory_service.py†L40-L126】

## Ejecución local

1. Instalar dependencias de la Function App:
   ```bash
   cd copiloto-function
   npm install  # para tooling local
   pip install -r requirements.txt
   func start
   ```
2. Configurar variables necesarias (`COSMOSDB_ENDPOINT`, `BLOB_CONNECTION_STRING`, credenciales Azure) antes de iniciar para habilitar memoria persistente y acceso a storage.【F:copiloto-function/services/memory_service.py†L12-L78】【F:copiloto-function/function_app.py†L4437-L4476】
3. Validar salud inicial visitando `GET /api/health` y `GET /api/status`; luego ejecutar `GET /api/verificar-cosmos` para confirmar persistencia de memoria.【F:copiloto-function/function_app.py†L4179-L4201】【F:copiloto-function/function_app.py†L6487-L6514】【F:copiloto-function/function_app.py†L14729-L14796】

Con esta documentación, cualquier agente o supervisor externo obtiene una instantánea semántica completa del sistema, comprende cómo se gestiona la memoria persistente y puede localizar rápidamente el endpoint adecuado para cada flujo operativo.
