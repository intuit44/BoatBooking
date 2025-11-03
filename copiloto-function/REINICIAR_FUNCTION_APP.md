# 🔄 ACCIÓN REQUERIDA: Reiniciar Function App

## ⚠️ Problema Actual

El error persiste porque **la Function App en ejecución NO ha recargado** las nuevas variables de entorno:

```
Error: Storage quota has been exceeded for this service
```

**Causa**: El proceso `func start` cargó las variables al iniciar y sigue usando:
- ❌ Endpoint antiguo: `boatrentalfoundrysearch` (Free - lleno)
- ✅ Debería usar: `boatrentalfoundrysearch-s1` (Standard - vacío)

## ✅ Solución Inmediata

### Paso 1: Detener Function App
En la terminal donde corre `func start`:
```bash
# Presionar Ctrl+C
```

### Paso 2: Verificar Configuración
```bash
cd c:\ProyectosSimbolicos\boat-rental-app\copiloto-function
grep "AZURE_SEARCH_ENDPOINT" local.settings.json
```

**Debe mostrar**:
```json
"AZURE_SEARCH_ENDPOINT": "https://boatrentalfoundrysearch-s1.search.windows.net"
```

### Paso 3: Reiniciar Function App
```bash
func start --port 7071
```

### Paso 4: Verificar en Logs
Buscar en los logs de inicio:
```
[INFO] AZURE_SEARCH_ENDPOINT: https://boatrentalfoundrysearch-s1.search.windows.net
```

## 🧪 Verificación Post-Reinicio

### Test 1: Guardar en Memoria
```bash
curl -X POST http://localhost:7071/api/guardar-memoria \
  -H "Content-Type: application/json" \
  -H "Session-ID: test-session" \
  -d '{"texto": "Test post-reinicio", "session_id": "test-session"}'
```

**Resultado esperado**: ✅ Sin errores de quota

### Test 2: Buscar en Memoria
```bash
curl -X POST http://localhost:7071/api/buscar-memoria \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "top": 5}'
```

**Resultado esperado**: ✅ Documentos indexados correctamente

## 📊 Checklist de Verificación

- [ ] Function App detenida (Ctrl+C)
- [ ] `local.settings.json` tiene endpoint correcto
- [ ] Function App reiniciada
- [ ] Logs muestran nuevo endpoint
- [ ] Test de guardar memoria exitoso
- [ ] Test de buscar memoria exitoso
- [ ] Sin errores de quota en logs

## 🔍 Troubleshooting

### Si persiste el error después de reiniciar

1. **Verificar variables de entorno en runtime**:
```python
# Agregar temporalmente en algún endpoint
import os
logging.info(f"SEARCH ENDPOINT: {os.getenv('AZURE_SEARCH_ENDPOINT')}")
```

2. **Limpiar caché de Python**:
```bash
# Detener func
# Eliminar __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} +
# Reiniciar
func start --port 7071
```

3. **Verificar que no hay override en código**:
```bash
grep -r "boatrentalfoundrysearch.search.windows.net" --include="*.py"
```

**Resultado esperado**: Sin coincidencias (no debe estar hardcodeado)

## 📝 Nota Importante

Las variables de entorno se cargan **una sola vez** al iniciar el proceso. Cualquier cambio en `local.settings.json` requiere **reiniciar** la Function App.

---

**Acción requerida**: Reiniciar Function App AHORA
**Tiempo estimado**: 30 segundos
**Impacto**: Resuelve el error de quota inmediatamente
