#!/bin/bash

# Variables
ACR_NAME="miacr"
CONTAINER_NAME="copiloto-func-azcli"
NEW_TAG="1.0.1"

# Paso 1: Compilar la nueva imagen del contenedor
echo "Compilando la nueva imagen del contenedor..."
docker build -t $ACR_NAME.azurecr.io/$CONTAINER_NAME:$NEW_TAG .

# Paso 2: Autenticarse contra el ACR
echo "Autenticándose contra el Azure Container Registry..."
az acr login --name $ACR_NAME

# Paso 3: Etiquetar la imagen
echo "Etiquetando la imagen..."
docker tag $CONTAINER_NAME:$NEW_TAG $ACR_NAME.azurecr.io/$CONTAINER_NAME:$NEW_TAG

# Paso 4: Subir la imagen al ACR (despliegue no ejecutado)
echo "La imagen está lista para ser subida al ACR, pero el despliegue no se ejecutará todavía."
echo "Para subir la imagen, ejecuta: docker push $ACR_NAME.azurecr.io/$CONTAINER_NAME:$NEW_TAG"

# Fin del script
echo "Script de despliegue generado con éxito."