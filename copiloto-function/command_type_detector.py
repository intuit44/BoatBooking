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
        # Patrones de detección dinámicos (mantener para compatibilidad, pero usar lógica estructural)
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
        Detecta el tipo de comando usando lógica estructural dinámica
        """
        if not command or not command.strip():
            return {
                "type": "unknown",
                "confidence": 0.0,
                "original_command": command,
                "normalized_command": command,
                "needs_prefix": False
            }
        
        # NO normalizar - mantener comando original
        normalized_command = command
        
        # Determinar tipo basado en el comando normalizado
        cmd_type = "generic"
        confidence = 0.5  # Confianza base para detección estructural
        
        if normalized_command.startswith("az "):
            cmd_type = "azure_cli"
            confidence = 0.9
        elif any(normalized_command.lower().startswith(p) for p in ["python ", "pip ", "conda ", "poetry "]):
            cmd_type = "python"
            confidence = 0.8
        elif any(normalized_command.lower().startswith(p) for p in ["powershell ", "pwsh ", "Get-", "Set-", "New-", "Remove-"]):
            cmd_type = "powershell"
            confidence = 0.8
        elif any(normalized_command.lower().startswith(p) for p in ["bash ", "sh ", "chmod ", "ls ", "cd ", "mkdir ", "rm "]):
            cmd_type = "bash"
            confidence = 0.8
        elif any(normalized_command.lower().startswith(p) for p in ["npm ", "yarn ", "pnpm "]):
            cmd_type = "npm"
            confidence = 0.8
        elif any(normalized_command.lower().startswith(p) for p in ["docker ", "docker-compose "]):
            cmd_type = "docker"
            confidence = 0.8
        
        return {
            "type": cmd_type,
            "confidence": confidence,
            "original_command": command,
            "normalized_command": normalized_command,
            "needs_prefix": normalized_command != command,
            "detected_patterns": []  # Simplificado, ya no usado
        }
    
    def _detect_and_prefix_command(self, command: str) -> str:
        """
        Decide dinámicamente si anteponer 'az' al comando.
        Usa señales estructurales, no predefiniciones.
        """
        cmd = command.strip()
        cmd_lower = cmd.lower()
        
        # 1️⃣ Si ya comienza con un ejecutable conocido, no tocar
        # (Tiene extensión .exe, .cmd, o ruta absoluta)
        if re.match(r'^[A-Za-z]:|^\.', cmd_lower):
            return cmd  # ejecutable local o script

        # 2️⃣ Si empieza con az o azure → ya es CLI de Azure
        if cmd_lower.startswith(("az ", "azure ")):
            return cmd

        # 3️⃣ Si el primer token parece un binario de herramienta externa
        # detecta automáticamente por patrón (palabra sin 'az' y sin subcomandos)
        first = cmd_lower.split(" ")[0]
        if re.match(r'^(func|docker|bash|sh|pwsh|powershell|python|pip|npm|yarn|node|git)$', first):
            return cmd  # herramientas externas → no agregar 'az'

        # 4️⃣ Si contiene subcomandos tipo 'webapp', 'functionapp', 'group', etc. → Azure CLI
        # En vez de lista fija, usa patrón por contexto (verbo + nombre de recurso)
        if re.search(r'\b(functionapp|webapp|storage|group|vm|account|cosmos|acr|resource|monitor)\b', cmd_lower):
            if not cmd_lower.startswith("az "):
                return f"az {cmd}"
        
        # 5️⃣ Si contiene opciones típicas del CLI de Azure → agregar az
        if re.search(r'--resource-group|--subscription|--output', cmd_lower):
            if not cmd_lower.startswith("az "):
                return f"az {cmd}"

        # 6️⃣ En cualquier otro caso, dejarlo limpio
        return cmd
    
    def _calculate_match_score(self, command: str, patterns: Dict) -> float:
        """Calcula score de coincidencia para un tipo de comando (mantener para compatibilidad)"""
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
        """Obtiene los patrones que coincidieron (mantener para compatibilidad)"""
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