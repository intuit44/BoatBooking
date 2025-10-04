#!/usr/bin/env python3
"""
Prueba local del endpoint ejecutar_cli_http mejorado
"""
import json
import subprocess
import platform

def simulate_ejecutar_cli_local(comando):
    """Simula la lógica mejorada del endpoint localmente"""
    print(f"[TEST] Simulando comando: {comando}")
    
    try:
        # Ejecutar comando localmente
        result = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Aplicar la lógica mejorada
        stdout_raw = result.stdout.strip() if result.stdout else ""
        stderr_raw = result.stderr.strip() if result.stderr else ""
        
        # Intentar parsear JSON
        stdout_parsed = None
        try:
            if stdout_raw:
                stdout_parsed = json.loads(stdout_raw)
        except json.JSONDecodeError:
            pass
        
        # Respuesta estructurada
        response_data = {
            "exito": result.returncode == 0,
            "comando_ejecutado": comando,
            "codigo_salida": result.returncode,
            "output": {
                "raw": stdout_raw,
                "parsed": stdout_parsed,
                "type": "json" if stdout_parsed else "text",
                "lines": stdout_raw.split('\n') if stdout_raw else []
            },
            "stderr": stderr_raw,
            "summary": f"Comando '{comando}' ejecutado. Output: {len(stdout_raw)} chars"
        }
        
        return response_data
        
    except Exception as e:
        return {
            "exito": False,
            "error": str(e),
            "comando_ejecutado": comando
        }

def test_commands():
    """Prueba varios tipos de comandos"""
    
    # Comandos de prueba según el sistema
    if platform.system().lower().startswith("win"):
        test_cases = [
            {"name": "Comando simple", "cmd": "echo Hello World"},
            {"name": "Comando con JSON", "cmd": "echo {\"test\": \"value\", \"number\": 123}"},
            {"name": "Comando multilinea", "cmd": "dir /b"},
            {"name": "Comando que falla", "cmd": "comando_inexistente"}
        ]
    else:
        test_cases = [
            {"name": "Comando simple", "cmd": "echo 'Hello World'"},
            {"name": "Comando con JSON", "cmd": "echo '{\"test\": \"value\", \"number\": 123}'"},
            {"name": "Comando multilinea", "cmd": "ls -la"},
            {"name": "Comando que falla", "cmd": "comando_inexistente"}
        ]
    
    print("=" * 60)
    print("PRUEBAS DEL ENDPOINT EJECUTAR_CLI_HTTP MEJORADO")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[PRUEBA {i}] {test_case['name']}")
        print(f"[COMANDO] {test_case['cmd']}")
        
        result = simulate_ejecutar_cli_local(test_case['cmd'])
        
        print(f"[EXITO] {result.get('exito')}")
        print(f"[CODIGO] {result.get('codigo_salida')}")
        
        if result.get('exito'):
            output = result.get('output', {})
            print(f"[TYPE] {output.get('type')}")
            print(f"[LINES] {len(output.get('lines', []))}")
            
            if output.get('parsed'):
                print(f"[PARSED] {output['parsed']}")
            else:
                raw = output.get('raw', '')
                preview = raw[:100] + "..." if len(raw) > 100 else raw
                print(f"[RAW] {preview}")
                
            print(f"[SUMMARY] {result.get('summary')}")
        else:
            print(f"[ERROR] {result.get('error')}")
        
        print("-" * 40)
    
    print(f"\n[SISTEMA] {platform.system()}")
    print("[DONE] Pruebas completadas")

if __name__ == "__main__":
    test_commands()