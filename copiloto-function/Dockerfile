FROM mcr.microsoft.com/azure-functions/python:4-python3.11

# SSH + Azure CLI
RUN apt-get update && \
  apt-get install -y curl apt-transport-https lsb-release gnupg openssh-server && \
  mkdir /var/run/sshd && \
  echo 'root:Docker!' | chpasswd && \
  sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
  echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config && \
  echo 'Port 2222' >> /etc/ssh/sshd_config

RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

WORKDIR /home/site/wwwroot

# Cache de deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código
COPY . .

# Env básicos
ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
  AzureFunctionsJobHost__Logging__Console__IsEnabled=true \
  FUNCTIONS_WORKER_RUNTIME=python \
  FUNCTIONS_EXTENSION_VERSION=~4

# Permisos
RUN chmod -R 755 /home/site/wwwroot && chown -R www-data:www-data /home/site/wwwroot

# HTTP + SSH
EXPOSE 80 2222

# 🔑 Arranca sshd y luego el host de Functions
CMD ["bash","-c","/usr/sbin/sshd -D & exec /azure-functions-host/Microsoft.Azure.WebJobs.Script.WebHost"]
