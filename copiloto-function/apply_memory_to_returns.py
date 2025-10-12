#!/usr/bin/env python3
"""
Script to apply memory to return statements of critical endpoints
"""

import re

def apply_memory_to_returns():
    """Apply memory to return statements in critical endpoints"""
    
    # Read the function_app.py file
    with open("function_app.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Pattern to find return statements that return JSON responses
    # Look for patterns like: return func.HttpResponse(json.dumps(result), ...)
    patterns_to_replace = [
        # Pattern 1: return func.HttpResponse(json.dumps(variable), ...)
        (r'(\s+)(return func\.HttpResponse\(\s*json\.dumps\(([^,)]+)\),([^)]+)\))', 
         r'\1\3 = aplicar_memoria_manual(req, \3)\n\1return func.HttpResponse(json.dumps(\3),\4)'),
        
        # Pattern 2: return func.HttpResponse(json.dumps({...}), ...)  
        (r'(\s+)(return func\.HttpResponse\(\s*json\.dumps\((\{[^}]+\})\),([^)]+)\))',
         r'\1resultado_temp = \3\n\1resultado_temp = aplicar_memoria_manual(req, resultado_temp)\n\1return func.HttpResponse(json.dumps(resultado_temp),\4)'),
    ]
    
    changes_made = 0
    
    for pattern, replacement in patterns_to_replace:
        # Count matches before replacement
        matches_before = len(re.findall(pattern, content))
        
        # Apply replacement
        content = re.sub(pattern, replacement, content)
        
        # Count matches after replacement (should be 0 if all were replaced)
        matches_after = len(re.findall(pattern, content))
        
        changes_made += (matches_before - matches_after)
    
    # Write back the modified content
    with open("function_app.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Applied memory to {changes_made} return statements")

if __name__ == "__main__":
    apply_memory_to_returns()