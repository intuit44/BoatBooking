"""
Helper functions for file operations
"""


def _generar_respuesta_no_encontrado(ruta: str, contenido: str, operacion: str, body: dict) -> dict:
    """
    Genera respuesta enriquecida cuando un archivo no se encuentra
    """
    return {
        "exito": False,
        "error": f"Archivo no encontrado: {ruta}",
        "sugerencias": [
            f"Crear archivo con: POST /api/escribir-archivo {{\"ruta\": \"{ruta}\", \"contenido\": \"...\"}}",
            f"Listar archivos disponibles: GET /api/listar-blobs?prefix={ruta.rsplit('/', 1)[0] if '/' in ruta else ''}",
            "Verificar ruta y permisos"
        ],
        "operacion_solicitada": operacion,
        "ruta_solicitada": ruta,
        "alternativas": [
            "Usar ruta absoluta",
            "Verificar que el archivo existe en Blob Storage",
            "Crear el archivo primero"
        ]
    }
