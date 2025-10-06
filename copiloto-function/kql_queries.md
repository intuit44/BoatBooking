# 📊 KQL Queries para Monitoreo de Fixes

## 🔍 Queries de Producción

### 1. Últimos fixes pendientes por prioridad
```kql
traces
| where customDimensions.tipo == "correccion_registrada"
| where timestamp > ago(24h)
| summarize count() by tostring(customDimensions.prioridad)
| order by count_ desc
```

### 2. Tiempo de promoción por fix
```kql
traces
| where customDimensions.fix_id != ""
| where customDimensions.tipo in ("correccion_registrada", "fix_promoted_successfully")
| summarize 
    firstReg = min(timestamp),
    lastProm = max(timestamp)
  by tostring(customDimensions.fix_id)
| extend TProm = lastProm - firstReg
| where TProm > 0s
| order by TProm desc
```

### 3. Fallos en promoción (últimas 24h)
```kql
traces
| where timestamp > ago(24h)
| where customDimensions.tipo == "promocion_batch"
| extend fallidos = toint(customDimensions.fallidos_count)
| where fallidos > 0
| project timestamp, customDimensions.run_id, fallidos, customDimensions.fixes_procesados
```

### 4. Throughput de fixes por hora
```kql
traces
| where customDimensions.tipo in ("fix_promoted_successfully", "fix_promotion_failed")
| where timestamp > ago(24h)
| summarize 
    promovidos = countif(customDimensions.tipo == "fix_promoted_successfully"),
    fallidos = countif(customDimensions.tipo == "fix_promotion_failed")
  by bin(timestamp, 1h)
| order by timestamp desc
```

### 5. Top targets con más fixes
```kql
traces
| where customDimensions.tipo == "correccion_registrada"
| where timestamp > ago(7d)
| summarize count() by tostring(customDimensions.target)
| order by count_ desc
| take 10
```

## 🚨 Alertas Recomendadas

### Alerta 1: Fallos en promoción
```kql
traces
| where timestamp > ago(5m)
| where customDimensions.tipo == "promocion_batch"
| extend fallidos = toint(customDimensions.fallidos_count)
| where fallidos > 0
| summarize total_fallidos = sum(fallidos)
| where total_fallidos > 0
```
**Acción**: Webhook a `/api/autocorregir` para auto-remedio

### Alerta 2: Sin promociones por tiempo prolongado
```kql
traces
| where timestamp > ago(30m)
| where customDimensions.tipo == "promocion_batch"
| extend promovidos = toint(customDimensions.promovidos_count)
| summarize total_promovidos = sum(promovidos)
| where total_promovidos == 0
```
**Acción**: Notificación a equipo SRE

## 📈 Dashboard Widgets

### Widget 1: Fixes por Estado (Pie Chart)
```kql
traces
| where customDimensions.fix_id != ""
| where timestamp > ago(24h)
| summarize count() by tostring(customDimensions.estado)
```

### Widget 2: Latencia de Promoción (Time Chart)
```kql
traces
| where customDimensions.tipo == "promocion_batch"
| where timestamp > ago(24h)
| extend promovidos = toint(customDimensions.promovidos_count)
| project timestamp, promovidos
| render timechart
```