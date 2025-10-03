#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor completo del flujo de alertas
"""
import json
import time
from datetime import datetime
from pathlib import Path

def monitor_alert_flow():
    """Monitorea todo el flujo de alertas"""
    
    print(f"MONITOREANDO FLUJO DE ALERTAS")
    print(f"Iniciado: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Estado inicial
    semantic_log = Path("scripts/semantic_log.jsonl")
    semantic_commits = Path("scripts/semantic_commits.json")
    pending_fixes = Path("scripts/pending_fixes.json")
    
    initial_counts = {}
    for file_path in [semantic_log, semantic_commits, pending_fixes]:
        if file_path.exists():
            if file_path.suffix == '.jsonl':
                with open(file_path, 'r', encoding='utf-8') as f:
                    initial_counts[file_path.name] = len(f.readlines())
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    initial_counts[file_path.name] = len(data) if isinstance(data, list) else 1
        else:
            initial_counts[file_path.name] = 0
    
    print("Estado inicial:")
    for filename, count in initial_counts.items():
        print(f"  {filename}: {count} entradas")
    print()
    
    # Monitorear por 10 minutos (20 iteraciones de 30 segundos)
    for i in range(20):
        time.sleep(30)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Verificacion {i+1}/20...")
        
        changes_detected = False
        
        for file_path in [semantic_log, semantic_commits, pending_fixes]:
            if file_path.exists():
                current_count = 0
                if file_path.suffix == '.jsonl':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        current_count = len(f.readlines())
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        current_count = len(data) if isinstance(data, list) else 1
                
                initial_count = initial_counts[file_path.name]
                if current_count > initial_count:
                    changes_detected = True
                    print(f"  CAMBIO en {file_path.name}: {current_count} (+{current_count - initial_count})")
                    
                    # Mostrar nuevas entradas
                    if file_path.suffix == '.jsonl':
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            for line in lines[initial_count:]:
                                try:
                                    entry = json.loads(line.strip())
                                    tipo = entry.get('tipo', 'unknown')
                                    fecha = entry.get('fecha', entry.get('timestamp', 'sin fecha'))
                                    print(f"    - {tipo}: {fecha}")
                                except:
                                    print(f"    - {line.strip()[:50]}...")
                    else:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            for entry in data[initial_count:]:
                                if isinstance(entry, dict):
                                    tipo = entry.get('tipo', entry.get('accion', 'unknown'))
                                    fecha = entry.get('fecha', entry.get('timestamp', 'sin fecha'))
                                    print(f"    - {tipo}: {fecha}")
        
        if changes_detected:
            print("\nALERTA DETECTADA Y PROCESADA!")
            return True
        else:
            print("  Sin cambios detectados")
    
    print("\nTiempo de monitoreo completado - No se detectaron cambios")
    return False

if __name__ == "__main__":
    success = monitor_alert_flow()
    if success:
        print("\nEl flujo de alertas funciona correctamente!")
    else:
        print("\nEl flujo de alertas necesita revision")