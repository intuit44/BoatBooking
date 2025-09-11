import requests
import json

# Cambia aquí para alternar entre local y Azure
USE_LOCAL = True

BASE_URL = "http://localhost:7071" if USE_LOCAL else "https://copiloto-semantico-func-us2.azurewebsites.net"


def call(endpoint, payload):
    url = f"{BASE_URL}{endpoint}"
    r = requests.post(url, json=payload)
    print(f"\n>>> POST {url} {payload}")
    print("Status:", r.status_code)
    try:
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(r.text)


if __name__ == "__main__":
    # ==== 1. Comando válido ====
    call("/api/ejecutar-cli", {"comando": "group list"})

    # ==== 2. Comando estilo CLI ====
    call("/api/ejecutar-cli", {"comando": "storage account list"})

    # ==== 3. Webapp list ====
    call("/api/ejecutar-cli", {"comando": "webapp list"})

    # ==== 4. Comando inválido ====
    call("/api/ejecutar-cli", {"comando": "vm list"})

    # ==== 5. Proxy invocar ====
    call("/api/invocar", {
        "endpoint": "ejecutar-cli",
        "method": "POST",
        "data": {"comando": "group list"}
    })

    # ==== 6. Proxy invocar con formato PLANO ====
    call("/api/invocar", {
        "endpoint": "ejecutar-cli",
        "method": "POST",
        "data": {"comando": "storage account list"}
    })

    # ==== 7. Proxy invocar con formato SEPARADO ====
    call("/api/invocar", {
        "endpoint": "ejecutar-cli",
        "method": "POST",
        "data": {"servicio": "storage", "comando": "account list"}
    })
