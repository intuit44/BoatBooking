#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detector dinámico de tipo de comando - Sin predefiniciones
Detecta automáticamente si es Azure CLI, PowerShell, Bash, Python, etc.
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple

class CommandTypeDetector:
    """Detector inteligente de tipo de comando sin predefiniciones"""
    
    def __init__(self):
        # Patrones de detección dinámicos
        self.command_patterns = {
            "azure_cli": {
                "prefixes": ["az ", "azure "],
                "keywords": ["cosmosdb", "storage account", "functionapp", "webapp", "group", "resource"],
                "indicators": ["--output", "--resource-group", "--subscription"]
            },
            "python": {
                "prefixes": ["python ", "pip ", "conda ", "poetry "],
                "keywords": ["install", "uninstall", "upgrade", "freeze", "list"],
                "indicators": ["requirements.txt", "__pycache__", ".py"]
            },
            "powershell": {
                "prefixes": ["powershell ", "pwsh ", "Get-", "Set-", "New-", "Remove-"],
                "keywords": ["cmdlet", "module", "script"],
                "indicators": ["-Force", "-Confirm", "-WhatIf", ".ps1"]
            },
            "bash": {
                "prefixes": ["bash ", "sh ", "chmod ", "ls ", "cd ", "mkdir ", "rm "],
                "keywords": ["grep", "awk", "sed", "find"],
                "indicators": ["&&", "||", "|", "./", "../"]
            },
            "npm": {
                "prefixes": ["npm ", "yarn ", "pnpm "],
                "keywords": ["install", "uninstall", "update", "run", "build"],
                "indicators": ["package.json", "node_modules", "--save"]
            },
            "docker": {
                "prefixes": ["docker ", "docker-compose "],
                "keywords": ["build", "run", "pull", "push", "exec"],
                "indicators": ["Dockerfile", "-d", "--rm", "-it"]
            }
        }
    
    def detect_command_type(self, command: str) -> Dict[str, Any]:
        """
        Detecta el tipo de comando dinámicamente
        """
        if not command or not command.strip():
            return {
                "type": "unknown",
                "confidence": 0.0,
                "original_command": command,
                "normalized_command": command,
                "needs_prefix": False
            }
        
        command_lower = command.lower().strip()
        best_match = None
        best_score = 0.0
        
        # Evaluar cada tipo de comando
        for cmd_type, patterns in self.command_patterns.items():
            score = self._calculate_match_score(command_lower, patterns)
            
            if score > best_score:
                best_score = score
                best_match = cmd_type
        
        # Determinar si necesita prefijo
        needs_prefix = False
        normalized_command = command.strip()
        
        if best_match == "azure_cli" and not command_lower.startswith("az "):
            needs_prefix = True
            normalized_command = f"az {command.strip()}"
        elif best_match == "python" and command_lower.startswith("pip "):
            # pip es comando directo, no necesita prefijo
            needs_prefix = False
        elif best_match == "powershell" and not any(command_lower.startswith(p) for p in ["powershell ", "pwsh "]):
            # Solo agregar prefijo si no es un cmdlet nativo
            if not any(command_lower.startswith(p.lower()) for p in ["get-", "set-", "new-", "remove-"]):
                needs_prefix = True
                normalized_command = f"powershell {command.strip()}"
        
        return {
            "type": best_match or "generic",
            "confidence": best_score,
            "original_command": command,
            "normalized_command": normalized_command,
            "needs_prefix": needs_prefix,
            "detected_patterns": self._get_matched_patterns(command_lower, best_match) if best_match else []
        }
    
    def _calculate_match_score(self, command: str, patterns: Dict) -> float:
        """Calcula score de coincidencia para un tipo de comando"""
        score = 0.0
        
        # Verificar prefijos (peso alto)
        for prefix in patterns.get("prefixes", []):
            if command.startswith(prefix.lower()):
                score += 0.8
                break
        
        # Verificar palabras clave (peso medio)
        keywords_found = 0
        for keyword in patterns.get("keywords", []):
            if keyword.lower() in command:
                keywords_found += 1
        
        if keywords_found > 0:
            score += min(0.5, keywords_found * 0.1)
        
        # Verificar indicadores (peso bajo)
        indicators_found = 0
        for indicator in patterns.get("indicators", []):
            if indicator.lower() in command:
                indicators_found += 1
        
        if indicators_found > 0:
            score += min(0.3, indicators_found * 0.05)
        
        return min(1.0, score)
    
    def _get_matched_patterns(self, command: str, cmd_type: str) -> list:
        """Obtiene los patrones que coincidieron"""
        if not cmd_type or cmd_type not in self.command_patterns:
            return []
        
        patterns = self.command_patterns[cmd_type]
        matched = []
        
        for prefix in patterns.get("prefixes", []):
            if command.startswith(prefix.lower()):
                matched.append(f"prefix: {prefix}")
        
        for keyword in patterns.get("keywords", []):
            if keyword.lower() in command:
                matched.append(f"keyword: {keyword}")
        
        for indicator in patterns.get("indicators", []):
            if indicator.lower() in command:
                matched.append(f"indicator: {indicator}")
        
        return matched

# Instancia global del detector
command_detector = CommandTypeDetector()

def detect_and_normalize_command(command: str) -> Dict[str, Any]:
    """
    Función principal para detectar y normalizar comandos
    """
    try:
        detection = command_detector.detect_command_type(command)
        
        logging.info(f"Comando detectado: {detection['type']} (confianza: {detection['confidence']:.3f})")
        logging.info(f"Comando normalizado: {detection['normalized_command']}")
        
        return detection
        
    except Exception as e:
        logging.error(f"Error en detección de comando: {e}")
        
        # Fallback seguro - no modificar el comando
        return {
            "type": "generic",
            "confidence": 0.0,
            "original_command": command,
            "normalized_command": command,
            "needs_prefix": False,
            "error": str(e)
        }

def is_azure_cli_command(command: str) -> bool:
    """Verifica si un comando es específicamente de Azure CLI"""
    detection = detect_and_normalize_command(command)
    return detection.get("type") == "azure_cli" and detection.get("confidence", 0) > 0.5

def should_add_az_prefix(command: str) -> bool:
    """Determina si se debe agregar el prefijo 'az' al comando"""
    detection = detect_and_normalize_command(command)
    return (
        detection.get("type") == "azure_cli" and 
        detection.get("needs_prefix", False) and
        detection.get("confidence", 0) > 0.5
    )