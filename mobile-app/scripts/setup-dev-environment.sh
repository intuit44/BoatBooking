#!/bin/bash

# Script de configuración completa del entorno de desarrollo
# Uso: curl -fsSL https://raw.githubusercontent.com/tu-repo/setup-dev-environment.sh | bash

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 CONFIGURACIÓN DEL ENTORNO DE DESARROLLO${NC}"
echo -e "${BLUE}======================================${NC}"

# Función para mostrar progreso
show_progress() {
    echo -e "${BLUE}$1...${NC}"
}

# Función para mostrar éxito
show_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Función para mostrar error
show_error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# 1. Actualizar sistema
show_progress "1. Actualizando sistema"
sudo apt update && sudo apt upgrade -y || show_error "Error actualizando sistema"
show_success "Sistema actualizado"

# 2. Instalar dependencias básicas
show_progress "2. Instalando dependencias básicas"
sudo apt install -y curl wget git unzip build-essential python3 python3-pip || show_error "Error instalando dependencias"
show_success "Dependencias instaladas"

# 3. Instalar Node.js vía nvm
show_progress "3. Instalando Node.js"
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm install --lts
nvm use --lts
show_success "Node.js instalado: $(node --version)"

# 4. Instalar herramientas globales
show_progress "4. Instalando herramientas de desarrollo"
npm install -g @aws-amplify/cli expo-cli yarn || show_error "Error instalando herramientas"
show_success "Herramientas instaladas"

# 5. Instalar y configurar AWS CLI
show_progress "5. Instalando AWS CLI"
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm -rf aws awscliv2.zip

# 6. Configurar AWS Credentials
show_progress "6. Configurando AWS Credentials"
mkdir -p ~/.aws

echo -e "${YELLOW}🔐 Ingresa tus credenciales de AWS:${NC}"
read -p "AWS Access Key ID: " aws_access_key
read -p "AWS Secret Access Key: " aws_secret_key
read -p "AWS Region [us-east-1]: " aws_region
aws_region=${aws_region:-us-east-1}

cat > ~/.aws/credentials << EOL
[default]
aws_access_key_id = ${aws_access_key}
aws_secret_access_key = ${aws_secret_key}
region = ${aws_region}
EOL

show_success "AWS configurado"

# 7. Clonar y configurar el proyecto
show_progress "7. Configurando el proyecto"
cd ~
git clone https://github.com/tu-usuario/boat-rental-app.git || show_error "Error clonando repositorio"
cd boat-rental-app

# 8. Configurar Amplify
show_progress "8. Configurando Amplify"
cd mobile-app
amplify pull --yes || show_error "Error configurando Amplify"

# 9. Instalar dependencias del proyecto
show_progress "9. Instalando dependencias del proyecto"
yarn install || show_error "Error instalando dependencias"

# 10. Verificar configuración de autenticación social
show_progress "10. Verificando configuración de autenticación social"
if [ -f "src/config/socialConfig.ts" ]; then
    echo -e "${YELLOW}⚠️ Verificar IDs de autenticación social en src/config/socialConfig.ts${NC}"
    echo -e "${YELLOW}Facebook App ID: $(grep -o 'FACEBOOK_APP_ID.*' src/config/socialConfig.ts)${NC}"
    echo -e "${YELLOW}Google Client ID: $(grep -o 'GOOGLE_CLIENT_ID.*' src/config/socialConfig.ts)${NC}"
fi

# 11. Verificar estructura del proyecto
show_progress "11. Verificando estructura del proyecto"
required_dirs=(
    "amplify"
    "src/screens"
    "src/store"
    "src/services"
    "src/components"
)

for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo -e "${RED}⚠️ Directorio faltante: $dir${NC}"
    else
        echo -e "${GREEN}✅ Directorio presente: $dir${NC}"
    fi
done

# 12. Verificar conexión con backend
show_progress "12. Verificando conexión con backend"
amplify status || show_error "Error verificando estado de Amplify"

# 13. Configurar variables de entorno
show_progress "13. Configurando variables de entorno"
if [ ! -f ".env" ]; then
    cat > .env << EOL
EXPO_PUBLIC_API_URL=https://your-api-gateway-url.amazonaws.com/dev
EXPO_PUBLIC_AWS_REGION=${aws_region}
EOL
    show_success "Archivo .env creado"
fi

# 14. Verificar configuración de Expo
show_progress "14. Verificando configuración de Expo"
if [ -f "app.json" ]; then
    echo -e "${GREEN}✅ Configuración de Expo presente${NC}"
else
    echo -e "${RED}⚠️ Falta archivo app.json${NC}"
fi

# Resumen final
echo -e "\n${BLUE}📋 RESUMEN DE INSTALACIÓN${NC}"
echo -e "${BLUE}======================${NC}"
echo -e "${GREEN}✅ Sistema actualizado${NC}"
echo -e "${GREEN}✅ Node.js $(node --version) instalado${NC}"
echo -e "${GREEN}✅ AWS CLI $(aws --version) instalado${NC}"
echo -e "${GREEN}✅ Amplify CLI $(amplify --version) instalado${NC}"
echo -e "${GREEN}✅ Expo CLI instalado${NC}"
echo -e "${GREEN}✅ Proyecto configurado${NC}"

echo -e "\n${YELLOW}🚀 PRÓXIMOS PASOS:${NC}"
echo -e "1. Verifica la configuración de autenticación social"
echo -e "2. Actualiza las variables de entorno en .env"
echo -e "3. Ejecuta ${BLUE}npx expo start${NC} para iniciar la app"

echo -e "\n${BLUE}📝 COMANDOS ÚTILES:${NC}"
echo -e "- ${YELLOW}amplify status${NC} - Ver estado del backend"
echo -e "- ${YELLOW}amplify push${NC} - Actualizar backend"
echo -e "- ${YELLOW}npx expo start${NC} - Iniciar la app"
echo -e "- ${YELLOW}yarn test${NC} - Ejecutar pruebas"

# Guardar log
exec 1> >(tee -a "/tmp/setup-$(date +%Y%m%d-%H%M%S).log")