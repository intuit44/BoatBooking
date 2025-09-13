FROM mcr.microsoft.com/azure-functions/python:4-python3.11

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
  AzureFunctionsJobHost__Logging__Console__IsEnabled=true

WORKDIR /app

COPY . /home/site/wwwroot

RUN pip install -r /home/site/wwwroot/requirements.txt

RUN chmod -R 755 /home/site/wwwroot
