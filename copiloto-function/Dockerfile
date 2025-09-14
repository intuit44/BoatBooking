FROM mcr.microsoft.com/azure-functions/python:4-python3.11

# Instalar Azure CLI primero
RUN apt-get update && \
  apt-get install -y curl apt-transport-https lsb-release gnupg && \
  curl -sL https://aka.ms/InstallAzureCLIDeb | bash

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
  AzureFunctionsJobHost__Logging__Console__IsEnabled=true

WORKDIR /app

COPY . /home/site/wwwroot

RUN pip install -r /home/site/wwwroot/requirements.txt

RUN chmod -R 755 /home/site/wwwroot
