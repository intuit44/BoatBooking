"""
🔍 Validador de Contexto Semántico
Evita redundancia, contradicción e incoherencia antes de enviar al modelo
"""

import logging
from typing import Dict, List, Any, Set, Tuple
from datetime import datetime, timedelta
import hashlib

class ContextValidator:
    """Validador que limpia y optimiza el contexto antes del modelo"""
    
    def __init__(self):
        self.similarity_threshold = 0.8  # Umbral para detectar duplicados
        self.max_context_age_hours = 24  # Máximo 24 horas de contexto
        self.max_tokens_estimate = 8000  # Estimación máxima de tokens (aumentado para más contexto)
        
    def validate_and_clean_context(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida y limpia el contexto completo antes de enviarlo al modelo"""
        
        if not context_data.get("interacciones_recientes"):
            return context_data
        
        interacciones = context_data["interacciones_recientes"]
        
        # 1. Filtrar por edad
        filtered_by_age = self._filter_by_age(interacciones)
        
        # 2. Eliminar duplicados semánticos
        deduplicated = self._remove_semantic_duplicates(filtered_by_age)
        
        # 3. Resolver contradicciones
        resolved = self._resolve_contradictions(deduplicated)
        
        # 4. Optimizar por tokens
        optimized = self._optimize_for_tokens(resolved)
        
        # 5. Generar resumen final limpio
        clean_summary = self._generate_clean_summary(optimized)
        
        # Actualizar el contexto
        context_data["interacciones_recientes"] = optimized
        context_data["resumen_conversacion"] = clean_summary
        context_data["validation_applied"] = True
        context_data["validation_stats"] = {
            "original_count": len(interacciones),
            "filtered_by_age": len(filtered_by_age),
            "after_deduplication": len(deduplicated),
            "after_contradiction_resolution": len(resolved),
            "final_optimized": len(optimized)
        }
        
        logging.info(f"🔍 Contexto validado: {len(interacciones)} → {len(optimized)} interacciones")
        
        return context_data
    
    def _filter_by_age(self, interacciones: List[Dict]) -> List[Dict]:
        """Filtra interacciones por edad máxima"""
        
        cutoff_time = datetime.now() - timedelta(hours=self.max_context_age_hours)
        filtered = []
        
        for interaccion in interacciones:
            try:
                timestamp_str = interaccion.get("timestamp", "")
                if timestamp_str:
                    # Parsear timestamp
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if timestamp.replace(tzinfo=None) > cutoff_time:
                        filtered.append(interaccion)
                else:
                    # Si no hay timestamp, incluir (asumir reciente)
                    filtered.append(interaccion)
            except Exception as e:
                # En caso de error, incluir la interacción
                filtered.append(interaccion)
                logging.warning(f"Error parseando timestamp: {e}")
        
        return filtered
    
    def _remove_semantic_duplicates(self, interacciones: List[Dict]) -> List[Dict]:
        """Elimina duplicados semánticos basados en contenido"""
        
        seen_hashes = set()
        unique_interactions = []
        
        for interaccion in interacciones:
            # Crear hash semántico
            semantic_content = f"{interaccion.get('endpoint', '')}{interaccion.get('texto_semantico', '')}"
            content_hash = hashlib.md5(semantic_content.encode()).hexdigest()
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_interactions.append(interaccion)
        
        return unique_interactions
    
    def _resolve_contradictions(self, interacciones: List[Dict]) -> List[Dict]:
        """Resuelve contradicciones manteniendo la información más reciente"""
        
        # Agrupar por endpoint para detectar contradicciones
        endpoint_groups = {}
        for interaccion in interacciones:
            endpoint = interaccion.get("endpoint", "unknown")
            if endpoint not in endpoint_groups:
                endpoint_groups[endpoint] = []
            endpoint_groups[endpoint].append(interaccion)
        
        resolved = []
        
        for endpoint, group in endpoint_groups.items():
            if len(group) == 1:
                # Sin contradicciones posibles
                resolved.extend(group)
            else:
                # Detectar contradicciones por éxito/fallo
                success_interactions = [i for i in group if i.get("exito", True)]
                failed_interactions = [i for i in group if not i.get("exito", True)]
                
                if success_interactions and failed_interactions:
                    # Hay contradicción: mantener la más reciente de cada tipo
                    # Ordenar por timestamp (más reciente primero)
                    success_sorted = sorted(success_interactions, 
                                          key=lambda x: x.get("timestamp", ""), reverse=True)
                    failed_sorted = sorted(failed_interactions, 
                                         key=lambda x: x.get("timestamp", ""), reverse=True)
                    
                    # Mantener la más reciente de cada tipo
                    resolved.append(success_sorted[0])
                    if failed_sorted:
                        resolved.append(failed_sorted[0])
                else:
                    # Sin contradicciones: mantener las 5 más recientes para más contexto
                    sorted_group = sorted(group, key=lambda x: x.get("timestamp", ""), reverse=True)
                    resolved.extend(sorted_group[:5])
        
        return resolved
    
    def _optimize_for_tokens(self, interacciones: List[Dict]) -> List[Dict]:
        """Optimiza el contexto para no exceder límites de tokens"""
        
        # Estimación simple: ~100 caracteres = 25 tokens
        current_chars = sum(len(str(i.get("texto_semantico", ""))) for i in interacciones)
        estimated_tokens = current_chars // 4  # Estimación conservadora
        
        if estimated_tokens <= self.max_tokens_estimate:
            return interacciones
        
        # Priorizar por relevancia y recencia
        scored_interactions = []
        for i, interaccion in enumerate(interacciones):
            score = self._calculate_relevance_score(interaccion, i)
            scored_interactions.append((score, interaccion))
        
        # Ordenar por score y tomar los mejores
        scored_interactions.sort(key=lambda x: x[0], reverse=True)
        
        optimized = []
        current_tokens = 0
        
        for score, interaccion in scored_interactions:
            interaction_tokens = len(str(interaccion.get("texto_semantico", ""))) // 4
            if current_tokens + interaction_tokens <= self.max_tokens_estimate:
                optimized.append(interaccion)
                current_tokens += interaction_tokens
            else:
                break
        
        # Reordenar por timestamp (más reciente primero)
        optimized.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return optimized
    
    def _calculate_relevance_score(self, interaccion: Dict, position: int) -> float:
        """Calcula score de relevancia para priorización"""
        
        score = 0.0
        
        # Score por recencia (posición en la lista)
        recency_score = 1.0 / (position + 1)
        score += recency_score * 0.4
        
        # Score por éxito/fallo
        if not interaccion.get("exito", True):
            score += 0.3  # Errores son más relevantes
        
        # Score por tipo de endpoint
        endpoint = interaccion.get("endpoint", "")
        if any(keyword in endpoint for keyword in ["error", "fail", "exception"]):
            score += 0.2
        elif any(keyword in endpoint for keyword in ["execute", "run", "command"]):
            score += 0.15
        
        # Score por contenido semántico
        texto = interaccion.get("texto_semantico", "").lower()
        if any(keyword in texto for keyword in ["error", "fail", "exception", "timeout"]):
            score += 0.15
        
        return score
    
    def _generate_clean_summary(self, interacciones: List[Dict]) -> str:
        """Genera un resumen limpio y conciso"""
        
        if not interacciones:
            return "Sin contexto relevante disponible"
        
        # Analizar patrones principales usando más interacciones
        endpoints = [i.get("endpoint", "") for i in interacciones[:10]]  # Analizar más endpoints
        success_count = sum(1 for i in interacciones if i.get("exito", True))
        total_count = len(interacciones)
        
        # Identificar endpoints más frecuentes
        from collections import Counter
        endpoint_counts = Counter(endpoints)
        top_endpoints = [ep for ep, count in endpoint_counts.most_common(3) if ep and ep != 'unknown']
        
        # Detectar patrón principal
        if total_count <= 3:
            pattern = "Actividad reciente"
        elif success_count / total_count > 0.8:
            pattern = "Sesión estable"
        elif success_count / total_count < 0.5:
            pattern = "Sesión con errores"
        else:
            pattern = "Sesión mixta"
        
        # Último endpoint significativo
        last_endpoint = endpoints[0] if endpoints else "unknown"
        
        # Agregar información de endpoints frecuentes si hay suficientes interacciones
        if total_count > 5 and top_endpoints:
            endpoints_info = f" | Endpoints frecuentes: {', '.join(top_endpoints[:2])}"
        else:
            endpoints_info = ""
        
        return f"{pattern}: {total_count} interacciones. Última acción: {last_endpoint} ({'✅' if interacciones[0].get('exito', True) else '❌'}){endpoints_info}"

# Instancia global
context_validator = ContextValidator()

def validate_context_before_model(context_data: Dict[str, Any]) -> Dict[str, Any]:
    """Función principal para validar contexto antes del modelo"""
    return context_validator.validate_and_clean_context(context_data)