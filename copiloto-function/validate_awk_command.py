"""
Validador de comandos awk para prevenir errores de sintaxis
"""
import re
import logging

def validate_awk_command(comando: str) -> dict:
    """
    Valida sintaxis de comandos awk antes de ejecutar
    
    Returns:
        dict con 'valido': bool, 'error': str, 'sugerencia': str
    """
    if 'awk' not in comando.lower():
        return {"valido": True}
    
    # Extraer el patrón awk
    match = re.search(r"awk\s+'([^']+)'", comando)
    if not match:
        match = re.search(r'awk\s+"([^"]+)"', comando)
    
    if not match:
        return {
            "valido": False,
            "error": "Comando awk sin patrón válido",
            "sugerencia": "Usa comillas simples: awk '/patron/' archivo"
        }
    
    patron = match.group(1)
    
    # Validar comillas balanceadas
    if patron.count('"') % 2 != 0:
        return {
            "valido": False,
            "error": "Comillas dobles desbalanceadas en patrón awk",
            "sugerencia": "Revisa las comillas dentro del patrón"
        }
    
    # Validar slashes de regex balanceados
    slashes = re.findall(r'(?<!\\)/', patron)
    if len(slashes) % 2 != 0:
        return {
            "valido": False,
            "error": "Slashes de regex desbalanceados",
            "sugerencia": "Cada regex debe tener / al inicio y final: /patron/"
        }
    
    # Validar llaves balanceadas
    if patron.count('{') != patron.count('}'):
        return {
            "valido": False,
            "error": "Llaves desbalanceadas en patrón awk",
            "sugerencia": "Cada { debe tener su correspondiente }"
        }
    
    return {"valido": True}

def suggest_awk_fix(comando: str) -> str:
    """
    Normaliza comandos awk automáticamente convirtiendo a PowerShell
    """
    # Detectar si es comando awk para extraer función
    if 'awk' in comando.lower() and 'function_app.py' in comando:
        # Extraer nombre de función del patrón awk
        func_match = re.search(r'def\s+(\w+)', comando)
        if func_match:
            func_name = func_match.group(1)
            # Convertir a PowerShell que funciona
            return f"powershell -Command \"$lines = Get-Content 'function_app.py'; for ($i = 0; $i -lt $lines.Count; $i++) {{ if ($lines[$i] -match 'def {func_name}') {{ $start = $i; $end = $i + 1; while ($end -lt $lines.Count -and ($lines[$end] -match '^\\s+' -or $lines[$end] -match '^$')) {{ $end++ }}; $lines[$start..$end] -join '`n'; break }} }}\""
    
    # Si no se puede normalizar, devolver original
    return comando
