FROM mcr.microsoft.com/azure-functions/python:4-python3.11

# Instalar Azure CLI dentro del contenedor
RUN apt-get update && \
  apt-get install -y curl apt-transport-https lsb-release gnupg && \
  curl -sL https://aka.ms/InstallAzureCLIDeb | bash && \
  az version

# Variables obligatorias de Azure Functions
ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
  AzureFunctionsJobHost__Logging__Console__IsEnabled=true

# Directorio de trabajo (se usa /home/site/wwwroot porque ahí vive la Function App)
WORKDIR /home/site/wwwroot

# Copiar todo el proyecto
COPY . /home/site/wwwroot

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Asegurar permisos
RUN chmod -R 755 /home/site/wwwroot
