
def safe_cosmos_get(item, field_name, fallback=''):
    """
    Guard universal para campos de Cosmos DB
    Previene KeyError en campos faltantes
    """
    try:
        value = item.get(field_name, fallback)
        return value if value is not None else fallback
    except Exception:
        return fallback

def safe_texto_semantico(item):
    """Guard específico para texto_semantico"""
    return (
        safe_cosmos_get(item, 'texto_semantico') or
        safe_cosmos_get(item, 'content') or
        safe_cosmos_get(item, 'message') or
        safe_cosmos_get(item, 'id', 'Sin contenido')
    )
