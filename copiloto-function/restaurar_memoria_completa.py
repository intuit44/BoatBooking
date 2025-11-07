"""
🔧 Script para restaurar la funcionalidad completa de memoria
Restaura el guardado automático de toda la conversación rica cuando se invoca un endpoint
"""

import logging
import sys
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def verificar_estado_actual():
    """Verifica el estado actual del sistema de memoria"""
    print("\n" + "="*60)
    print("🔍 VERIFICANDO ESTADO ACTUAL DEL SISTEMA DE MEMORIA")
    print("="*60)
    
    archivos_criticos = {
        "memory_route_wrapper.py": "Wrapper automático de memoria",
        "services/memory_service.py": "Servicio de memoria principal",
        "services/memory_decorator.py": "Decorador de memoria",
        "cosmos_memory_direct.py": "Acceso directo a Cosmos DB",
        "endpoints_search_memory.py": "Búsqueda en AI Search"
    }
    
    estado = {}
    for archivo, descripcion in archivos_criticos.items():
        ruta = os.path.join(os.path.dirname(__file__), archivo)
        existe = os.path.exists(ruta)
        estado[archivo] = existe
        print(f"  {'✅' if existe else '❌'} {archivo}: {descripcion}")
    
    return estado

def diagnosticar_problema():
    """Diagnostica qué está fallando en el sistema de memoria"""
    print("\n" + "="*60)
    print("🔍 DIAGNOSTICANDO PROBLEMAS")
    print("="*60)
    
    problemas = []
    
    # 1. Verificar que el wrapper esté aplicado
    try:
        with open("function_app.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "apply_memory_wrapper" in content:
                print("  ✅ Wrapper está siendo aplicado en function_app.py")
            else:
                print("  ❌ Wrapper NO está siendo aplicado")
                problemas.append("wrapper_no_aplicado")
    except Exception as e:
        print(f"  ❌ Error leyendo function_app.py: {e}")
        problemas.append("error_function_app")
    
    # 2. Verificar que memory_service esté guardando
    try:
        with open("services/memory_service.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "registrar_llamada" in content:
                print("  ✅ memory_service tiene método registrar_llamada")
            else:
                print("  ❌ memory_service NO tiene registrar_llamada")
                problemas.append("sin_registrar_llamada")
                
            if "memory_container" in content:
                print("  ✅ memory_service tiene conexión a Cosmos DB")
            else:
                print("  ❌ memory_service NO tiene conexión a Cosmos")
                problemas.append("sin_cosmos")
    except Exception as e:
        print(f"  ❌ Error leyendo memory_service.py: {e}")
        problemas.append("error_memory_service")
    
    # 3. Verificar indexación en AI Search
    try:
        with open("endpoints_search_memory.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "indexar_memoria_endpoint" in content:
                print("  ✅ AI Search tiene función de indexación")
            else:
                print("  ❌ AI Search NO tiene indexación")
                problemas.append("sin_indexacion")
    except Exception as e:
        print(f"  ❌ Error leyendo endpoints_search_memory.py: {e}")
        problemas.append("error_search")
    
    return problemas

def generar_plan_reparacion(problemas):
    """Genera un plan de reparación basado en los problemas encontrados"""
    print("\n" + "="*60)
    print("🔧 PLAN DE REPARACIÓN")
    print("="*60)
    
    if not problemas:
        print("  ✅ No se detectaron problemas críticos")
        print("\n  📝 RECOMENDACIONES:")
        print("     1. Verificar que los endpoints estén guardando correctamente")
        print("     2. Revisar logs de Azure Functions para confirmar guardado")
        print("     3. Ejecutar script de diagnóstico: python diagnostico_memoria_semantica.py")
        return
    
    print("\n  ❌ PROBLEMAS DETECTADOS:")
    for i, problema in enumerate(problemas, 1):
        print(f"     {i}. {problema}")
    
    print("\n  🔧 ACCIONES REQUERIDAS:")
    
    if "wrapper_no_aplicado" in problemas:
        print("\n     1️⃣ APLICAR WRAPPER AUTOMÁTICO")
        print("        - Verificar que function_app.py tenga:")
        print("          from memory_route_wrapper import apply_memory_wrapper")
        print("          apply_memory_wrapper(app)")
        print("        - Reiniciar Azure Functions")
    
    if "sin_registrar_llamada" in problemas:
        print("\n     2️⃣ RESTAURAR MÉTODO registrar_llamada")
        print("        - El método debe estar en memory_service.py")
        print("        - Debe guardar en Cosmos DB Y en AI Search")
    
    if "sin_cosmos" in problemas:
        print("\n     3️⃣ CONFIGURAR COSMOS DB")
        print("        - Verificar variables de entorno:")
        print("          COSMOS_ENDPOINT")
        print("          COSMOS_KEY")
        print("          COSMOS_DATABASE_NAME")
        print("          COSMOS_CONTAINER_NAME")
    
    if "sin_indexacion" in problemas:
        print("\n     4️⃣ CONFIGURAR AI SEARCH")
        print("        - Verificar variables de entorno:")
        print("          AZURE_SEARCH_ENDPOINT")
        print("          AZURE_SEARCH_KEY")
        print("          AZURE_SEARCH_INDEX_NAME")

def verificar_configuracion_env():
    """Verifica que las variables de entorno estén configuradas"""
    print("\n" + "="*60)
    print("🔍 VERIFICANDO VARIABLES DE ENTORNO")
    print("="*60)
    
    vars_requeridas = {
        "COSMOS_ENDPOINT": "Endpoint de Cosmos DB",
        "COSMOS_KEY": "Clave de Cosmos DB",
        "COSMOS_DATABASE_NAME": "Nombre de base de datos",
        "COSMOS_CONTAINER_NAME": "Nombre de contenedor",
        "AZURE_SEARCH_ENDPOINT": "Endpoint de AI Search",
        "AZURE_SEARCH_KEY": "Clave de AI Search",
        "AZURE_SEARCH_INDEX_NAME": "Nombre del índice"
    }
    
    faltantes = []
    for var, descripcion in vars_requeridas.items():
        valor = os.getenv(var)
        if valor:
            print(f"  ✅ {var}: {descripcion}")
        else:
            print(f"  ❌ {var}: {descripcion} - NO CONFIGURADA")
            faltantes.append(var)
    
    return faltantes

def main():
    """Función principal"""
    print("\n" + "="*60)
    print("🚀 RESTAURACIÓN DE MEMORIA COMPLETA")
    print("="*60)
    
    # 1. Verificar estado actual
    estado = verificar_estado_actual()
    
    # 2. Diagnosticar problemas
    problemas = diagnosticar_problema()
    
    # 3. Verificar configuración
    vars_faltantes = verificar_configuracion_env()
    
    # 4. Generar plan de reparación
    generar_plan_reparacion(problemas)
    
    # 5. Resumen final
    print("\n" + "="*60)
    print("📊 RESUMEN")
    print("="*60)
    print(f"  Archivos críticos: {sum(estado.values())}/{len(estado)} presentes")
    print(f"  Problemas detectados: {len(problemas)}")
    print(f"  Variables faltantes: {len(vars_faltantes)}")
    
    if not problemas and not vars_faltantes:
        print("\n  ✅ SISTEMA DE MEMORIA ESTÁ CONFIGURADO CORRECTAMENTE")
        print("\n  📝 PRÓXIMOS PASOS:")
        print("     1. Reiniciar Azure Functions si hiciste cambios")
        print("     2. Invocar un endpoint y verificar que se guarde en Cosmos DB")
        print("     3. Ejecutar: python diagnostico_memoria_semantica.py")
    else:
        print("\n  ⚠️ SE REQUIERE ACCIÓN MANUAL")
        print("\n  📝 SIGUE EL PLAN DE REPARACIÓN ARRIBA")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
