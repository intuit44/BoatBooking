# servidor_local.py - Corre en TU PC, no en Azure
from flask import Flask, request, jsonify
import subprocess
import hashlib

app = Flask(__name__)

# Token secreto para autenticación
SECRET_TOKEN = "tu-token-secreto-aqui"


@app.route('/ejecutar-local', methods=['POST'])
def ejecutar_local():
    # Verificar token
    if request.headers.get('Authorization') != f"Bearer {SECRET_TOKEN}":
        return jsonify({"error": "No autorizado"}), 401

    data = request.json
    if not data:
        return jsonify({"error": "JSON data required"}), 400
    comando = data.get('comando')

    # Lista blanca de comandos permitidos
    COMANDOS_PERMITIDOS = [
        "docker build",
        "docker tag",
        "docker push",
        "az acr login",
        "az functionapp"
    ]

    # Verificar que el comando empiece con algo permitido
    if not any(comando.startswith(cmd) for cmd in COMANDOS_PERMITIDOS):
        return jsonify({"error": "Comando no permitido"}), 403

    try:
        result = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos para Docker build
        )

        return jsonify({
            "comando": comando,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "exito": result.returncode == 0
        }), 200 if result.returncode == 0 else 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(port=8082, host='127.0.0.1')  # Solo localhost
