# 📁 Guía de Operaciones con Archivos

## 🎯 Endpoint Universal: `/api/ejecutar-cli`

**IMPORTANTE**: Para TODAS las operaciones con archivos, usa **SIEMPRE** `/api/ejecutar-cli` con comandos PowerShell.

## 📖 Leer Archivos Completos

### ✅ Comando Recomendado: `type`

```json
{
  "comando": "type \"C:\\ruta\\al\\archivo.py\""
}
```

**Ventajas**:

- Lee todo el contenido sin problemas de codificación
- Maneja rutas con espacios correctamente
- Salida limpia y directa

## 📄 Leer Líneas Específicas

### Primeras N líneas

```json
{
  "comando": "Get-Content \"C:\\ruta\\al\\archivo.py\" | Select-Object -First 20"
}
```

### Últimas N líneas

```json
{
  "comando": "Get-Content \"C:\\ruta\\al\\archivo.py\" | Select-Object -Last 10"
}
```

## 🔍 Buscar Texto en Archivos

### Buscar patrón (estilo grep)

```json
{
  "comando": "Select-String -Path \"C:\\ruta\\al\\archivo.py\" -Pattern \"def \""
}
```

### Buscar con contexto

```json
{
  "comando": "Select-String -Path \"C:\\ruta\\al\\archivo.py\" -Pattern \"def \" -Context 2,5"
}
```

## 📂 Listar Archivos

### Listar directorio

```json
{
  "comando": "Get-ChildItem \"C:\\ruta\\directorio\""
}
```

### Buscar archivos por patrón

```json
{
  "comando": "Get-ChildItem \"C:\\ruta\" -Filter \"*.py\" -Recurse"
}
```

## ⚠️ NO USAR

- ❌ `/api/leer-archivo` - Endpoint deprecado
- ❌ `cat` - No disponible en Windows
- ❌ `grep` - Usar `Select-String` en su lugar

## 💡 Ejemplos Completos

### Leer archivo de configuración

```json
{
  "comando": "type \"C:\\ProyectosSimbolicos\\boat-rental-app\\copiloto-function\\function_app.py\""
}
```

### Buscar funciones en archivo

```json
{
  "comando": "Select-String -Path \"C:\\ProyectosSimbolicos\\boat-rental-app\\copiloto-function\\function_app.py\" -Pattern \"^def \" -Context 0,10"
}
```

### Listar archivos Python en proyecto

```json
{
  "comando": "Get-ChildItem \"C:\\ProyectosSimbolicos\\boat-rental-app\\copiloto-function\" -Filter \"*.py\" -Recurse | Select-Object FullName"
}
```

## 🎯 Reglas de Oro

1. **SIEMPRE** usa `/api/ejecutar-cli` para operaciones con archivos
2. **SIEMPRE** usa comillas dobles para rutas con espacios
3. **SIEMPRE** usa comandos PowerShell nativos (`type`, `Get-Content`, `Select-String`)
4. **NUNCA** uses comandos Unix (`cat`, `grep`, `ls`) en Windows
