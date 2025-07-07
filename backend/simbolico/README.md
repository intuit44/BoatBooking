# 🧠 Sistema Simbólico - Servidor de Ejecución para Agentes CodeGPT

Sistema de ejecución que permite a los agentes de CodeGPT (tanto de la extensión VS Code como de la web) ejecutar acciones concretas en el sistema de archivos local a través de un servidor Flask.

## 🎯 Propósito

Este sistema actúa como puente entre:
- **Agentes CodeGPT** (que solo pueden generar instrucciones)
- **Sistema Local** (donde se ejecutan las acciones reales)

Permite que el Architect Agent y otros agentes especializados puedan:
- ✅ Crear y modificar archivos
- ✅ Registrar funciones en serverless.yml
- ✅ Crear tablas DynamoDB
- ✅ Ejecutar comandos del sistema
- ✅ Desplegar a AWS

## 📁 Estructura

boat-rental-app/backend/simbolico/
├── simbolo_gpt4_api.py      # Servidor Flask principal
├── ejecutor_sistemico.py    # Motor de ejecución de acciones
├── requirements.txt         # Dependencias Python
├── logs/                    # Logs de ejecución
└── README.md               # Este archivo

## 🚀 Instalación

### 1. Instalar dependencias

```bash
cd boat-rental-app/backend/simbolico
pip install -r requirements.txt

2. Iniciar el servidor

python simbolo_gpt4_api.py

El servidor estará disponible en http://localhost:5000
📡 Endpoints
POST /simbolo
Endpoint principal para ejecutar acciones simbólicas.
Request:

{
  "agente": "dynamodb_creator",
  "accion": "crear_tabla",
  "parametros": {
    "tabla": "UsersTable",
    "indices": ["email"],
    "archivo": "backend/serverless.yml"
  }
}

Response:
{
  "estado": "ok",
  "detalle": {
    "mensaje": "Tabla UsersTable creada exitosamente",
    "archivo_modificado": "backend/serverless.yml",
    "variable_entorno": "DYNAMODB_TABLE_USERS"
  }
}

GET /agentes
Lista todos los agentes disponibles y sus capacidades.
GET /health
Verifica el estado del servidor.
🤖 Agentes Disponibles
1. dynamodb_creator
Gestiona tablas DynamoDB en serverless.yml

crear_tabla: Crea nueva tabla con índices
agregar_indices: Agrega índices a tabla existente
configurar_iam: Configura permisos DynamoDB

2. function_registrar
Registra funciones Lambda en serverless.yml

registrar_funcion: Registra una función
registrar_multiples: Registra varias funciones
eliminar_funcion: Elimina una función

3. code_generator
Genera código para handlers y utilidades

crear_handler: Crea handler Lambda
crear_util: Crea archivos de utilidades
fix_sintaxis: Corrige errores de sintaxis
generar_test: Genera archivos de test

4. file_manager
Gestiona archivos del proyecto

leer_archivo: Lee contenido
escribir_archivo: Escribe/modifica archivos
crear_directorio: Crea directorios
listar_archivos: Lista archivos con patrones

5. serverless_deployer
Gestiona deployments de Serverless

deploy: Despliega a AWS
remove: Elimina stack
logs: Obtiene logs de funciones
info: Información del stack

💻 Uso desde CodeGPT
1. En CodeGPT Web (Architect Agent)
El agente genera instrucciones JSON que debes copiar y ejecutar:

// Ejemplo de instrucción generada por el Architect
{
  "agente": "function_registrar",
  "accion": "registrar_funcion",
  "parametros": {
    "funcion": "getBoats",
    "handler": "src/handlers/boats.getBoats",
    "metodo": "get",
    "path": "boats"
  }
}

2. Ejecutar con Cliente JavaScript

// client-executor.js
const axios = require('axios');

async function ejecutar(instruccion) {
  try {
    const response = await axios.post('http://localhost:5000/simbolo', instruccion);
    console.log('✅', response.data);
  } catch (error) {
    console.error('❌', error.message);
  }
}

// Pega aquí la instrucción del Architect
const instruccion = {
  "agente": "dynamodb_creator",
  "accion": "crear_tabla",
  "parametros": {
    "tabla": "UsersTable",
    "indices": ["email"]
  }
};

3. Ejecutar con cURL

curl -X POST http://localhost:5000/simbolo \
  -H "Content-Type: application/json" \
  -d '{
    "agente": "function_registrar",
    "accion": "registrar_funcion",
    "parametros": {
      "funcion": "createBooking",
      "handler": "src/handlers/bookings.createBooking",
      "metodo": "post",
      "path": "bookings",
      "autorizacion": true
    }
  }'

  🔄 Flujo de Trabajo Completo

  graph LR
    A[CodeGPT Web/VS Code] -->|Genera Instrucción| B[Usuario]
    B -->|Copia y Ejecuta| C[Cliente HTTP]
    C -->|POST /simbolo| D[Servidor Simbólico]
    D -->|Procesa| E[Ejecutor Sistémico]
    E -->|Modifica| F[Archivos Locales]
    F -->|Git Push| G[GitHub]
    G -->|CI/CD| H[AWS]

🛡️ Seguridad
⚠️ IMPORTANTE: Este servidor está diseñado para desarrollo local.
NO expongas el puerto 5000 a internet ya que permite modificación de archivos.
Para producción, considera:

Autenticación con tokens
HTTPS
Restricción de IPs
Logs de auditoría

🐛 Troubleshooting
Error: "Connection refused"

# Verificar que el servidor esté corriendo
ps aux | grep simbolo_gpt4_api
# O en Windows
tasklist | findstr python

Error: "Module not found"

# Reinstalar dependencias
pip install -r requirements.txt

Error: "Permission denied"

# En Linux/Mac, dar permisos
chmod +x simbolo_gpt4_api.py
# O ejecutar con sudo (no recomendado)

📊 Logs
Los logs se guardan en:

Consola: Información en tiempo real
logs/simbolico.log: Historial completo (si está configurado)

🔗 Integración con el Proyecto
Este sistema es parte integral del proyecto Boat Rental App y trabaja en conjunto con:

Architect Agent: Analiza y genera instrucciones
Backend: Donde se aplican los cambios
CI/CD: Despliega los cambios a AWS

📚 Ejemplos Avanzados
Crear tabla con configuración completa

{
  "agente": "dynamodb_creator",
  "accion": "crear_tabla",
  "parametros": {
    "tabla": "BookingsTable",
    "indices": ["userId", "boatId", "date"],
    "archivo": "backend/serverless.yml",
    "configurar_iam": true
  }
}

Registrar múltiples funciones

{
  "agente": "function_registrar",
  "accion": "registrar_multiples",
  "parametros": {
    "funciones": [
      {
        "funcion": "getBoats",
        "handler": "src/handlers/boats.getBoats",
        "metodo": "get",
        "path": "boats"
      },
      {
        "funcion": "createBoat",
        "handler": "src/handlers/boats.createBoat",
        "metodo": "post",
        "path": "boats",
        "autorizacion": true
      }
    ]
  }
}

Deploy a producción

{
  "agente": "serverless_deployer",
  "accion": "deploy",
  "parametros": {
    "stage": "prod",
    "region": "us-east-1"
  }
}

🤝 Contribuir
Para agregar nuevos agentes o capacidades:

Edita simbolo_gpt4_api.py
Agrega el agente en el diccionario AGENTES
Implementa las funciones correspondientes
Actualiza este README
Prueba exhaustivamente

📞 Soporte
Si encuentras problemas:

Revisa los logs del servidor
Verifica la estructura de tu instrucción JSON
Asegúrate de que los paths sean correctos
Consulta la documentación del agente específico

### 📄 **requirements.txt**

```txt
flask==3.0.0
flask-cors==4.0.0
pyyaml==6.0.1
pathlib==1.0.1
requests==2.31.0



