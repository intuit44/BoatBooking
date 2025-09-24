#!/bin/bash

# 🔐 Autenticación automática con Managed Identity
echo "🔐 Autenticando Azure CLI usando identidad administrada..."
az login --identity >/dev/null 2>&1

if [ $? -ne 0 ]; then
  echo "❌ Error al autenticar con MI (az login --identity)"
  exit 1
fi

echo "✅ Azure CLI autenticado correctamente."

# 🚀 Iniciar SSH en segundo plano
/usr/sbin/sshd -D &
SSH_PID=$!

# 🎯 Función para terminar procesos limpiamente
terminate_processes() {
    kill -TERM $SSH_PID 2>/dev/null
    kill -TERM $FUNC_PID 2>/dev/null
    exit 0
}

# 🛑 Capturar señales de parada
trap terminate_processes SIGTERM SIGINT

# 🚀 Iniciar el host de Azure Functions
exec /azure-functions-host/Microsoft.Azure.WebJobs.Script.WebHost &
FUNC_PID=$!

# ⏳ Esperar a que alguno termine
wait -n $SSH_PID $FUNC_PID

# 🔄 Cerrar el contenedor si algo finaliza
terminate_processes
