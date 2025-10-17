# 🧪 Testing del Endpoint `/api/escribir-archivo`

## 📋 Resumen

Este directorio contiene scripts de validación completos para probar las **3 fases implementadas** del endpoint `/api/escribir-archivo` antes del despliegue en Azure.

### ✅ Fases Implementadas

1. **🔍 FASE 1: Validación Previa Completa**
   - Validación de encoding UTF-8
   - Validación sintáctica Python con `ast.parse()`
   - Detección de imports recursivos

2. **🔧 FASE 2: Inyección Delimitada con Detección de Duplicados**
   - Bloques delimitados con `# ===BEGIN/END AUTO-INJECT===`
   - Detección y reemplazo de bloques existentes
   - Prevención de duplicados mediante regex

3. **💾 FASE 3: Respaldo Automático con Restauración**
   - Versionado incremental con timestamp
   - Restauración automática si falla validación post-escritura
   - Validación post-escritura para archivos Python

## 🚀 Inicio Rápido

### 1. Configurar Entorno

```bash
# Instalar dependencias y configurar entorno
python setup_testing.py
```

### 2. Iniciar Azure Functions (Local)

```bash
# En el directorio copiloto-function
func start
```

### 3. Ejecutar Prueba Rápida

```bash
# Verificar que el endpoint responde
python quick_test.py
```

### 4. Ejecutar Validación Completa

```bash
# Ejecutar todas las pruebas de validación
python run_all_tests.py
```

## 📁 Archivos de Testing

| Archivo | Propósito |
|---------|-----------|
| `setup_testing.py` | Configuración inicial del entorno |
| `quick_test.py` | Prueba rápida de conectividad |
| `test_deployment_validation.py` | Validación completa de las 3 fases |
| `azure_compatibility_test.py` | Pruebas específicas de Azure |
| `run_all_tests.py` | Script maestro que ejecuta todo |

## 🔍 Pruebas Incluidas

### Validación de Deployment (`test_deployment_validation.py`)

- ✅ **Fase 1**: UTF-8, sintaxis Python, imports recursivos
- ✅ **Fase 2**: Inyección delimitada de ErrorHandler
- ✅ **Fase 3**: Respaldo automático con timestamp
- ✅ **Bing Fallback**: Integración con sistema de recuperación
- ✅ **Azure Deployment**: Conectividad con producción

### Compatibilidad Azure (`azure_compatibility_test.py`)

- ☁️ **Escenarios específicos**: Caracteres especiales, archivos grandes
- ⚡ **Rendimiento**: Medición de tiempos de respuesta
- 🚨 **Manejo de errores**: Validación de error handling
- 🧠 **3 Fases en Azure**: Verificación en producción

## 📊 Reportes Generados

Los scripts generan reportes JSON detallados:

- `deployment_validation_report.json` - Resultados de validación completa
- `azure_compatibility_report.json` - Resultados de compatibilidad Azure

## 🎯 Criterios de Éxito

### ✅ Para Aprobar Deployment

1. **Todas las pruebas críticas deben pasar** (Fases 1, 2, 3)
2. **Tasa de éxito ≥ 80%** en pruebas generales
3. **Azure connectivity** debe funcionar
4. **Error handling** debe ser robusto

### ⚠️ Advertencias Aceptables

- Timeouts ocasionales en Azure (cold start)
- Pruebas no críticas que fallen
- Bing Fallback no disponible temporalmente

## 🔧 Troubleshooting

### Problema: "requests module not found"
```bash
pip install requests
```

### Problema: "func command not found"
Instalar Azure Functions Core Tools:
- Windows: `npm install -g azure-functions-core-tools@4 --unsafe-perm true`
- macOS: `brew tap azure/functions && brew install azure-functions-core-tools@4`

### Problema: "Connection refused localhost:7071"
```bash
# Verificar que Azure Functions esté corriendo
func start --verbose
```

### Problema: "Azure timeout"
- Es normal en cold start
- Reintentar después de 30 segundos
- Verificar URL de Azure en `azure_compatibility_test.py`

## 📈 Interpretación de Resultados

### 🎉 Éxito Total
```
✅ TODAS LAS PRUEBAS PASARON
✅ LISTO PARA DESPLIEGUE EN AZURE
```

### ⚠️ Éxito Parcial
```
⚠️ ALGUNAS PRUEBAS NO CRÍTICAS FALLARON
✅ PUEDE PROCEDER CON DESPLIEGUE (con precaución)
```

### ❌ Fallo Crítico
```
❌ FALLAS CRÍTICAS DETECTADAS
🚫 NO DESPLEGAR HASTA RESOLVER PROBLEMAS
```

## 🚀 Flujo de Deployment

1. **Pre-deployment**: `python run_all_tests.py`
2. **Deploy**: Subir a Azure si todas las pruebas críticas pasan
3. **Post-deployment**: `python azure_compatibility_test.py`
4. **Monitoring**: Revisar logs en Azure Portal

## 🔍 Validación Manual Adicional

### Probar Endpoint Manualmente

```bash
# Crear archivo simple
curl -X POST http://localhost:7071/api/escribir-archivo \
  -H "Content-Type: application/json" \
  -d '{"ruta": "manual_test.py", "contenido": "print(\"test\")"}'

# Probar inyección ErrorHandler
curl -X POST http://localhost:7071/api/escribir-archivo \
  -H "Content-Type: application/json" \
  -d '{"ruta": "error_handler_test.py", "contenido": "from error_handler import ErrorHandler\nprint(\"test\")"}'
```

### Verificar en Azure

```bash
# Cambiar URL en los scripts o probar directamente
curl -X POST https://copiloto-semantico-func-us2.azurewebsites.net/api/escribir-archivo \
  -H "Content-Type: application/json" \
  -d '{"ruta": "azure_manual_test.py", "contenido": "print(\"Azure test\")"}'
```

## 📞 Soporte

Si encuentras problemas:

1. **Revisar logs**: `func start --verbose`
2. **Verificar reportes JSON** generados
3. **Ejecutar setup_testing.py** nuevamente
4. **Verificar que function_app.py** tenga las 3 fases implementadas

## 🎯 Próximos Pasos

Después de que todas las pruebas pasen:

1. ✅ Hacer commit de los cambios
2. ✅ Desplegar a Azure con confianza
3. ✅ Ejecutar `azure_compatibility_test.py` post-despliegue
4. ✅ Monitorear logs en Azure Portal
5. ✅ Documentar cualquier issue encontrado

---

**Última actualización**: Enero 2025  
**Versión**: 1.0 - Validación completa de 3 fases implementadas