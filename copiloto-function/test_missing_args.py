#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple para verificar la detección de argumentos faltantes
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

# Simular la función _detectar_argumento_faltante
def _detectar_argumento_faltante(comando: str, error_msg: str):
    """
    Detecta argumentos faltantes en comandos Azure CLI y sugiere soluciones.
    """
    try:
        error_lower = error_msg.lower()
        comando_lower = comando.lower()
        
        # Patrones de detección de argumentos faltantes
        missing_patterns = {
            "--resource-group": {
                "patterns": ["resource group", "--resource-group", "-g", "resource-group is required"],
                "argumento": "--resource-group",
                "descripcion": "Este comando requiere especificar el grupo de recursos",
                "comando_listar": "az group list --output table",
                "sugerencia": "¿Quieres que liste los grupos de recursos disponibles?",
                "valores_comunes": ["boat-rental-app-group", "boat-rental-rg", "DefaultResourceGroup-EUS2"]
            },
            "--account-name": {
                "patterns": ["account name", "--account-name", "storage account", "account-name is required"],
                "argumento": "--account-name",
                "descripcion": "Este comando requiere el nombre de la cuenta de almacenamiento",
                "comando_listar": "az storage account list --output table",
                "sugerencia": "¿Quieres que liste las cuentas de almacenamiento disponibles?",
                "valores_comunes": ["boatrentalstorage", "copilotostorage"]
            }
        }
        
        # Buscar patrones en el mensaje de error
        for arg_name, info in missing_patterns.items():
            for pattern in info["patterns"]:
                if pattern in error_lower:
                    # Verificar que el argumento no esté ya en el comando
                    if arg_name not in comando_lower:
                        print(f"Argumento faltante detectado: {arg_name}")
                        return info
        
        # Detección específica para Cosmos DB
        if "cosmosdb" in comando_lower and any(pattern in error_lower for pattern in ["account-name", "account name"]):
            return {
                "argumento": "--account-name",
                "descripcion": "Este comando de Cosmos DB requiere el nombre de la cuenta",
                "comando_listar": "az cosmosdb list --output table",
                "sugerencia": "¿Quieres que liste las cuentas de Cosmos DB disponibles?",
                "valores_comunes": ["copiloto-cosmos", "boat-rental-cosmos"]
            }
        
        return None
        
    except Exception as e:
        print(f"Error detectando argumento faltante: {e}")
        return None

def test_casos():
    """Probar diferentes casos de argumentos faltantes"""
    
    casos_test = [
        {
            "comando": "az cosmosdb sql database list --account-name copiloto-cosmos --output json",
            "error": "argument --resource-group/-g: expected one argument",
            "esperado": "--resource-group"
        },
        {
            "comando": "az storage account list",
            "error": "Storage account name is required",
            "esperado": "--account-name"
        },
        {
            "comando": "az functionapp list",
            "error": "Resource group is required for this operation",
            "esperado": "--resource-group"
        },
        {
            "comando": "az cosmosdb list",
            "error": "Account name is required",
            "esperado": "--account-name"
        }
    ]
    
    print("Ejecutando tests de detección de argumentos faltantes...\n")
    
    for i, caso in enumerate(casos_test, 1):
        print(f"Test {i}: {caso['comando']}")
        print(f"Error: {caso['error']}")
        
        resultado = _detectar_argumento_faltante(caso["comando"], caso["error"])
        
        if resultado:
            print(f"Detectado: {resultado['argumento']}")
            print(f"   Descripción: {resultado['descripcion']}")
            print(f"   Sugerencia: {resultado['sugerencia']}")
            print(f"   Comando para listar: {resultado.get('comando_listar', 'N/A')}")
            
            if resultado["argumento"] == caso["esperado"]:
                print("CORRECTO - Argumento detectado correctamente")
            else:
                print(f"ERROR - Esperado: {caso['esperado']}, Detectado: {resultado['argumento']}")
        else:
            print("No se detectó argumento faltante")
        
        print("-" * 60)

if __name__ == "__main__":
    test_casos()