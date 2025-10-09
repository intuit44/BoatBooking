# 🔍 Detección Inteligente de Argumentos Faltantes

## 📋 Funcionalidad Implementada

El endpoint `/api/ejecutar-cli` ahora detecta automáticamente cuando un comando Azure CLI falla por argumentos faltantes y proporciona sugerencias inteligentes para resolverlo.

## 🎯 Casos Soportados

### 1. Resource Group Faltante
```bash
# Comando con argumento faltante
POST /api/ejecutar-cli
{
  "comando": "az cosmosdb sql database list --account-name copiloto-cosmos"
}

# Respuesta con detección inteligente
{
  "exito": false,
  "comando": "az cosmosdb sql database list --account-name copiloto-cosmos",
  "error": "argument --resource-group/-g: expected one argument",
  "codigo_salida": 2,
  "diagnostico": {
    "argumento_faltante": "--resource-group",
    "descripcion": "Este comando requiere especificar el grupo de recursos",
    "sugerencia_automatica": "¿Quieres que liste los grupos de recursos disponibles?",
    "comando_para_listar": "az group list --output table",
    "valores_comunes": ["boat-rental-app-group", "boat-rental-rg", "DefaultResourceGroup-EUS2"]
  },
  "accion_sugerida": "Ejecutar: az group list --output table para obtener valores disponibles"
}
```

### 2. Account Name Faltante
```bash
# Comando con argumento faltante
POST /api/ejecutar-cli
{
  "comando": "az storage account show"
}

# Respuesta con detección inteligente
{
  "exito": false,
  "comando": "az storage account show",
  "error": "Storage account name is required",
  "codigo_salida": 2,
  "diagnostico": {
    "argumento_faltante": "--account-name",
    "descripcion": "Este comando requiere el nombre de la cuenta de almacenamiento",
    "sugerencia_automatica": "¿Quieres que liste las cuentas de almacenamiento disponibles?",
    "comando_para_listar": "az storage account list --output table",
    "valores_comunes": ["boatrentalstorage", "copilotostorage"]
  },
  "accion_sugerida": "Ejecutar: az storage account list --output table para obtener valores disponibles"
}
```

### 3. Function App Name Faltante
```bash
# Comando con argumento faltante
POST /api/ejecutar-cli
{
  "comando": "az functionapp show --resource-group boat-rental-rg"
}

# Respuesta con detección inteligente
{
  "exito": false,
  "comando": "az functionapp show --resource-group boat-rental-rg",
  "error": "Function app name is required",
  "codigo_salida": 2,
  "diagnostico": {
    "argumento_faltante": "--name",
    "descripcion": "Este comando requiere el nombre de la aplicación",
    "sugerencia_automatica": "¿Quieres que liste las aplicaciones disponibles?",
    "comando_para_listar": "az functionapp list --output table",
    "valores_comunes": ["copiloto-semantico-func-us2", "boat-rental-app"]
  },
  "accion_sugerida": "Ejecutar: az functionapp list --output table para obtener valores disponibles"
}
```

## 🔧 Argumentos Detectados

| Argumento | Patrones de Detección | Comando Sugerido | Valores Comunes |
|-----------|----------------------|------------------|-----------------|
| `--resource-group` | "resource group", "--resource-group", "-g" | `az group list --output table` | boat-rental-app-group, boat-rental-rg |
| `--account-name` | "account name", "--account-name", "storage account" | `az storage account list --output table` | boatrentalstorage, copilotostorage |
| `--name` | "function app name", "--name", "app name" | `az functionapp list --output table` | copiloto-semantico-func-us2 |
| `--subscription` | "subscription", "--subscription", "subscription id" | `az account list --output table` | - |
| `--location` | "location", "--location", "region" | `az account list-locations --output table` | eastus, eastus2, westus2 |

## 🎯 Casos Especiales

### Cosmos DB
```bash
# Detecta automáticamente comandos de Cosmos DB
POST /api/ejecutar-cli
{
  "comando": "az cosmosdb list"
}

# Si falla por account-name, sugiere comando específico de Cosmos DB
{
  "diagnostico": {
    "argumento_faltante": "--account-name",
    "comando_para_listar": "az cosmosdb list --output table",
    "valores_comunes": ["copiloto-cosmos", "boat-rental-cosmos"]
  }
}
```

### Storage Containers
```bash
# Detecta comandos de contenedores de storage
POST /api/ejecutar-cli
{
  "comando": "az storage container show"
}

# Sugiere listar contenedores
{
  "diagnostico": {
    "argumento_faltante": "--container-name",
    "comando_para_listar": "az storage container list --account-name <account-name> --output table",
    "valores_comunes": ["boat-rental-project", "scripts", "backups"]
  }
}
```

## 🚀 Flujo de Uso Recomendado

1. **Ejecutar comando incompleto**: El agente ejecuta el comando tal como lo recibe
2. **Detectar argumento faltante**: El sistema identifica qué argumento falta
3. **Sugerir comando de listado**: Proporciona el comando para obtener valores válidos
4. **Ejecutar comando sugerido**: El agente puede ejecutar el comando de listado
5. **Completar comando original**: Con el valor obtenido, ejecutar el comando completo

## 📊 Beneficios

| Ventaja | Descripción |
|---------|-------------|
| 🔍 **Detección Automática** | El sistema sabe qué falta sin intervención del usuario |
| 🧠 **Flujos Inteligentes** | Puede activar grounding, sugerencias, completar automáticamente |
| 🤖 **Agente Proactivo** | El agente actúa como copiloto real, no como asistente pasivo |
| 🧪 **Tests Mejorados** | Facilita test semánticos incluso con comandos incompletos |

## 🔄 Compatibilidad

- ✅ **Mantiene funcionalidad existente**: Comandos completos siguen funcionando igual
- ✅ **No rompe agentes**: Los agentes existentes reciben información adicional útil
- ✅ **Extensible**: Fácil agregar nuevos patrones de detección
- ✅ **Configurable**: Los valores comunes se pueden personalizar por proyecto

## 🎯 Resultado Final

El endpoint `/api/ejecutar-cli` ahora es un **copiloto inteligente** que:
- Ejecuta cualquier comando sin rechazar
- Detecta problemas automáticamente
- Sugiere soluciones específicas
- Guía al usuario hacia la resolución
- Mantiene compatibilidad total con uso existente