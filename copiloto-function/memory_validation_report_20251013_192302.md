
# 📊 REPORTE DE VALIDACIÓN DE MEMORIA
**Fecha:** 2025-10-13 19:23:02
**Endpoints probados:** 7

## 📈 Resumen General

- ✅ **Endpoints funcionando:** 6/7
- 🧠 **Con integración de memoria:** 6/7
- 📊 **Tasa de éxito:** 85.7%
- 🎯 **Memoria integrada:** 85.7%

## 📋 Detalle por Endpoint

### ✅ copiloto
- **URL:** /api/copiloto
- **Status:** 200
- **Tiempo:** 2.33s
- **Memoria:** 🧠 Integrada
- **Campos encontrados:** metadata.session_info, metadata.session_info.session_id, metadata.memoria_disponible

### ✅ status
- **URL:** /api/status
- **Status:** 200
- **Tiempo:** 2.23s
- **Memoria:** 🧠 Integrada
- **Campos encontrados:** metadata.memoria_error

### ❌ ejecutar
- **URL:** /api/ejecutar
- **Status:** 400
- **Tiempo:** 2.05s
- **Memoria:** 🚫 No detectada
- **Error:** HTTP 400

### ✅ hybrid
- **URL:** /api/hybrid
- **Status:** 200
- **Tiempo:** 2.06s
- **Memoria:** 🧠 Integrada
- **Campos encontrados:** resultado.metadata.contexto, metadata.session_info, metadata.session_info.session_id, metadata.memoria_disponible

### ✅ escribir-archivo
- **URL:** /api/escribir-archivo
- **Status:** 200
- **Tiempo:** 2.08s
- **Memoria:** 🧠 Integrada
- **Campos encontrados:** metadata.session_info, metadata.session_info.session_id, metadata.memoria_disponible

### ✅ leer-archivo
- **URL:** /api/leer-archivo
- **Status:** 200
- **Tiempo:** 2.07s
- **Memoria:** 🧠 Integrada
- **Campos encontrados:** metadata.memoria_error

### ✅ modificar-archivo
- **URL:** /api/modificar-archivo
- **Status:** 200
- **Tiempo:** 2.24s
- **Memoria:** 🧠 Integrada
- **Campos encontrados:** metadata.session_info, metadata.session_info.session_id, metadata.memoria_disponible

## 🔧 Recomendaciones

- ⚠️  **1 endpoints** necesitan integración de memoria
- 🚨 **1 endpoints** no están respondiendo correctamente
