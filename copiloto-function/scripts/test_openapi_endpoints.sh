#!/bin/bash

# Archivo OpenAPI local
OPENAPI_FILE='openapi.yaml'

# Leer los endpoints del archivo OpenAPI y probar cada uno
endpoints=$(yq eval '.paths | keys | .[]' $OPENAPI_FILE)

# Probar cada endpoint
for endpoint in $endpoints; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000$endpoint")
    if [ "$response" -eq 200 ]; then
        echo "$endpoint: OK"
    else
        echo "$endpoint: FAIL (HTTP $response)"
    fi
done
