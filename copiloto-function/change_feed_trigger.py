# -*- coding: utf-8 -*-
"""
Azure Function con Change Feed trigger para promoción automática de fixes
"""
import azure.functions as func
import json
import logging
from datetime import datetime
from services.cosmos_fixes_service import cosmos_fixes_service
from services.app_insights_logger import app_insights_logger

app = func.FunctionApp()

@app.function_name(name="fixes_change_feed")
@app.cosmos_db_trigger(
    arg_name="documents",
    database_name="agentMemory",
    container_name="fixes",
    connection="COSMOSDB_CONNECTION_STRING",
    lease_container_name="leases",
    create_lease_container_if_not_exists=True
)
def fixes_change_feed_trigger(documents: func.DocumentList) -> None:
    """
    Trigger de Change Feed que procesa cambios en fixes
    y ejecuta promoción automática cuando es necesario
    """
    
    if not documents:
        return
    
    run_id = f"changefeed_{int(datetime.now().timestamp())}"
    logging.info(f'[{run_id}] Processing {len(documents)} document changes')
    
    promovidos = 0
    fallidos = 0
    fixes_procesados = []
    
    for doc in documents:
        fix_id: str = "unknown"
        try:
            doc_dict = dict(doc)
            fix_id = doc_dict.get('id') or "unknown"
            estado = doc_dict.get('estado')
            prioridad = doc_dict.get('prioridad', 0)
            
            fixes_procesados.append(fix_id)
            
            # Solo procesar fixes pendientes de alta prioridad
            if estado == 'pendiente' and prioridad >= 8:
                
                # Log del evento
                app_insights_logger.log_fix_event(
                    'fix_detected_for_promotion',
                    fix_id, run_id, estado, 
                    doc_dict.get('target', ''), prioridad
                )
                
                # Evaluar y ejecutar promoción
                if _should_auto_promote(doc_dict):
                    resultado = _execute_fix_promotion(doc_dict, run_id)
                    
                    if resultado.get('exito'):
                        promovidos += 1
                        app_insights_logger.log_fix_event(
                            'fix_promoted_successfully',
                            fix_id, run_id, 'promovido',
                            doc_dict.get('target', ''), prioridad,
                            {'resultado': resultado}
                        )
                    else:
                        fallidos += 1
                        app_insights_logger.log_fix_event(
                            'fix_promotion_failed',
                            fix_id, run_id, 'fallido',
                            doc_dict.get('target', ''), prioridad,
                            {'error': resultado.get('error')}
                        )
                        
        except Exception as e:
            logging.error(f'[{run_id}] Error processing document {fix_id}: {str(e)}')
            fallidos += 1
    
    # Log del batch completo
    app_insights_logger.log_promotion_batch(
        run_id, promovidos, fallidos, fixes_procesados
    )
    
    logging.info(f'[{run_id}] Batch completed: {promovidos} promoted, {fallidos} failed')

def _should_auto_promote(fix_data: dict) -> bool:
    """Evalúa si un fix debe ser auto-promovido"""
    # Lógica de evaluación (reutilizar de auto_promoter)
    prioridad = fix_data.get('prioridad', 0)
    tipo = fix_data.get('tipo', '')
    
    # Auto-promover solo fixes de muy alta prioridad y tipos seguros
    return (prioridad >= 9 and 
            tipo in ['config_update', 'dependency_fix', 'security_patch'])

def _execute_fix_promotion(fix_data: dict, run_id: str) -> dict:
    """Ejecuta la promoción de un fix"""
    try:
        if cosmos_fixes_service is None:
            return {
                'exito': False,
                'error': 'cosmos_fixes_service is not available'
            }
        # Actualizar estado a 'promovido' con ETag
        etag = str(fix_data.get('_etag') or "")
        resultado = cosmos_fixes_service.update_fix_status(
            fix_data['id'],
            'promovido',
            etag
        )

        
        if resultado.get('exito'):
            # Aquí iría la lógica de ejecución real del fix
            # Por ahora solo simulamos
            return {
                'exito': True,
                'mensaje': f'Fix {fix_data["id"]} promovido exitosamente',
                'timestamp': datetime.now().isoformat()
            }
        else:
            return resultado
            
    except Exception as e:
        return {
            'exito': False,
            'error': str(e)
        }