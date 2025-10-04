#!/usr/bin/env python3
import os

def test_paths():
    paths = [
        "copiloto-function/function_app.py",
        "c:\\ProyectosSimbolicos\\boat-rental-app\\copiloto-function\\function_app.py"
    ]
    
    for path in paths:
        exists = os.path.exists(path)
        print(f"[TEST] {path} -> {exists}")
        if exists:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                print(f"[SUCCESS] Read {len(content)} chars")
                print(f"[PREVIEW] {content[:100]}...")
                return True
            except Exception as e:
                print(f"[ERROR] {e}")
    
    return False

if __name__ == "__main__":
    test_paths()