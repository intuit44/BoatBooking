#!/bin/bash

# 🧪 Script de Test Rápido - Integración de Queries Dinámicas
# Ejecutar: bash TEST_RAPIDO.sh

echo "🧪 Iniciando tests de integración de queries dinámicas..."
echo ""

BASE_URL="http://localhost:7071/api"
SESSION_ID="test_session_$(date +%s)"

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para test
test_endpoint() {
    local name=$1
    local url=$2
    local method=${3:-GET}
    local data=$4
    
    echo -e "${YELLOW}Testing: $name${NC}"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL/$url" \
            -H "Session-ID: $SESSION_ID")
    else
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/$url" \
            -H "Content-Type: application/json" \
            -H "Session-ID: $SESSION_ID" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        exito=$(echo "$body" | jq -r '.exito // .ok // true')
        if [ "$exito" = "true" ]; then
            echo -e "${GREEN}✅ PASS${NC} - HTTP $http_code"
        else
            echo -e "${RED}❌ FAIL${NC} - HTTP $http_code (exito=false)"
        fi
    else
        echo -e "${RED}❌ FAIL${NC} - HTTP $http_code"
    fi
    
    echo ""
}

# Test 1: /api/copiloto con query dinámica básica
test_endpoint \
    "Copiloto - Query dinámica básica" \
    "copiloto?tipo=error&limite=5"

# Test 2: /api/copiloto con múltiples filtros
test_endpoint \
    "Copiloto - Múltiples filtros" \
    "copiloto?tipo=error&fecha_inicio=2025-01-05&limite=10"

# Test 3: /api/copiloto con búsqueda de texto
test_endpoint \
    "Copiloto - Búsqueda de texto" \
    "copiloto" \
    "POST" \
    '{"contiene": "cosmos", "limite": 10}'

# Test 4: /api/sugerencias
test_endpoint \
    "Sugerencias - Básico" \
    "sugerencias?limite=5"

# Test 5: /api/contexto-inteligente
test_endpoint \
    "Contexto Inteligente - Básico" \
    "contexto-inteligente"

# Test 6: /api/memoria-global
test_endpoint \
    "Memoria Global - Básico" \
    "memoria-global?limite=20"

# Test 7: /api/diagnostico
test_endpoint \
    "Diagnóstico - Por sesión" \
    "diagnostico?session_id=$SESSION_ID"

# Test 8: /api/buscar-interacciones
test_endpoint \
    "Buscar Interacciones - Básico" \
    "buscar-interacciones?limite=10"

# Test 9: /api/msearch
test_endpoint \
    "MSearch - Búsqueda semántica" \
    "msearch" \
    "POST" \
    '{"query": "errores recientes", "limit": 5}'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Tests completados!"
echo ""
echo "📊 Resumen:"
echo "  - Session ID usado: $SESSION_ID"
echo "  - Base URL: $BASE_URL"
echo ""
echo "💡 Para ver logs detallados:"
echo "  tail -f /var/log/azure-functions/copiloto-function.log"
echo ""
echo "📚 Documentación:"
echo "  - INTEGRACION_QUERIES_DINAMICAS.md"
echo "  - RESUMEN_INTEGRACION.md"
echo "  - VERIFICACION_FINAL.md"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
