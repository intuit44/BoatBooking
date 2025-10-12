#!/usr/bin/env python3
"""
Validador OpenAPI para aplicar-correccion-manual
"""
import yaml
import json

def validate_openapi_schema():
    """Valida que el schema OpenAPI esté bien formado"""
    try:
        with open('openapi.yaml', 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        # Verificar que existe el endpoint
        endpoint = schema['paths'].get('/api/aplicar-correccion-manual')
        if not endpoint:
            return False, "Endpoint no encontrado en OpenAPI"
        
        # Verificar método POST
        post_method = endpoint.get('post')
        if not post_method:
            return False, "Método POST no encontrado"
        
        # Verificar requestBody
        request_body = post_method.get('requestBody')
        if not request_body:
            return False, "requestBody no encontrado"
        
        # Verificar schema properties
        schema_props = request_body['content']['application/json']['schema']['properties']
        expected_props = ['timeout', 'database', 'comando', 'ruta', 'contenido', 'configuracion']
        
        found_props = list(schema_props.keys())
        missing = [prop for prop in expected_props if prop not in found_props]
        
        if missing:
            return False, f"Propiedades faltantes: {missing}"
        
        # Verificar responses
        responses = post_method.get('responses', {})
        if '200' not in responses:
            return False, "Response 200 no definida"
        
        return True, "Schema OpenAPI válido"
        
    except Exception as e:
        return False, f"Error validando schema: {str(e)}"

if __name__ == "__main__":
    valid, message = validate_openapi_schema()
    print(f"{'✅' if valid else '❌'} {message}")