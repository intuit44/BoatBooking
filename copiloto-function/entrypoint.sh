#!/bin/bash

# Iniciar SSH en background
/usr/sbin/sshd -D &

# Capturar el PID de SSH
SSH_PID=$!

# Función para terminar procesos al recibir señal
terminate_processes() {
    kill -TERM $SSH_PID 2>/dev/null
    exit 0
}

# Configurar trap para señales
trap terminate_processes SIGTERM SIGINT

# Ejecutar el host de Functions
exec /azure-functions-host/Microsoft.Azure.WebJobs.Script.WebHost &

# Capturar PID de Functions
FUNC_PID=$!

# Esperar a que cualquiera de los procesos termine
wait -n $SSH_PID $FUNC_PID

# Si llegamos aquí, algún proceso terminó
terminate_processes