#!/usr/bin/env python3
"""
Fix para errores de Cosmos DB 'texto_semantico'
Corrige validación de campos en endpoints de monitoreo
"""
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COSMOS_FIXES = {
    "verificar_estado_sistema.py": {
        "old_pattern": "item.get('texto_semantico', '')",
        "new_pattern": "item.get('texto_semantico', '') or item.get('content', '') or str(item.get('id', ''))",
        "context": "Fallback para texto_semantico faltante"
    },
    "verificar_app_insights.py": {
        "old_pattern": "document.get('texto_semantico')",
        "new_pattern": "document.get('texto_semantico') or document.get('message') or document.get('content') or 'N/A'",
        "context": "Validación robusta de texto_semantico"
    },
    "agent_output.py": {
        "old_pattern": "texto_semantico = item['texto_semantico']",
        "new_pattern": "texto_semantico = item.get('texto_semantico', '') or item.get('content', '') or 'Sin contenido'",
        "context": "Manejo seguro de texto_semantico"
    }
}


def find_and_fix_cosmos_errors():
    """Busca y corrige errores de texto_semantico en endpoints"""
    endpoints_dir = "endpoints"
    fixes_applied = 0

    logger.info("🔧 Iniciando fix de errores Cosmos DB texto_semantico...")

    for filename, fix_info in COSMOS_FIXES.items():
        file_path = os.path.join(endpoints_dir, filename)

        if not os.path.exists(file_path):
            logger.warning(f"❌ Archivo no encontrado: {file_path}")
            continue

        try:
            # Leer archivo
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Verificar si necesita fix
            if fix_info["old_pattern"] in content:
                logger.info(
                    f"🔧 Aplicando fix en {filename}: {fix_info['context']}")

                # Aplicar fix
                fixed_content = content.replace(
                    fix_info["old_pattern"],
                    fix_info["new_pattern"]
                )

                # Escribir archivo corregido
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)

                logger.info(f"✅ Fix aplicado exitosamente en {filename}")
                fixes_applied += 1
            else:
                logger.info(
                    f"ℹ️  {filename} no requiere fix (ya corregido o patrón no encontrado)")

        except Exception as e:
            logger.error(f"❌ Error procesando {filename}: {str(e)}")

    return fixes_applied


def validate_cosmos_connection():
    """Valida configuración de Cosmos DB"""
    logger.info("🔍 Validando configuración Cosmos DB...")

    required_env_vars = [
        'COSMOS_DB_ENDPOINT',
        'COSMOS_DB_KEY',
        'COSMOS_DB_DATABASE_NAME',
        'COSMOS_DB_CONTAINER_NAME'
    ]

    missing_vars = []
    for var in required_env_vars:
        if not os.environ.get(var):
            missing_vars.append(var)

    if missing_vars:
        logger.warning(
            f"⚠️  Variables de entorno faltantes: {', '.join(missing_vars)}")
        return False

    logger.info("✅ Configuración Cosmos DB completa")
    return True


def create_cosmos_error_guard():
    """Crea guard universal para errores de Cosmos"""
    guard_code = '''
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
'''

    guard_path = os.path.join("endpoints", "cosmos_error_guard.py")

    try:
        with open(guard_path, 'w', encoding='utf-8') as f:
            f.write(guard_code)
        logger.info(f"✅ Guard creado: {guard_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Error creando guard: {str(e)}")
        return False


def main():
    """Función principal"""
    logger.info("🚀 Iniciando corrección de errores Cosmos DB...")

    # Validar configuración
    if not validate_cosmos_connection():
        logger.warning(
            "⚠️  Configuración Cosmos incompleta - algunos fixes pueden fallar")

    # Aplicar fixes específicos
    fixes_count = find_and_fix_cosmos_errors()

    # Crear guard universal
    guard_created = create_cosmos_error_guard()

    # Resumen
    logger.info(f"📊 RESUMEN:")
    logger.info(f"   • Fixes aplicados: {fixes_count}")
    logger.info(f"   • Guard creado: {'✅' if guard_created else '❌'}")

    if fixes_count > 0 or guard_created:
        logger.info(
            "✅ Corrección completada. Reinicia el host para aplicar cambios.")
        logger.info(
            "💡 Comando recomendado: az functionapp restart -g boat-rental-app-group -n copiloto-semantico-func-us2")
    else:
        logger.info(
            "ℹ️  No se aplicaron cambios - archivos ya corregidos o no encontrados")


if __name__ == "__main__":
    main()
