# Script para debuggear qué está recibiendo autocorregir_http
import json
from datetime import datetime

# Agregar logging temporal a autocorregir_http
debug_log = {
    "timestamp": datetime.now().isoformat(),
    "problema": "La función autocorregir_http se ejecuta pero no registra logs",
    "causa_probable": "Azure Monitor no envía los headers/body requeridos",
    "solucion": "Modificar la función para ser más tolerante con webhooks de Azure Monitor"
}

print(json.dumps(debug_log, indent=2, ensure_ascii=False))