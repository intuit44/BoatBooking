"""
Limpiador de comandos para evitar problemas con comillas y escapes
"""
import re
import logging
import os
from pathlib import Path


def limpiar_comillas_comando(comando: str) -> str:
    """
    Limpia comillas duplicadas y mal escapadas en comandos.
    Especialmente útil para findstr, grep y comandos similares.
    """
    try:
        # Caso especial: findstr con /C:"pattern"
        if 'findstr' in comando.lower() and '/C:' in comando:
            return _limpiar_findstr(comando)
        
        # Caso especial: grep con patrones
        if 'grep' in comando.lower():
            return _limpiar_grep(comando)
        
        # Limpieza general: eliminar comillas duplicadas
        comando = re.sub(r'"{2,}', '"', comando)
        
        return comando
    except Exception as e:
        logging.warning(f"Error limpiando comando: {e}")
        return comando


def _limpiar_findstr(comando: str) -> str:
    """
    Limpia comandos findstr eliminando comillas internas y resolviendo rutas.
    Ejemplo: findstr /C:"def "auditar_deploy_http" copilot-function\function_app.py"
    Resultado: findstr /C:"def auditar_deploy_http" "C:\...\copiloto-function\function_app.py"
    """
    try:
        if '/C:' not in comando:
            return comando
        
        # Dividir en: antes de /C:, después de /C:
        parts = comando.split('/C:', 1)
        if len(parts) != 2:
            return comando
        
        prefix = parts[0]
        resto = parts[1]
        
        if not resto.startswith('"'):
            return comando
        
        # Quitar primera comilla
        resto = resto[1:]
        
        # Buscar último espacio (separa patrón de archivo)
        ultimo_espacio = resto.rfind(' ')
        if ultimo_espacio == -1:
            return comando
        
        pattern_sucio = resto[:ultimo_espacio]
        archivo_sucio = resto[ultimo_espacio+1:]
        
        # Limpiar todas las comillas
        pattern_limpio = pattern_sucio.replace('"', '')
        archivo_sucio_limpio = archivo_sucio.replace('"', '')
        
        # 🔥 RESOLVER RUTA REAL DEL ARCHIVO
        archivo_resuelto = _resolver_ruta_archivo(archivo_sucio_limpio)
        
        return f'{prefix}/C:"{pattern_limpio}" "{archivo_resuelto}"'
        
    except Exception as e:
        logging.warning(f"Error limpiando findstr: {e}")
        return comando


def _resolver_ruta_archivo(ruta_parcial: str) -> str:
    """
    Resuelve la ruta real del archivo buscando en ubicaciones comunes.
    """
    try:
        # Si ya es ruta absoluta y existe, devolverla
        if Path(ruta_parcial).is_absolute() and Path(ruta_parcial).exists():
            return ruta_parcial
        
        # Normalizar separadores
        ruta_parcial = ruta_parcial.replace('/', '\\')
        
        # Extraer nombre del archivo
        filename = Path(ruta_parcial).name
        
        # Ubicaciones comunes donde buscar
        PROJECT_ROOT = Path("C:/ProyectosSimbolicos/boat-rental-app")
        
        rutas_busqueda = [
            PROJECT_ROOT / ruta_parcial,
            PROJECT_ROOT / "copiloto-function" / filename,
            PROJECT_ROOT / "copiloto-function" / ruta_parcial,
            PROJECT_ROOT / filename,
        ]
        
        # Buscar el archivo
        for ruta in rutas_busqueda:
            if ruta.exists():
                logging.info(f"✅ Ruta resuelta: {ruta_parcial} -> {ruta}")
                return str(ruta)
        
        # Si no se encuentra, devolver la ruta original
        logging.warning(f"⚠️ No se encontró archivo: {ruta_parcial}")
        return ruta_parcial
        
    except Exception as e:
        logging.warning(f"Error resolviendo ruta: {e}")
        return ruta_parcial


def _limpiar_grep(comando: str) -> str:
    """
    Limpia comandos grep.
    """
    try:
        comando = re.sub(r'"{2,}', '"', comando)
        return comando
    except Exception:
        return comando
