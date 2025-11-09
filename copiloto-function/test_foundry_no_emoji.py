# -*- coding: utf-8 -*-
"""
Test de captura de entrada del usuario desde Foundry UI (sin emojis para terminal)
Simula el payload que envía Azure AI Foundry y valida que se persista correctamente.
"""
import os
import json
import requests
import time
from datetime import datetime

# Cargar variables de entorno desde local.settings.json
try:
    with open("local.settings.json", "r", encoding="utf-8") as f:
        settings = json.load(f)
        for key, value in settings.get("Values", {}).items():
            os.environ[key] = str(value)
    print("[OK] Variables de entorno cargadas desde local.settings.json\n")
except Exception as e:
    print(f"[WARN] No se pudo cargar local.settings.json: {e}\n")

# Configuración
BASE_URL = "http://localhost:7071"
ENDPOINT = "/api/copiloto"


def test_foundry_input_capture():
    """Simula mensaje desde Foundry y valida persistencia completa."""

    print("\n" + "="*80)
    print("[TEST] Captura de entrada del usuario desde Foundry")
    print("="*80 + "\n")

    # Payload REAL de Foundry (emulación exacta)
    payload = {
        "tipo": "user_input",
        "input": "valida si puedes ver los ultimos cambios que he realizado",
        "session_id": "universal_session",
        "agent_id": "foundry_user",
        "metadata": {
            "source": "Foundry.UI",
            "interface": "Copiloto",
            "trigger": "manual"
        }
    }

    headers = {
        "Content-Type": "application/json",
        "user-agent": "azure-agents"
    }

    print(f"[SEND] Enviando mensaje a {BASE_URL}{ENDPOINT}")
    print(f"[INPUT] {payload['input']}")
    print(f"[SESSION] {payload['session_id']}")
    print(f"[AGENT] {payload['agent_id']}")
    print(f"[METADATA] {payload['metadata']}\n")

    try:
        response = requests.post(
            f"{BASE_URL}{ENDPOINT}",
            json=payload,
            headers=headers,
            timeout=30
        )

        print(f"[STATUS] {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"[OK] Respuesta exitosa del endpoint\n")
            # Usar ensure_ascii=True para evitar problemas con emojis en terminal
            print(f"[RESPONSE] {json.dumps(result, indent=2, ensure_ascii=True)[:500]}...\n")
        else:
            print(f"[WARN] Respuesta no exitosa: {response.text[:500]}\n")

        # Esperar a que se complete la indexación
        print("[WAIT] Esperando 5 segundos para indexacion completa...")
        time.sleep(5)

        # Validar en Cosmos DB
        print("\n" + "-"*80)
        print("[VALIDATE] COSMOS DB")
        print("-"*80 + "\n")

        validate_cosmos_storage(payload['session_id'], payload['input'])

        # Validar en Azure AI Search
        print("\n" + "-"*80)
        print("[VALIDATE] AZURE AI SEARCH")
        print("-"*80 + "\n")

        validate_ai_search_index(payload['input'])

        # Validar respuesta semántica del agente
        print("\n" + "-"*80)
        print("[VALIDATE] RESPUESTA SEMANTICA DEL AGENTE")
        print("-"*80 + "\n")

        validate_agent_response(payload['session_id'])

        # Validar memoria global (respuesta conversacional)
        print("\n" + "-"*80)
        print("[VALIDATE] MEMORIA GLOBAL (RESPUESTA FOUNDRY)")
        print("-"*80 + "\n")

        validate_memoria_global()

        print("\n" + "="*80)
        print("[OK] TEST COMPLETADO")
        print("="*80 + "\n")

    except Exception as e:
        print(f"[ERROR] Error en el test: {e}")
        import traceback
        traceback.print_exc()


def validate_cosmos_storage(session_id: str, mensaje: str):
    """Valida que el mensaje se guardó en Cosmos DB."""
    try:
        from services.memory_service import memory_service

        # Buscar en historial de sesión
        historial = memory_service.get_session_history(session_id, limit=10)

        print(f"[INFO] Total de documentos en sesion '{session_id}': {len(historial)}")

        # Buscar el mensaje específico
        encontrado = False
        for doc in historial:
            texto = doc.get("texto_semantico", "")
            if mensaje in texto:
                encontrado = True
                print(f"\n[OK] Documento encontrado en Cosmos:")
                print(f"   ID: {doc.get('id')}")
                print(f"   Session: {doc.get('session_id')}")
                print(f"   Event Type: {doc.get('event_type')}")
                print(f"   Texto: {texto[:100]}...")
                print(f"   Timestamp: {doc.get('timestamp')}")
                break

        if not encontrado:
            print(f"\n[WARN] Mensaje NO encontrado en Cosmos DB")
            print(f"[INFO] Ultimos 3 documentos:")
            for i, doc in enumerate(historial[:3], 1):
                print(f"\n   {i}. ID: {doc.get('id')}")
                print(f"      Texto: {doc.get('texto_semantico', '')[:80]}...")

    except Exception as e:
        print(f"[ERROR] Error validando Cosmos: {e}")


def validate_ai_search_index(mensaje: str):
    """Valida que el mensaje se indexó en Azure AI Search."""
    try:
        from endpoints_search_memory import buscar_memoria_endpoint

        # Buscar el mensaje
        resultado = buscar_memoria_endpoint({
            "query": mensaje,
            "top": 5
        })

        if resultado.get("exito"):
            docs = resultado.get("documentos", [])
            print(f"[INFO] Total de documentos encontrados: {len(docs)}")

            # Buscar coincidencia exacta
            encontrado = False
            for doc in docs:
                texto = doc.get("texto_semantico", "")
                if mensaje in texto:
                    encontrado = True
                    print(f"\n[OK] Documento encontrado en AI Search:")
                    print(f"   ID: {doc.get('id')}")
                    print(f"   Score: {doc.get('@search.score', 'N/A')}")
                    print(f"   Texto: {texto[:100]}...")
                    break

            if not encontrado:
                print(f"\n[WARN] Mensaje NO encontrado en AI Search")
                print(f"[INFO] Documentos similares:")
                for i, doc in enumerate(docs[:3], 1):
                    print(f"\n   {i}. Score: {doc.get('@search.score', 'N/A')}")
                    print(f"      Texto: {doc.get('texto_semantico', '')[:80]}...")
        else:
            print(f"[ERROR] Error en busqueda: {resultado.get('error')}")

    except Exception as e:
        print(f"[ERROR] Error validando AI Search: {e}")


def validate_agent_response(session_id: str):
    """Valida que la respuesta del agente se guardó como evento semántico SIN emojis."""
    try:
        from services.memory_service import memory_service
        from datetime import datetime, timedelta

        # Buscar respuestas semánticas RECIENTES (creadas en los últimos 10 segundos)
        historial = memory_service.get_session_history(session_id, limit=50)
        
        # Filtrar solo las creadas en los últimos 10 segundos
        ahora = datetime.utcnow()
        respuestas_recientes = []
        for doc in historial:
            if doc.get("event_type") == "respuesta_semantica":
                try:
                    ts_str = doc.get('timestamp', '')
                    if ts_str:
                        # Remover 'Z' si existe
                        ts_str = ts_str.replace('Z', '')
                        ts = datetime.fromisoformat(ts_str)
                        if (ahora - ts).total_seconds() < 15:
                            respuestas_recientes.append(doc)
                except:
                    pass

        print(f"[INFO] Total de respuestas semanticas RECIENTES: {len(respuestas_recientes)}")

        if respuestas_recientes:
            # Validar la más reciente
            doc_reciente = respuestas_recientes[0]
            texto = doc_reciente.get('texto_semantico', '')
            
            print(f"\n[VALIDATE] DOCUMENTO RECIEN CREADO:")
            print(f"   ID: {doc_reciente.get('id')}")
            print(f"   Timestamp: {doc_reciente.get('timestamp')}")
            print(f"   Texto completo: {texto[:200]}...\n")
            
            # Detectar problemas
            problemas_doc = []
            
            # Emojis técnicos (usando códigos Unicode)
            emojis_tecnicos = ['\U0001F527', '\u2705', '\U0001F4CA', '\U0001F538', '\U0001F539', 
                             '\U0001F4E1', '\U0001F4D8', '\U0001F5C2', '\U0001F4AC', '\U0001F4DD', 
                             '\U0001F4C4', '\u2699', '\U0001F4C8']
            for emoji in emojis_tecnicos:
                if emoji in texto:
                    problemas_doc.append(f"Contiene emoji tecnico: {repr(emoji)}")
            
            # Referencias técnicas
            if 'endpoint' in texto.lower():
                problemas_doc.append("Contiene referencia a 'endpoint'")
            if 'session' in texto.lower() and 'sesion' not in texto.lower():
                problemas_doc.append("Contiene referencia tecnica a 'session'")
            
            if problemas_doc:
                print("[ERROR] DOCUMENTO RECIEN CREADO TIENE PROBLEMAS:\n")
                for problema in problemas_doc:
                    print(f"   * {problema}")
                print("\n[FIX] CORRECCION: Los cambios en memory_route_wrapper.py NO se aplicaron correctamente.")
                print("   Verifica que removiste TODOS los emojis de los bloques 1-5.\n")
            else:
                print("[OK] DOCUMENTO RECIEN CREADO ESTA LIMPIO")
                print("[OK] Sin emojis tecnicos")
                print("[OK] Sin referencias tecnicas")
                print(f"   Vector: {len(doc_reciente.get('vector', []))} dimensiones\n")
        else:
            print("\n[WARN] No se encontraron respuestas semanticas recientes (creadas en los ultimos 10s)")
            print("   Esto puede indicar que registrar_respuesta_semantica() no se ejecuto.\n")

    except Exception as e:
        print(f"[ERROR] Error validando respuesta del agente: {e}")
        import traceback
        traceback.print_exc()


def validate_memoria_global():
    """Valida que /api/memoria-global devuelve respuesta conversacional."""
    try:
        response = requests.get(
            f"{BASE_URL}/api/memoria-global",
            headers={
                "Session-ID": "universal_session",
                "Agent-ID": "foundry_user"
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            respuesta = result.get("respuesta_usuario", "")

            print(f"[INFO] Status: {response.status_code}")
            print(f"[INFO] Longitud respuesta: {len(respuesta)} chars")
            print(f"\n[RESPONSE] respuesta_usuario:\n{respuesta}\n")
            
            # VALIDAR JSON COMPLETO QUE RECIBE FOUNDRY
            print("\n[VALIDATE] JSON COMPLETO QUE RECIBE FOUNDRY:")
            interacciones = result.get("interacciones", [])
            print(f"   Total interacciones en JSON: {len(interacciones)}")
            if interacciones:
                print(f"\n   Primera interaccion (lo que ve Foundry):")
                primera = interacciones[0]
                for key, value in primera.items():
                    valor_str = str(value)[:100]
                    print(f"      {key}: {valor_str}..." if len(str(value)) > 100 else f"      {key}: {value}")
            print()

            # DETECCION DE PROBLEMAS EN EL JSON QUE RECIBE FOUNDRY
            print("\n[VALIDATE] ANALISIS DE DATOS QUE RECIBE FOUNDRY:\n")
            
            # Validar estructura de interacciones
            if interacciones:
                campos_tecnicos_en_json = []
                for i, interaccion in enumerate(interacciones[:3]):
                    texto = interaccion.get("texto_semantico", "")
                    # Buscar emojis técnicos usando códigos Unicode
                    tiene_emojis = any(emoji in texto for emoji in ['\U0001F527', '\u2705', '\U0001F4CA'])
                    if tiene_emojis or "endpoint" in texto.lower():
                        campos_tecnicos_en_json.append({
                            "interaccion": i+1,
                            "texto": texto[:100],
                            "problema": "Contiene emojis tecnicos o referencias a 'endpoint'"
                        })
                
                if campos_tecnicos_en_json:
                    print("[ERROR] PROBLEMA: JSON contiene datos tecnicos que Foundry interpreta\n")
                    for item in campos_tecnicos_en_json:
                        print(f"   Interaccion {item['interaccion']}:")
                        print(f"      Texto: '{item['texto']}...'")
                        print(f"      Problema: {item['problema']}\n")
                    
                    print("[FIX] CORRECCION NECESARIA:")
                    print("   Los documentos en Cosmos DB tienen 'texto_semantico' con formato tecnico.")
                    print("   Foundry lee estos textos y los interpreta, generando respuestas verbosas.\n")
                    print("   Solucion: Limpiar 'texto_semantico' en los documentos guardados.")
                    print("   Ubicacion: memory_route_wrapper.py -> linea ~450")
                    print("   Cambiar: texto_semantico = f'[emoji] {endpoint} [emoji] exitosa'")
                    print("   A: texto_semantico = f'Consulta procesada exitosamente'\n")
            
            # DETECCION DE PROBLEMAS EN sintetizar()
            problemas = []
            
            # 1. Detectar encabezados técnicos (sin emojis, solo texto)
            encabezados_tecnicos = [
                "Otros resultados vectoriales",
                "Actividad relevante (vectores",
                "Interacciones tipo endpoint_call",
                "Resumenes enriquecidos",
                "Otras interacciones recientes"
            ]
            
            for encabezado in encabezados_tecnicos:
                if encabezado.lower() in respuesta.lower():
                    problemas.append({
                        "tipo": "ENCABEZADO_TECNICO",
                        "patron": encabezado,
                        "ubicacion": "function_app.py -> sintetizar()",
                        "linea_aprox": "~1300",
                        "correccion": f"Remover: partes.append('[emoji] {encabezado}')"
                    })
            
            # 2. Detectar formato de lista técnica
            if "* [" in respuesta or "[" in respuesta and "]" in respuesta:
                problemas.append({
                    "tipo": "FORMATO_LISTA_TECNICA",
                    "patron": "* [endpoint]",
                    "ubicacion": "function_app.py -> sintetizar() -> _append_doc()",
                    "linea_aprox": "~1350",
                    "correccion": "Cambiar formato de: '* [{endpoint}]\\n{texto}' a: texto directo sin brackets"
                })
            
            # 3. Detectar referencias a "vectores" o "Cosmos"
            terminos_tecnicos = ["vectores", "cosmos", "score>", "endpoint_call", "fallback"]
            for termino in terminos_tecnicos:
                if termino in respuesta.lower():
                    problemas.append({
                        "tipo": "TERMINOLOGIA_TECNICA",
                        "patron": termino,
                        "ubicacion": "function_app.py -> sintetizar()",
                        "correccion": f"Reemplazar '{termino}' con lenguaje natural"
                    })
            
            # 4. Detectar estructura de múltiples secciones
            if respuesta.count("\n\n") > 3:
                problemas.append({
                    "tipo": "ESTRUCTURA_FRAGMENTADA",
                    "patron": "Multiples secciones separadas",
                    "ubicacion": "function_app.py -> sintetizar()",
                    "correccion": "Sintetizar en un solo parrafo conversacional en lugar de listar secciones"
                })
            
            # REPORTE DE RESULTADOS
            if problemas:
                print("[ERROR] RESPUESTA NO ES CONVERSACIONAL\n")
                print("[FIX] CORRECCIONES NECESARIAS EN function_app.py:\n")
                
                for i, problema in enumerate(problemas, 1):
                    print(f"{i}. {problema['tipo']}")
                    print(f"   Patron detectado: '{problema['patron']}'")
                    print(f"   Ubicacion: {problema['ubicacion']}")
                    if 'linea_aprox' in problema:
                        print(f"   Linea aproximada: {problema['linea_aprox']}")
                    print(f"   [OK] Correccion: {problema['correccion']}")
                    print()
                
                print("[EXAMPLE] RESPUESTA CONVERSACIONAL ESPERADA:")
                print("   'He revisado el historial y encontre 5 interacciones relevantes.")
                print("   Recientemente validaste los ultimos cambios realizados y consultaste")
                print("   los archivos disponibles. Necesitas mas detalles sobre alguna actividad?'\n")
                
                print("[ACTION] ACCION REQUERIDA:")
                print("   1. Limpiar texto_semantico en memory_route_wrapper.py (linea ~450)")
                print("   2. Abrir: copiloto-function/function_app.py")
                print("   3. Buscar: def sintetizar(docs_search, docs_cosmos")
                print("   4. Aplicar correcciones listadas arriba")
                print("   5. Re-ejecutar: python test_foundry_no_emoji.py\n")
            else:
                print("[OK] RESPUESTA ES CONVERSACIONAL")
                print("[OK] Sin patrones tecnicos detectados")
                print("[OK] Formato apropiado para Foundry UI\n")
            
            # Mostrar metadata
            if "sintetizador_usado" in result:
                print(f"[INFO] Sintetizador usado: {result['sintetizador_usado']}")
            if "total_interacciones" in result:
                print(f"[INFO] Total interacciones: {result['total_interacciones']}")

        else:
            print(f"[ERROR] Status {response.status_code}")
            print(f"   {response.text[:200]}")

    except Exception as e:
        print(f"[ERROR] Error validando memoria global: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_foundry_input_capture()
