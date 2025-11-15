# 🔄 Instrucciones para Reiniciar el Servidor

## ✅ Fixes Aplicados que Requieren Reinicio

1. **Fix PowerShell con Pipes** (`function_app.py` línea ~8650)
2. **Fix Conversión Unix a PowerShell** (`command_type_detector.py`)
3. **Fix Detección Case-Insensitive** (`command_type_detector.py` línea ~93)

## 🧪 Verificación de Fixes (Test Local)

```bash
cd c:\ProyectosSimbolicos\boat-rental-app\copiloto-function
python test_detector.py
```

### Resultado Esperado del Test
```
Comando: Get-ChildItem -Path "C:\ProyectosSimbolicos" -Include "*_test.py" -Recurse
  Tipo: powershell
  Confianza: 0.8
  ✅ CORRECTO

Comando: ls C:\ProyectosSimbolicos\*_test.py
  Tipo: powershell
  Confianza: 0.9
  Normalizado: Get-ChildItem -Path "C:\ProyectosSimbolicos" -Include "*_test.py" -Recurse
  ✅ CORRECTO
```

## 🚀 Opciones de Reinicio

### Opción 1: Reinicio desde Azure Portal (Recomendado)
1. Ir a [Azure Portal](https://portal.azure.com)
2. Buscar la Function App: `copiloto-semantico-func-us2`
3. Click en **"Restart"** en la barra superior
4. Esperar ~30 segundos

### Opción 2: Reinicio desde Azure CLI
```bash
az functionapp restart --name copiloto-semantico-func-us2 --resource-group boat-rental-app-group
```

### Opción 3: Reinicio Local (Desarrollo)
Si estás ejecutando localmente:
```bash
# Detener el servidor (Ctrl+C)
# Luego reiniciar
func start
```

## 🔍 Verificación Post-Reinicio

### Test 1: Comando PowerShell Directo
```json
POST /api/ejecutar-cli
{
  "comando": "Get-ChildItem -Path \"C:\\ProyectosSimbolicos\" -Include \"*_test.py\" -Recurse"
}
```

**Resultado Esperado:**
```json
{
  "exito": true,
  "tipo_comando": "powershell",
  "metodo_ejecucion": "powershell_native",
  "output": [...]
}
```

### Test 2: Comando Unix Convertido
```json
POST /api/ejecutar-cli
{
  "comando": "ls C:\\ProyectosSimbolicos\\*_test.py"
}
```

**Resultado Esperado:**
```json
{
  "exito": true,
  "tipo_comando": "powershell",
  "comando_ejecutado": "Get-ChildItem -Path \"C:\\ProyectosSimbolicos\" -Include \"*_test.py\" -Recurse",
  "metodo_ejecucion": "powershell_native",
  "output": [...]
}
```

## ❌ Problemas Conocidos (Antes del Reinicio)

### Síntoma 1: Detección como "generic"
```json
{
  "tipo_comando": "generic",
  "metodo_ejecucion": "shell",
  "error": "Get-ChildItem no se reconoce como un comando interno o externo"
}
```
**Causa**: El servidor está usando código antiguo en caché  
**Solución**: Reiniciar el servidor

### Síntoma 2: Ejecución con cmd.exe
```json
{
  "tipo_comando": "powershell",
  "metodo_ejecucion": "shell",
  "error": "Get-ChildItem no se reconoce..."
}
```
**Causa**: El fix de `function_app.py` no está activo  
**Solución**: Reiniciar el servidor

## 📋 Checklist de Verificación

- [ ] Test local ejecutado (`python test_detector.py`)
- [ ] Servidor reiniciado
- [ ] Test 1 ejecutado desde Azure AI Foundry
- [ ] Test 2 ejecutado desde Azure AI Foundry
- [ ] Logs verificados para confirmar `execution_method = "powershell_native"`
- [ ] Documentación actualizada

## 📝 Logs a Verificar

Después del reinicio, buscar en los logs:

```
Comando detectado: powershell (confianza: 0.800)
Ejecutando PowerShell con powershell.exe: ['powershell', '-NoProfile', '-Command', '& { Get-ChildItem ... }']
```

## 🎯 Resultado Final Esperado

Después del reinicio, todos los comandos PowerShell (tanto nativos como convertidos desde Unix) deberían:

1. ✅ Detectarse correctamente como `tipo_comando: "powershell"`
2. ✅ Ejecutarse con `powershell.exe` (`metodo_ejecucion: "powershell_native"`)
3. ✅ Devolver resultados correctos sin errores de "comando no reconocido"

---

**Última Actualización**: 2025-01-14  
**Archivos Modificados**: 
- `function_app.py` (línea ~8650)
- `command_type_detector.py` (líneas ~15-30, ~93, ~100-145)
