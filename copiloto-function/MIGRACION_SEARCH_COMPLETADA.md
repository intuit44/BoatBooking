# ✅ MIGRACIÓN A NUEVO SERVICIO DE BÚSQUEDA COMPLETADA

## 🎯 Problema Original

```
Storage quota has been exceeded for this service. 
You must either delete documents first, or use a higher SKU for additional quota.
```

**Servicio antiguo**: `boatrentalfoundrysearch` (Free tier - 50MB límite)

## ✅ Solución Implementada

### 1. Nuevo Servicio Creado
**Nombre**: `boatrentalfoundrysearch-s1`
**SKU**: Standard
**Capacidad**: 25GB (500x más que Free)
**Endpoint**: `https://boatrentalfoundrysearch-s1.search.windows.net`

### 2. Configuración Actualizada
**Archivo**: `local.settings.json`

```json
{
  "AZURE_SEARCH_ENDPOINT": "https://boatrentalfoundrysearch-s1.search.windows.net",
  "AZURE_SEARCH_KEY": "drXPuF3I7BO4klDHAglz5hNYqR3kYSg5AoY2PXGhgaAzSeBCn2JP"
}
```

### 3. Índice Creado
**Nombre**: `agent-memory-index`
**Campos**:
- `id` (String, key)
- `session_id` (String, filterable)
- `agent_id` (String, filterable)
- `endpoint` (String, filterable)
- `texto_semantico` (String, searchable)
- `exito` (Boolean, filterable)
- `tipo` (String, filterable)
- `timestamp` (DateTimeOffset, sortable)

## 🚀 Próximos Pasos

### 1. Reiniciar Function App
```bash
# Detener (Ctrl+C)
# Iniciar nuevamente
func host start --port 7071
```

### 2. Verificar Funcionamiento
```bash
# Test de indexación
curl -X POST http://localhost:7071/api/guardar-memoria \
  -H "Content-Type: application/json" \
  -d '{"texto": "Test de nuevo servicio", "session_id": "test"}'

# Test de búsqueda
curl -X POST http://localhost:7071/api/buscar-memoria \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "top": 5}'
```

### 3. Migrar Datos (Opcional)
Si necesitas los datos del servicio antiguo:

```python
# Script de migración (crear si es necesario)
python migrar_datos_search.py
```

## 📊 Comparación de Servicios

| Característica | Free (Antiguo) | Standard (Nuevo) |
|----------------|----------------|------------------|
| Almacenamiento | 50 MB | 25 GB |
| Documentos | 10,000 | 15 millones |
| Índices | 3 | 50 |
| Particiones | 1 | 12 |
| Réplicas | 1 | 12 |
| Costo | $0/mes | ~$250/mes |

## ✅ Estado Final

- ✅ Servicio Standard creado
- ✅ Configuración actualizada
- ✅ Índice creado
- 🟡 Function App pendiente de reinicio
- 🟡 Datos pendientes de migración (si es necesario)

## 🔧 Troubleshooting

### Si persiste el error
1. Verificar que `local.settings.json` tiene el endpoint correcto
2. Reiniciar completamente la Function App
3. Limpiar la cola: `az storage message clear --queue-name memory-indexing-queue`

### Si necesitas volver al servicio antiguo
```json
{
  "AZURE_SEARCH_ENDPOINT": "https://boatrentalfoundrysearch.search.windows.net",
  "AZURE_SEARCH_KEY": "kyfYT1Proxvt9fT4ZBmWPcppUkvjK0rxBuEB7prkxYAzSeCmpM7L"
}
```

---

**Fecha**: 2025-11-02
**Costo adicional**: ~$250/mes
**Beneficio**: 500x más capacidad de almacenamiento
**Estado**: ✅ Listo para usar
