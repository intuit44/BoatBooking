FROM mcr.microsoft.com/azure-functions/python:4-python3.11

# 🔧 Herramientas esenciales de diagnóstico y operaciones
RUN apt-get update && \
  apt-get install -y \
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

# Variables obligatorias de Azure Functions + Application Insights
ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
  AzureFunctionsJobHost__Logging__Console__IsEnabled=true \
  WEBSITES_PORT=80 \
  APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=bc768980-75a6-4f2d-b6dd-fcb1e524f1ed;IngestionEndpoint=https://eastus2-3.in.applicationinsights.azure.com/;LiveEndpoint=https://eastus2.livediagnostics.monitor.azure.com/;ApplicationId=35e88cd8-54da-4b1d-9946-f98855374d53" \
  APPINSIGHTS_INSTRUMENTATIONKEY="bc768980-75a6-4f2d-b6dd-fcb1e524f1ed"

EXPOSE 80
WORKDIR /home/site/wwwroot

# Copiar todo el proyecto
COPY . /home/site/wwwroot

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Asegurar permisos
RUN chmod -R 755 /home/site/wwwroot

# Comando de inicio para Azure Functions
CMD ["/azure-functions-host/Microsoft.Azure.WebJobs.Script.WebHost"]