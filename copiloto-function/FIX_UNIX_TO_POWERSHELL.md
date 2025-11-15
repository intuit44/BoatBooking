# ✅ Fix Aplicado: Conversión Automática de Comandos Unix a PowerShell en Windows

## 🐛 Problema Identificado

El endpoint `/api/ejecutar-cli` detectaba comandos Unix como `ls` como tipo `bash` y los ejecutaba con `bash`, causando errores en Windows donde bash no está disponible o no funciona correctamente con rutas de Windows.

### Síntoma
```json
{
  "comando": "ls C:\\ProyectosSimbolicos\\*_test.py",
  "error": "ls: cannot access 'C:\\ProyectosSimbolicos\\*_test.py': No such file or directory",
  "tipo_comando": "bash"
}
```

### Causa Raíz
El detector de comandos (`command_type_detector.py`) identificaba correctamente `ls` como comando bash, pero no consideraba que en Windows estos comandos deben convertirse a sus equivalentes PowerShell.

## ✅ Solución Aplicada

Se implementó conversión automática de comandos Unix a PowerShell cuando se detecta que el sistema operativo es Windows.

### Cambios Realizados

#### 1. Detección de Sistema Operativo
```python
import platform

# En detect_command_type()
elif any(normalized_command.lower().startswith(p) for p in ["bash ", "sh ", "chmod ", "ls ", "cd ", "mkdir ", "rm "]):
    # 🔥 FIX: En Windows, convertir comandos Unix a PowerShell
    if platform.system() == "Windows":
        cmd_type = "powershell"
        confidence = 0.9
        # Convertir comando Unix a PowerShell
        normalized_command = self._convert_unix_to_powershell(normalized_command)
        logging.info(f"Comando Unix convertido a PowerShell: {normalized_command}")
    else:
        cmd_type = "bash"
        confidence = 0.8
```

#### 2. Mapeo de Comandos Unix a PowerShell
```python
self.unix_to_powershell = {
    "ls": "Get-ChildItem",
    "dir": "Get-ChildItem",
    "cat": "Get-Content",
    "grep": "Select-String",
    "find": "Get-ChildItem -Recurse",
    "rm": "Remove-Item",
    "cp": "Copy-Item",
    "mv": "Move-Item",
    "mkdir": "New-Item -ItemType Directory",
    "touch": "New-Item -ItemType File",
    "pwd": "Get-Location",
    "cd": "Set-Location",
    "echo": "Write-Output"
}
```

#### 3. Método de Conversión Inteligente
```python
def _convert_unix_to_powershell(self, command: str) -> str:
    """
    Convierte comandos Unix a sus equivalentes PowerShell en Windows
    """
    # Casos especiales para ls con wildcards
    if base_cmd == "ls":
        if len(parts) > 1:
            path = " ".join(parts[1:])
            # Si tiene wildcards, usar -Include
            if "*" in path:
                # Extraer directorio base y patrón
                if "\\" in path or "/" in path:
                    base_path = path.rsplit("\\", 1)[0]
                    pattern = path.rsplit("\\", 1)[1]
                    return f'{ps_cmd} -Path "{base_path}" -Include "{pattern}" -Recurse'
                else:
                    return f'{ps_cmd} -Include "{path}"'
            else:
                return f'{ps_cmd} -Path "{path}"'
```

## 🔧 Ejemplos de Conversión

### Ejemplo 1: ls simple
```bash
# Entrada
ls C:\ProyectosSimbolicos

# Salida
Get-ChildItem -Path "C:\ProyectosSimbolicos"
```

### Ejemplo 2: ls con wildcard
```bash
# Entrada
ls C:\ProyectosSimbolicos\*_test.py

# Salida
Get-ChildItem -Path "C:\ProyectosSimbolicos" -Include "*_test.py" -Recurse
```

### Ejemplo 3: Otros comandos Unix
```bash
# cat file.txt -> Get-Content file.txt
# rm file.txt -> Remove-Item file.txt
# mkdir newdir -> New-Item -ItemType Directory newdir
# pwd -> Get-Location
```

## 🧪 Validación

### Comando de Prueba
```bash
ls C:\ProyectosSimbolicos\*_test.py
```

### Resultado Esperado
```json
{
  "exito": true,
  "comando_ejecutado": "Get-ChildItem -Path \"C:\\ProyectosSimbolicos\" -Include \"*_test.py\" -Recurse",
  "tipo_comando": "powershell",
  "metodo_ejecucion": "powershell_native",
  "output": [
    {
      "Name": "test_adodbapi_dbapi20.py",
      "FullName": "C:\\ProyectosSimbolicos\\boat-rental-app\\.venv\\Lib\\site-packages\\adodbapi\\test\\test_adodbapi_dbapi20.py"
    }
  ]
}
```

## 📋 Comandos Soportados

| Comando Unix | Equivalente PowerShell | Notas |
|-------------|------------------------|-------|
| `ls` | `Get-ChildItem` | Soporta wildcards con `-Include` |
| `cat` | `Get-Content` | Lee contenido de archivos |
| `grep` | `Select-String` | Búsqueda de patrones |
| `find` | `Get-ChildItem -Recurse` | Búsqueda recursiva |
| `rm` | `Remove-Item` | Eliminar archivos/directorios |
| `cp` | `Copy-Item` | Copiar archivos |
| `mv` | `Move-Item` | Mover/renombrar archivos |
| `mkdir` | `New-Item -ItemType Directory` | Crear directorios |
| `pwd` | `Get-Location` | Directorio actual |
| `cd` | `Set-Location` | Cambiar directorio |

## 🔄 Flujo de Ejecución

1. **Detección**: `ls C:\path\*_test.py` → detectado como comando Unix
2. **Verificación OS**: `platform.system()` → "Windows"
3. **Conversión**: `ls` → `Get-ChildItem -Path "C:\path" -Include "*_test.py" -Recurse`
4. **Tipo**: Cambiado de `bash` a `powershell`
5. **Ejecución**: Usa el fix de PowerShell (línea 8650) con `powershell.exe`

## 📝 Notas Adicionales

- La conversión solo ocurre en Windows (`platform.system() == "Windows"`)
- En Linux/macOS, los comandos Unix se ejecutan normalmente con bash
- La conversión es inteligente y maneja casos especiales como wildcards
- Los comandos convertidos se registran en los logs para debugging

## 🚀 Próximos Pasos

1. **Reiniciar el servidor** de Azure Functions
2. **Probar comandos Unix** desde Azure AI Foundry
3. **Verificar logs** para confirmar la conversión automática

---

**Fecha de Aplicación**: 2025-01-14  
**Archivo Modificado**: `command_type_detector.py`  
**Líneas Modificadas**: ~70-85, ~100-145
