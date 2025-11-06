"""
Limpiador de comandos para evitar problemas con comillas y escapes
"""
import re
import logging

def limpiar_comillas_comando(comando: str) -> str:
    """
    Limpia comillas duplicadas SOLO si están mal formadas.
    NO tocar comandos bien formados.
    """
    try:
        # Si comillas están balanceadas, probablemente está bien
        if comando.count('"') % 2 == 0:
            # Solo limpiar si hay comillas duplicadas obvias
            if '""' in comando:
                comando = re.sub(r'"{2,}', '"', comando)
            return comando
        
        # Si están desbalanceadas, intentar limpiar
        comando = re.sub(r'"{2,}', '"', comando)
        return comando
        
    except Exception as e:
        logging.warning(f"Error limpiando comando: {e}")
        return comando
