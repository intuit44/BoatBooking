# ✅ Fix Aplicado: Ejecución de Comandos PowerShell

## 🐛 Problema Identificado

El endpoint `/api/ejecutar-cli` estaba ejecutando comandos PowerShell con `cmd.exe` en lugar de `powershell.exe` cuando el comando contenía pipes (`|`) u otros operadores.

### Síntoma
```json
{
  "comando": "Get-ChildItem -Path \"C:\\ProyectosSimbolicos\" -Include \"*_test.py\" -Recurse",
  "error": "\"Get-ChildItem\" no se reconoce como un comando interno o externo"
}
```

### Causa Raíz
En la función `ejecutar_comando_sistema()` (línea ~8650), la lógica de decisión de método de ejecución priorizaba `shell=True` cuando detectaba pipes, lo que causaba que PowerShell se ejecutara con `cmd.exe`:

```python
# ANTES (INCORRECTO)
if has_spaces_in_paths or has_quotes or has_pipes or shell:
    # Usar shell para comandos complejos
    execution_method = "shell"
    result = subprocess.run(
        comando_limpio,
        shell=True,  # ❌ Esto ejecuta con cmd.exe
        ...
    )
```

## ✅ Solución Aplicada

Se agregó una verificación prioritaria para comandos PowerShell que **siempre** usa `powershell.exe` independientemente de la complejidad del comando:

```python
# DESPUÉS (CORRECTO)
if tipo == "powershell":
    # PowerShell SIEMPRE debe ejecutarse con powershell.exe
    execution_method = "powershell_native"
    logging.info(f"Ejecutando PowerShell con powershell.exe: {cmd_args}")
    
    result = subprocess.run(
        cmd_args,  # Ya contiene ["powershell", "-NoProfile", "-Command", comando]
        capture_output=True,
        text=True,
        timeout=60,
        encoding='utf-8',
        errors='replace',
        env=env,
        shell=False  # ✅ NUNCA usar shell=True para PowerShell
    )
elif has_spaces_in_paths or has_quotes or has_pipes or shell:
    # Usar shell para comandos complejos (NO PowerShell)
    execution_method = "shell"
    ...
```

## 🔧 Cambios Realizados

### Archivo: `function_app.py`
- **Línea**: ~8650
- **Función**: `ejecutar_comando_sistema()`
- **Cambio**: Agregada verificación prioritaria `if tipo == "powershell"` antes de la lógica de shell

### Comportamiento Nuevo

1. **Detección de PowerShell**: El comando se detecta como PowerShell por:
   - Cmdlets nativos: `Get-*`, `Set-*`, `New-*`, `Remove-*`, `Invoke-*`
   - Detección automática en `command_type_detector.py`

2. **Construcción de Argumentos**: 
   ```python
   cmd_args = ["powershell", "-NoProfile", "-Command", "& { comando }"]
   ```

3. **Ejecución Directa**:
   - `shell=False` para evitar `cmd.exe`
   - Argumentos como lista para control preciso
   - Wrapping con `& { }` para ejecución correcta

## 🧪 Validación

### Comando de Prueba
```powershell
Get-ChildItem -Path "C:\ProyectosSimbolicos" -Include "*_test.py", "test_*.py" -Recurse
```

### Resultado Esperado
```json
{
  "exito": true,
  "comando_ejecutado": "Get-ChildItem -Path \"C:\\ProyectosSimbolicos\" -Include \"*_test.py\", \"test_*.py\" -Recurse",
  "tipo_comando": "powershell",
  "metodo_ejecucion": "powershell_native",
  "output": [
    {
      "Name": "test_adodbapi_dbapi20.py",
      "Directory": "C:\\ProyectosSimbolicos\\boat-rental-app\\.venv\\Lib\\site-packages\\adodbapi\\test"
    }
  ]
}
```

## 📋 Checklist de Verificación

- [x] Fix aplicado en `function_app.py`
- [x] Backup creado: `function_app.py.backup_powershell`
- [x] Lógica de detección PowerShell preservada
- [x] Wrapping con `& { }` mantenido
- [x] `shell=False` forzado para PowerShell
- [x] Otros tipos de comando no afectados

## 🚀 Próximos Pasos

1. **Reiniciar el servidor** de Azure Functions para aplicar cambios
2. **Probar el comando** desde Azure AI Foundry
3. **Verificar logs** para confirmar `execution_method = "powershell_native"`

## 📝 Notas Adicionales

- El fix NO afecta comandos Azure CLI, Python, Bash, NPM o Docker
- La detección automática de tipo sigue funcionando correctamente
- Los auto-fixes de `command_fixers.auto_fixers` se aplican antes de la ejecución
- El wrapping `& { comando }` se mantiene para compatibilidad con pipes y objetos PowerShell

---

**Fecha de Aplicación**: 2025-01-14  
**Archivo Modificado**: `function_app.py` (línea ~8650)  
**Backup Disponible**: `function_app.py.backup_powershell`
