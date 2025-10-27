
# 📊 REPORTE DE VALIDACIÓN DE MEMORIA
**Fecha:** 2025-10-25 20:32:34
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
- **Tiempo:** 3.66s
- **Memoria:** 🧠 Integrada
- **Campos encontrados:** metadata.memoria_aplicada, contexto_conversacion, contexto_conversacion.session_id, interacciones_previas

### ✅ status
- **URL:** /api/status
- **Status:** 200
- **Tiempo:** 3.43s
- **Memoria:** 🧠 Integrada
- **Campos encontrados:** metadata.memoria_aplicada, contexto_conversacion, contexto_conversacion.session_id, interacciones_previas

### ❌ ejecutar
- **URL:** /api/ejecutar
- **Status:** 400
- **Tiempo:** 2.94s
- **Memoria:** 🚫 No detectada
- **Error:** HTTP 400

### ✅ hybrid
- **URL:** /api/hybrid
- **Status:** 200
- **Tiempo:** 3.03s
- **Memoria:** 🧠 Integrada
- **Campos encontrados:** resultado.metadata.contexto, metadata.session_info, metadata.session_info.session_id, metadata.memoria_disponible, metadata.memoria_sesion, metadata.memoria_sesion.continuidad_sesion, metadata.memoria_aplicada, contexto_conversacion, contexto_conversacion.session_id, interacciones_previas

### ✅ escribir-archivo
- **URL:** /api/escribir-archivo
- **Status:** 200
- **Tiempo:** 4.39s
- **Memoria:** 🧠 Integrada
- **Campos encontrados:** contexto_conversacion, contexto_conversacion.session_id, metadata.memoria_aplicada, metadata.memoria_global, metadata.session_info, metadata.session_info.session_id, metadata.memoria_disponible, interacciones_previas

### ✅ leer-archivo
- **URL:** /api/leer-archivo
- **Status:** 200
- **Tiempo:** 3.22s
- **Memoria:** 🧠 Integrada
- **Campos encontrados:** metadata.memoria_aplicada, contexto_conversacion, contexto_conversacion.session_id, interacciones_previas

### ✅ modificar-archivo
- **URL:** /api/modificar-archivo
- **Status:** 200
- **Tiempo:** 4.41s
- **Memoria:** 🧠 Integrada
- **Campos encontrados:** contexto_conversacion, contexto_conversacion.session_id, metadata.memoria_aplicada, metadata.memoria_global, metadata.session_info, metadata.session_info.session_id, metadata.memoria_disponible, interacciones_previas

## 🔧 Recomendaciones

- ⚠️  **1 endpoints** necesitan integración de memoria
- 🚨 **1 endpoints** no están respondiendo correctamente
