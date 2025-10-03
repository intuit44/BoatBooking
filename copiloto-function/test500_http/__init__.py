import azure.functions as func
import logging

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint de prueba que siempre devuelve HTTP 500
    para activar alertas de Application Insights
    """
    logging.info('🚨 test500_http: Generando error 500 simulado para pruebas de alertas')
    
    return func.HttpResponse(
        "Internal Server Error (simulado para pruebas de Application Insights)",
        status_code=500
    )