# Crear un archivo Dockerfile en el directorio actual
$dockerfileContent = @'
FROM mcr.microsoft.com/azure-functions/python:4-python3.11

# Dependencias del sistema para Azure CLI
RUN apt-get update && \
    apt-get install -y curl apt-transport-https lsb-release gnupg && \
    rm -rf /var/lib/apt/lists/*

# Instalar Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# (Opcional) extensiones de Azure CLI
# RUN az extension add --name account --yes && \
#     az extension add --name storage-preview --yes && \
#     az extension add --name azure-devops --yes

# Directorio de trabajo de Functions
WORKDIR /home/site/wwwroot

# Copiar el código de la Function App
COPY . .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Permisos
RUN chmod -R 755 /home/site/wwwroot && \
    chown -R www-data:www-data /home/site/wwwroot
'@

# Escribir el contenido en un archivo Dockerfile
Set-Content -Path ./Dockerfile -Value $dockerfileContent