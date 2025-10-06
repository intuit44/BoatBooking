# -*- coding: utf-8 -*-
"""
Logger estructurado para Application Insights con customDimensions
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

class AppInsightsLogger:
    def __init__(self):
        self.logger = logging.getLogger('cosmos_fixes')
        
    def log_fix_event(self, event_type: str, fix_id: str, run_id: str, 
                     estado: str, target: str, prioridad: int, 
                     additional_data: Optional[Dict[str, Any]] = None):
        """Log estructurado para eventos de fixes"""
        
        custom_dimensions = {
            'tipo': event_type,
            'fix_id': fix_id,
            'run_id': run_id,
            'estado': estado,
            'target': target,
            'prioridad': str(prioridad),
            'timestamp': datetime.now().isoformat()
        }
        
        if additional_data:
            custom_dimensions.update(additional_data)
        
        # Log con customDimensions para App Insights
        self.logger.info(
            f"Fix Event: {event_type}",
            extra={
                'custom_dimensions': custom_dimensions,
                'operation_Id': run_id
            }
        )
    
    def log_promotion_batch(self, run_id: str, promovidos: int, fallidos: int, 
                           fixes_procesados: List[str]):
        """Log de batch de promociones"""
        
        custom_dimensions = {
            'tipo': 'promocion_batch',
            'run_id': run_id,
            'promovidos_count': str(promovidos),
            'fallidos_count': str(fallidos),
            'fixes_procesados': json.dumps(fixes_procesados),
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(
            f"Promotion Batch: {promovidos} promoted, {fallidos} failed",
            extra={
                'custom_dimensions': custom_dimensions,
                'operation_Id': run_id
            }
        )

# Instancia global
app_insights_logger = AppInsightsLogger()