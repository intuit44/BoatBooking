import re
import logging


def apply_auto_fixes(comando: str, tipo: str) -> str:
    """Aplica correcciones automáticas a comandos según patrones conocidos"""

    # --- PowerShell $lines rebanadas ---
    if tipo == "powershell":
        m = re.search(
            r"\$lines\s*=\s*Get-Content\s+['\"]([^'\"]+)['\"].*?;\s*\$lines\[(\d+)\.\.(\d+)\]",
            comando, re.IGNORECASE
        )
        if m:
            ruta, start, end = m.group(1), m.group(2), m.group(3)
            comando = f"(Get-Content '{ruta}' -Encoding UTF8)[{start}..{end}]"
            logging.info(
                f"[AUTO_FIX_POWERSHELL] Reescrito: $lines pattern -> evaluable")
            return comando

    # --- PowerShell Select-String con -Context (MatchInfo -> texto) ---
    if tipo == "powershell" and "Select-String" in comando and "-Context" in comando:
        needs_fix = "Format-Table" not in comando or not re.search(r'Out-String\s+-Width', comando, re.IGNORECASE)
        
        if needs_fix:
            m = re.search(r'^(.*)(["\'])\s*$', comando)
            if m:
                base = m.group(1)
                quote = m.group(2)
                # Remover Format-Table y Out-String existentes
                base = re.sub(r'\|\s*Format-Table[^|]*', '', base, flags=re.IGNORECASE)
                base = re.sub(r'\|\s*Out-String[^|"\']]*', '', base, flags=re.IGNORECASE).rstrip()
                comando = f"{base} | Format-Table -AutoSize -Wrap | Out-String -Width 4096{quote}"
            else:
                comando = re.sub(r'\|\s*Format-Table[^|]*', '', comando, flags=re.IGNORECASE)
                comando = re.sub(r'\|\s*Out-String[^|]*$', '', comando, flags=re.IGNORECASE).rstrip()
                comando = f"{comando} | Format-Table -AutoSize -Wrap | Out-String -Width 4096"
            
            logging.info("[AUTO_FIX_POWERSHELL] Select-String -Context: Out-String -Width aplicado")
        return comando

    # --- grep con contexto faltante ---
    if tipo == "bash" and "grep" in comando and "-A" not in comando and "-B" not in comando:
        if re.search(r"grep\s+['\"]?\w+['\"]?\s+\S+\.py", comando):
            comando = re.sub(r"grep\s+", "grep -A 10 -B 3 ", comando, count=1)
            logging.info(f"[AUTO_FIX_GREP] Añadido contexto -A/-B")

    # --- findstr rutas con espacios ---
    if tipo == "powershell" and "findstr" in comando:
        if re.search(r"findstr.*[A-Za-z]:\\", comando) and '"' not in comando:
            comando = re.sub(r"(findstr\s+/\w+\s+)(\S+)", r'\1"\2"', comando)
            logging.info(f"[AUTO_FIX_FINDSTR] Comillas añadidas a ruta")

    # --- awk sin print ---
    if tipo == "bash" and "awk" in comando and "print" not in comando:
        comando = re.sub(r"awk\s+'([^']+)'", r"awk '{\1; print $0}'", comando)
        logging.info(f"[AUTO_FIX_AWK] Añadido print $0")

    return comando
