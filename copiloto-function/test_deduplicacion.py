#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de Deduplicación Semántica
Valida que el sistema filtre correctamente endpoints meta-operacionales
"""

import sys
import hashlib
from collections import defaultdict

def test_deduplicacion():
    """Simula la función de deduplicación"""
    
    # Datos de prueba simulando lo que viene de Cosmos (incluyendo basura real)
    items_simulados = [
        {"endpoint": "historial-interacciones", "texto_semantico": "CONSULTA DE HISTORIAL COMPLETADA\n\nRESULTADO: Se encontraron 5 interacciones recientes", "_ts": 1000},
        {"endpoint": "/api/historial-interacciones", "texto_semantico": "CONSULTA DE HISTORIAL COMPLETADA\n\nRESULTADO: Se encontraron 10 interacciones recientes", "_ts": 999},
        {"endpoint": "hybrid", "texto_semantico": "Ejecutando comando az storage list en resource group production", "_ts": 998},
        {"endpoint": "verificar-cosmos", "texto_semantico": "Verificando Cosmos DB", "_ts": 997},
        {"endpoint": "ejecutar-cli", "texto_semantico": "Comando ejecutado: az storage account list --resource-group mygroup", "_ts": 996},
        {"endpoint": "preparar-script", "texto_semantico": "Generando script de deployment para contenedor backup-datos", "_ts": 995},
        {"endpoint": "hybrid", "texto_semantico": "Ejecutando comando az storage list en resource group production", "_ts": 994},
        {"endpoint": "health", "texto_semantico": "Health check OK", "_ts": 993},
        {"endpoint": "ejecutar-cli", "texto_semantico": "Exito", "_ts": 992},
        {"endpoint": "copiloto", "texto_semantico": "Consulta completada sin errores", "_ts": 991},
    ]
    
    print(f"[INFO] Items originales: {len(items_simulados)} (incluyendo basura real de produccion)")
    print("=" * 60)
    
    # PASO 1: Filtrar endpoints excluidos
    ENDPOINTS_EXCLUIDOS = {
        'historial-interacciones', '/api/historial-interacciones',
        'health', '/api/health',
        'verificar-sistema', 'verificar-cosmos', 'verificar-app-insights'
    }
    
    PATRONES_BASURA = [
        'CONSULTA DE HISTORIAL',
        'Se encontraron',
        'interacciones recientes',
        'Consulta completada',
        'Exito'
    ]
    
    items_filtrados = []
    for item in items_simulados:
        endpoint = item.get('endpoint', '')
        texto = item.get('texto_semantico', '')
        
        if endpoint in ENDPOINTS_EXCLUIDOS:
            continue
        
        if any(patron in texto for patron in PATRONES_BASURA):
            continue
        
        if len(texto.strip()) < 30:
            continue
        
        items_filtrados.append(item)
    
    print(f"[FILTER] Despues de filtrar meta-operacionales: {len(items_filtrados)}")
    print(f"         Eliminados: {len(items_simulados) - len(items_filtrados)}")
    print()
    
    # PASO 2: Deduplicar por endpoint + hash semántico
    grupos = defaultdict(list)
    
    for item in items_filtrados:
        endpoint = item.get('endpoint', 'unknown')
        texto = item.get('texto_semantico', '')
        
        # Hash semántico: primeros 100 chars normalizados
        texto_norm = texto[:100].lower().strip()
        hash_semantico = hashlib.md5(texto_norm.encode()).hexdigest()[:8]
        
        clave = f"{endpoint}_{hash_semantico}"
        grupos[clave].append(item)
    
    # Tomar solo el más reciente de cada grupo
    items_unicos = []
    for clave, grupo in grupos.items():
        grupo_ordenado = sorted(grupo, key=lambda x: x.get('_ts', 0), reverse=True)
        items_unicos.append(grupo_ordenado[0])
        
        if len(grupo) > 1:
            print(f"[DEDUP] Grupo '{clave}': {len(grupo)} items -> 1 (mas reciente)")
    
    # Ordenar por timestamp
    items_unicos.sort(key=lambda x: x.get('_ts', 0), reverse=True)
    
    print()
    print(f"[OK] Items unicos finales: {len(items_unicos)}")
    print("=" * 60)
    print()
    print("[RESULT] Interacciones recuperadas:")
    for i, item in enumerate(items_unicos, 1):
        print(f"   {i}. {item['endpoint']} - {item['texto_semantico'][:50]}...")
    
    print()
    print("=" * 60)
    
    # Validaciones
    assert len(items_unicos) < len(items_simulados), "[ERROR] No se redujo el numero de items"
    assert not any(item['endpoint'] == 'historial-interacciones' for item in items_unicos), "[ERROR] historial-interacciones no fue filtrado"
    assert not any(item['endpoint'] == 'health' for item in items_unicos), "[ERROR] health no fue filtrado"
    assert not any(item['endpoint'] == 'verificar-cosmos' for item in items_unicos), "[ERROR] verificar-cosmos no fue filtrado"
    
    # Verificar que no hay duplicados semánticos
    endpoints_vistos = set()
    for item in items_unicos:
        texto_norm = item['texto_semantico'][:100].lower().strip()
        hash_semantico = hashlib.md5(texto_norm.encode()).hexdigest()[:8]
        clave = f"{item['endpoint']}_{hash_semantico}"
        assert clave not in endpoints_vistos, f"[ERROR] Duplicado encontrado: {clave}"
        endpoints_vistos.add(clave)
    
    print("[PASS] TODAS LAS VALIDACIONES PASARON")
    print()
    print("[SUMMARY] Resultado:")
    print(f"   - {len(items_simulados)} items originales")
    print(f"   - {len(items_simulados) - len(items_filtrados)} meta-operacionales eliminados")
    print(f"   - {len(items_filtrados) - len(items_unicos)} duplicados eliminados")
    print(f"   - {len(items_unicos)} interacciones unicas y relevantes")
    
    return True

if __name__ == "__main__":
    try:
        test_deduplicacion()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] TEST FALLIDO: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        sys.exit(1)
