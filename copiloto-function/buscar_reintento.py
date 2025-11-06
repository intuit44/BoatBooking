import re

with open('function_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar el patrón de re-ejecución
pattern = r'(if.*stdout.*empty|if.*returncode.*0.*stdout|comando_con_outstring)'
matches = re.finditer(pattern, content, re.IGNORECASE)

for match in matches:
    start = max(0, match.start() - 500)
    end = min(len(content), match.end() + 500)
    print("="*80)
    print(f"Encontrado en posición {match.start()}:")
    print(content[start:end])
    print("="*80)
