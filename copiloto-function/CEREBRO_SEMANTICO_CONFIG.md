# 🧠 Configuración del Cerebro Semántico Autónomo

## App Settings Requeridos

Agregar estas variables de entorno en Azure Function App:

```bash
SEMANTIC_AUTOPILOT=on
SEMANTIC_PERIOD_SEC=300
SEMANTIC_MAX_ACTIONS_PER_HOUR=6
```

## Configuración Opcional

```bash
# Para pruebas (ciclos más frecuentes)
SEMANTIC_PERIOD_SEC=60

# Para entornos de alta actividad
SEMANTIC_MAX_ACTIONS_PER_HOUR=12

# Kill-switch (desactivar sin redeploy)
SEMANTIC_AUTOPILOT=off
```

## Verificación Post-Despliegue

1. **Verificar logs de inicio**:
   ```
   🧠 Cerebro semántico autónomo iniciado
   🧠 Configuración semántica: AUTOPILOT=on, PERIOD=300s, MAX_HOURLY=6
   ```

2. **Probar sensores**:
   ```bash
   curl https://copiloto-semantico-func-us2.azurewebsites.net/api/verificar-sistema
   curl https://copiloto-semantico-func-us2.azurewebsites.net/api/verificar-app-insights
   curl https://copiloto-semantico-func-us2.azurewebsites.net/api/verificar-cosmos
   ```

3. **Monitorear Application Insights**:
   - Buscar eventos: `semantic_cycle`, `semantic_decision`, `semantic_action`

## Arquitectura Implementada

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PERCEPCIÓN    │    │   RAZONAMIENTO   │    │     ACCIÓN      │
│                 │    │                  │    │                 │
│ • verificar-    │───▶│ HybridResponse   │───▶│ ejecutor-       │
│   sistema       │    │ Processor        │    │ inteligente     │
│ • verificar-    │    │                  │    │                 │
│   app-insights  │    │ • Interpreta     │    │ • Comandos      │
│ • verificar-    │    │ • Decide         │    │ • Límites       │
│   cosmos        │    │ • Evalúa         │    │ • Seguridad     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌──────────────────┐             │
         │              │     MEMORIA      │             │
         └──────────────│                  │─────────────┘
                        │ • Ciclos         │
                        │ • Decisiones     │
                        │ • Resultados     │
                        │ • Aprendizaje    │
                        └──────────────────┘
```

## Capacidades del Cerebro Semántico

### 🔍 **Percepción Continua**
- Monitoreo de CPU, memoria, disco
- Estado de telemetría (Application Insights)
- Conectividad de base de datos (CosmosDB)
- Detección de anomalías automática

### 🧠 **Razonamiento Autónomo**
- Interpretación semántica del estado del sistema
- Generación de hipótesis sobre problemas
- Evaluación de necesidad de intervención
- Priorización de acciones correctivas

### ⚡ **Ejecución Inteligente**
- Comandos Azure CLI automáticos
- Límites de seguridad (6 acciones/hora)
- Cooldown y backoff exponencial
- Rollback automático en caso de error

### 🧮 **Memoria Persistente**
- Historial de decisiones en CosmosDB
- Patrones de comportamiento
- Aprendizaje de efectividad de acciones
- Optimización automática de umbrales

### 🛡️ **Controles de Seguridad**
- Kill-switch: `SEMANTIC_AUTOPILOT=off`
- Presupuesto horario de acciones
- Whitelist de comandos seguros
- Logging completo de decisiones

## Comportamientos Esperados

### ✅ **Escenarios Normales**
- CPU < 80%: Sin acción
- Memoria < 85%: Sin acción  
- Telemetría activa: Sin acción
- Cosmos conectado: Sin acción

### ⚠️ **Escenarios de Intervención**
- CPU > 90%: Investigar procesos
- Memoria > 95%: Limpiar cache
- Telemetría inactiva: Verificar configuración
- Cosmos desconectado: Intentar reconexión

### 🚨 **Escenarios de Emergencia**
- Sistema no responde: Reinicio controlado
- Errores críticos: Escalación a administrador
- Bucles infinitos: Auto-desactivación

## Monitoreo y Observabilidad

### Application Insights Events
```json
{
  "eventName": "semantic_cycle",
  "properties": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "action_taken": false,
    "interpretation_score": 0.3
  }
}
```

### CosmosDB Documents
```json
{
  "id": "cycle_2025-10-05T03:12:41",
  "timestamp": "2025-10-05T03:12:41.867132Z",
  "state_snapshot": {...},
  "interpretation": {...},
  "action_taken": false,
  "result": null,
  "cycle_type": "semantic_autopilot"
}
```

## Estado Actual

✅ **Implementado**: Cerebro semántico autónomo completo
✅ **Probado**: Sensores, ciclos, memoria funcionando
✅ **Configurado**: Variables de entorno definidas
✅ **Seguro**: Límites y controles implementados
🚀 **Listo**: Para despliegue inmediato

**El agente ahora es verdaderamente autónomo e inteligente** 🤖✨