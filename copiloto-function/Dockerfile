FROM mcr.microsoft.com/azure-functions/python:4-python3.11

# 🔧 Herramientas esenciales de diagnóstico y operaciones
RUN apt-get update && \
  apt-get install -y \
  bash \
  iproute2 \
  traceroute \
  tcpdump \
  mtr \
  iputils-ping \
  curl \
  wget \
  dnsutils \
  net-tools \
  jq \
  git \
  vim-tiny \
  unzip \
  zip \
  less \
  procps \
  htop \
  tree \
  file \
  lsof \
  strace \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# 🔐 Docker CLI (solo cliente, sin engine)
RUN curl -fsSL https://get.docker.com -o get-docker.sh && \
  sh get-docker.sh --docker-engine=false --docker-cli=true && \
  rm get-docker.sh

# 🐍 Azure CLI
RUN apt-get update && \
  apt-get install -y curl apt-transport-https lsb-release gnupg && \
  curl -sL https://aka.ms/InstallAzureCLIDeb | bash && \
  az version

# Variables base de Azure Functions + MCP (sin credenciales embebidas)
ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
  AzureFunctionsJobHost__Logging__Console__IsEnabled=true \
  WEBSITES_PORT=80 \
  MCP_TRANSPORT=http \
  MCP_HOST=0.0.0.0 \
  MCP_PORT=8000

EXPOSE 80
WORKDIR /home/site/wwwroot

# Copiar todo el proyecto
COPY . /home/site/wwwroot

# Script de arranque combinado (Functions + MCP)
RUN echo '#!/bin/bash' > /start.sh && \
    echo 'set -e' >> /start.sh && \
    echo '/azure-functions-host/Microsoft.Azure.WebJobs.Script.WebHost & ' >> /start.sh && \
    echo 'python /home/site/wwwroot/mcp_redis_wrapper_server.py' >> /start.sh && \
    chmod +x /start.sh

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Asegurar permisos
RUN chmod -R 755 /home/site/wwwroot

# Exponer puertos Functions (80) y MCP (8000)
EXPOSE 80 8000

# Comando de inicio combinado
CMD ["/bin/bash", "/start.sh"]
