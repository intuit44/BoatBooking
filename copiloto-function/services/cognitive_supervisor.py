# -*- coding: utf-8 -*-
"""
Supervisor Cognitivo - Analiza memoria, detecta patrones y genera conocimiento
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from services.semantic_memory import obtener_estado_sistema
from services.cosmos_store import CosmosMemoryStore

class CognitiveSupervisor:
    def __init__(self):
        self.cosmos = CosmosMemoryStore()
    
    def analyze_and_learn(self, horas_analisis: int = 24) -> Dict[str, Any]:
        """Analiza memoria completa y genera conocimiento"""
        try:
            # 1. Obtener estado actual
            estado_resultado = obtener_estado_sistema(horas_analisis)
            if not estado_resultado.get("exito"):
                return {"exito": False, "error": "No se pudo obtener estado"}
            
            estado = estado_resultado["estado"]
            
            # 2. Análisis cognitivo
            analisis = self._analyze_patterns(estado)
            
            # 3. Generar conocimiento
            conocimiento = self._generate_knowledge(analisis)
            
            # 4. Guardar snapshot
            snapshot_id = self._save_snapshot(conocimiento)
            
            return {
                "exito": True,
                "snapshot_id": snapshot_id,
                "conocimiento": conocimiento,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error en supervisor cognitivo: {e}")
            return {"exito": False, "error": str(e)}
    
    def _analyze_patterns(self, estado: Dict) -> Dict[str, Any]:
        """Detecta patrones en los datos"""
        total = estado.get("total_interacciones", 0)
        errores = len(estado.get("errores_recientes", []))
        
        return {
            "tasa_exito": (total - errores) / max(total, 1),
            "endpoints_criticos": self._identify_critical_endpoints(estado),
            "tendencias": self._detect_trends(estado),
            "problemas_recurrentes": self._find_recurring_issues(estado)
        }
    
    def _identify_critical_endpoints(self, estado: Dict) -> List[str]:
        """Identifica endpoints críticos por uso"""
        endpoints = estado.get("endpoints_mas_usados", {})
        return sorted(endpoints.keys(), key=lambda x: endpoints[x], reverse=True)[:3]
    
    def _detect_trends(self, estado: Dict) -> Dict[str, Any]:
        """Detecta tendencias"""
        return {
            "subsistemas_estables": len(estado.get("subsistemas_activos", [])) > 3,
            "monitoreo_efectivo": estado.get("monitoreo_activo", False),
            "agentes_colaborando": len(estado.get("agentes_activos", [])) > 1
        }
    
    def _find_recurring_issues(self, estado: Dict) -> List[str]:
        """Encuentra problemas recurrentes"""
        errores = estado.get("errores_recientes", [])
        problemas = {}
        
        for error in errores:
            error_msg = error.get("error", "").lower()
            for palabra in ["timeout", "connection", "auth", "permission"]:
                if palabra in error_msg:
                    problemas[palabra] = problemas.get(palabra, 0) + 1
        
        return [k for k, v in problemas.items() if v > 1]
    
    def _generate_knowledge(self, analisis: Dict) -> Dict[str, Any]:
        """Genera conocimiento derivado"""
        conocimiento = {
            "evaluacion_sistema": "estable" if analisis["tasa_exito"] > 0.8 else "inestable",
            "recomendaciones": [],
            "aprendizajes": [],
            "metricas_clave": {
                "tasa_exito": analisis["tasa_exito"],
                "endpoints_criticos": len(analisis["endpoints_criticos"]),
                "problemas_activos": len(analisis["problemas_recurrentes"])
            }
        }
        
        # Generar recomendaciones
        if analisis["tasa_exito"] < 0.7:
            conocimiento["recomendaciones"].append("Revisar endpoints con mayor tasa de error")
        
        if analisis["problemas_recurrentes"]:
            conocimiento["recomendaciones"].append(f"Atender problemas recurrentes: {', '.join(analisis['problemas_recurrentes'])}")
        
        if analisis["tendencias"]["monitoreo_efectivo"]:
            conocimiento["aprendizajes"].append("Sistema de monitoreo funcionando correctamente")
        
        return conocimiento
    
    def _save_snapshot(self, conocimiento: Dict) -> str:
        """Guarda snapshot de conocimiento en Cosmos"""
        timestamp = datetime.utcnow()
        snapshot_id = f"estado_sistema_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        documento = {
            "id": snapshot_id,
            "tipo": "cognitive_snapshot",
            "timestamp": timestamp.isoformat(),
            "conocimiento": conocimiento,
            "version": "1.0"
        }
        
        if self.cosmos.container is None:
            logging.error("Cosmos container is not initialized")
            return f"error_container_none_{timestamp.strftime('%H%M%S')}"
        
        try:
            self.cosmos.container.upsert_item(documento)
            logging.info(f"Snapshot cognitivo guardado: {snapshot_id}")
            return snapshot_id
        except Exception as e:
            logging.error(f"Error guardando snapshot: {e}")
            return f"error_{timestamp.strftime('%H%M%S')}"
    
    def get_latest_knowledge(self) -> Dict[str, Any]:
        """Obtiene el conocimiento más reciente"""
        try:
            if self.cosmos.container is None:
                logging.error("Cosmos container is not initialized")
                return {"exito": False, "error": "Cosmos container is not initialized"}
            
            query = """
            SELECT TOP 1 * FROM c 
            WHERE c.tipo = 'cognitive_snapshot' 
            ORDER BY c.timestamp DESC
            """
            
            items = list(self.cosmos.container.query_items(query, enable_cross_partition_query=True))
            
            if items:
                return {"exito": True, "conocimiento": items[0]["conocimiento"]}
            else:
                return {"exito": False, "error": "No hay snapshots disponibles"}
                
        except Exception as e:
            logging.error(f"Error obteniendo conocimiento: {e}")
            return {"exito": False, "error": str(e)}