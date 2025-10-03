#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor para verificar si aparecen nuevos logs después del parche
"""
import json
import time
from datetime import datetime
from pathlib import Path

def monitor_logs():
    """Monitorea los archivos de logs para ver cambios"""
    
    semantic_log = Path("scripts/semantic_log.jsonl")
    pending_fixes = Path("scripts/pending_fixes.json")
    
    print(f"Monitoreando logs desde: {datetime.now().isoformat()}")
    print("=" * 50)
    
    # Leer estado inicial
    initial_semantic_lines = 0
    initial_pending_count = 0
    
    if semantic_log.exists():
        with open(semantic_log, 'r', encoding='utf-8') as f:
            initial_semantic_lines = len(f.readlines())
    
    if pending_fixes.exists():
        with open(pending_fixes, 'r', encoding='utf-8') as f:
            data = json.load(f)
            initial_pending_count = len(data)
    
    print(f"Estado inicial:")
    print(f"  - semantic_log.jsonl: {initial_semantic_lines} líneas")
    print(f"  - pending_fixes.json: {initial_pending_count} fixes")
    print()
    
    # Monitorear por 5 minutos
    for i in range(30):  # 30 iteraciones de 10 segundos = 5 minutos
        time.sleep(10)
        
        current_semantic_lines = 0
        current_pending_count = 0
        
        if semantic_log.exists():
            with open(semantic_log, 'r', encoding='utf-8') as f:
                current_semantic_lines = len(f.readlines())
        
        if pending_fixes.exists():
            with open(pending_fixes, 'r', encoding='utf-8') as f:
                data = json.load(f)
                current_pending_count = len(data)
        
        # Verificar cambios
        semantic_changed = current_semantic_lines > initial_semantic_lines
        pending_changed = current_pending_count > initial_pending_count
        
        if semantic_changed or pending_changed:
            print(f"CAMBIO DETECTADO a las {datetime.now().isoformat()}")
            print(f"  - semantic_log.jsonl: {current_semantic_lines} líneas (+{current_semantic_lines - initial_semantic_lines})")
            print(f"  - pending_fixes.json: {current_pending_count} fixes (+{current_pending_count - initial_pending_count})")
            
            # Mostrar nuevas líneas en semantic_log
            if semantic_changed:
                print("\nNuevas entradas en semantic_log.jsonl:")
                with open(semantic_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[initial_semantic_lines:]:
                        try:
                            entry = json.loads(line.strip())
                            print(f"  - {entry.get('tipo', 'unknown')}: {entry.get('mensaje', 'sin mensaje')}")
                        except:
                            print(f"  - {line.strip()}")
            
            # Mostrar nuevos fixes
            if pending_changed:
                print("\nNuevos fixes en pending_fixes.json:")
                with open(pending_fixes, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for fix in data[initial_pending_count:]:
                        print(f"  - {fix.get('id', 'unknown')}: {fix.get('accion', 'sin acción')}")
            
            return True
        
        print(f"Iteración {i+1}/30 - Sin cambios detectados")
    
    print("Monitoreo completado - No se detectaron cambios")
    return False

if __name__ == "__main__":
    monitor_logs()