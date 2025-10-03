#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificar todos los archivos de logs para ver si hay nuevas entradas
"""
import json
from datetime import datetime
from pathlib import Path

def check_all_logs():
    """Verifica todos los archivos de logs"""
    
    files_to_check = [
        "scripts/semantic_log.jsonl",
        "scripts/semantic_commits.json", 
        "scripts/pending_fixes.json"
    ]
    
    print(f"Verificando logs a las: {datetime.now().isoformat()}")
    print("=" * 60)
    
    for file_path in files_to_check:
        path = Path(file_path)
        print(f"\n{file_path}:")
        
        if not path.exists():
            print("  Archivo no existe")
            continue
            
        try:
            if file_path.endswith('.jsonl'):
                # Archivo JSONL - leer línea por línea
                with open(path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    print(f"  Total lineas: {len(lines)}")
                    
                    # Mostrar las ultimas 3 lineas
                    print("  Ultimas entradas:")
                    for line in lines[-3:]:
                        try:
                            entry = json.loads(line.strip())
                            fecha = entry.get('fecha', entry.get('timestamp', 'sin fecha'))
                            tipo = entry.get('tipo', 'sin tipo')
                            print(f"    - {fecha}: {tipo}")
                        except:
                            print(f"    - {line.strip()[:50]}...")
            else:
                # Archivo JSON normal
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if isinstance(data, list):
                        print(f"  Total entradas: {len(data)}")
                        
                        # Mostrar las ultimas 3 entradas
                        print("  Ultimas entradas:")
                        for entry in data[-3:]:
                            if isinstance(entry, dict):
                                fecha = entry.get('fecha', entry.get('timestamp', 'sin fecha'))
                                tipo = entry.get('tipo', entry.get('accion', 'sin tipo'))
                                print(f"    - {fecha}: {tipo}")
                            else:
                                print(f"    - {str(entry)[:50]}...")
                    else:
                        print(f"  Tipo de datos: {type(data).__name__}")
                        
        except Exception as e:
            print(f"  Error leyendo archivo: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Verificación completada")

if __name__ == "__main__":
    check_all_logs()