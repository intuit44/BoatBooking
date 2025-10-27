# 🧪 Guía de Ejecución de Pruebas Pre-Despliegue

## 📋 Orden de Ejecución

### 1️⃣ **Validación de Integración** (PRIMERO)
```bash
cd copiloto-function
python validate_wrapper_integration.py
```

**✅ Esperado**: 
- Todos los componentes importados correctamente
- Funciones principales disponibles
- Estructura de respuesta válida

---

### 2️⃣ **Iniciar Azure Function** (SEGUNDO)
```bash
func start --port 7071
```

**✅ Esperado**: 
- Function App corriendo en http://localhost:7071
- Endpoints disponibles

---

### 3️⃣ **Pruebas de Producción** (TERCERO)
```bash
# En otra terminal
python test_production_readiness.py
```

**✅ Esperado**: 
- 6/6 pruebas pasando (mínimo 5/6 para producción)
- Success rate >= 80%

---

## 🎯 Criterios de Aprobación

| Prueba | Descripción | Criterio de Éxito |
|--------|-------------|-------------------|
| **Historial Endpoint** | Respuesta con campos requeridos | Status 200 + campos semánticos |
| **Clasificación Semántica** | Detecta intenciones diferentes | >= 2 intenciones únicas |
| **Validación de Contexto** | Elimina duplicados y optimiza | Reduce interacciones duplicadas |
| **Flujo de Continuidad** | Mantiene historial entre llamadas | >= 3 interacciones recordadas |
| **Optimización de Tokens** | Limita contexto a ~2000 tokens | Reduce 50 → ≤15 interacciones |
| **Memoria Cruzada** | Agentes comparten memoria | Ve interacciones de otros agentes |

---

## 🚨 Troubleshooting

### Error: "Module not found"
```bash
# Verificar que estás en el directorio correcto
cd c:\ProyectosSimbolicos\boat-rental-app\copiloto-function

# Verificar archivos
ls semantic_classifier.py context_validator.py cosmos_memory_direct.py
```

### Error: "Connection refused"
```bash
# Verificar que Azure Function está corriendo
curl http://localhost:7071/api/historial-interacciones
```

### Error: "Cosmos DB connection"
```bash
# Verificar variables de entorno
echo $COSMOSDB_ENDPOINT
echo $COSMOSDB_KEY
```

---

## 📊 Interpretación de Resultados

### ✅ **LISTO PARA PRODUCCIÓN** (Success Rate >= 80%)
```
📊 RESULTADOS: 6/6 pruebas pasaron
🎯 RECOMENDACIÓN: ✅ LISTO PARA DESPLIEGUE
```

**Siguiente paso**: Proceder con empaquetado y despliegue

### ❌ **REQUIERE CORRECCIONES** (Success Rate < 80%)
```
📊 RESULTADOS: 3/6 pruebas pasaron
🎯 RECOMENDACIÓN: ❌ REQUIERE CORRECCIONES
```

**Siguiente paso**: Revisar errores específicos en `production_readiness_report.json`

---

## 🔍 Logs Importantes a Verificar

Durante las pruebas, buscar en los logs:

```
🧠 Interpretación semántica: Análisis inteligente...
🎯 Contexto inteligente: {"modo_operacion": "..."}
🔍 Contexto validado y optimizado
✅ customMetric|name=historial_interacciones_hits
```

---

## 📄 Reportes Generados

- `production_readiness_report.json` - Resultados detallados de todas las pruebas
- Logs de Azure Function - Métricas y debugging info

---

## 🚀 Después de Aprobar las Pruebas

1. **Commit** cambios finales
2. **Tag** versión (ej: v283)
3. **Build** imagen Docker
4. **Deploy** a Azure
5. **Restart** App Service

```bash
git add .
git commit -m "✅ Sistema LLM robusto - Pruebas aprobadas"
git tag v283
docker build -t copiloto-function:v283 .
# ... resto del proceso de despliegue
```