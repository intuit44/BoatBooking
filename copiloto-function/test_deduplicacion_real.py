import hashlib
import re

"""
Test REAL de deduplicacion y validacion de contexto
Verifica que NO se pierdan interacciones valiosas
"""


def test_deduplicacion_logica():
    """Simula la logica de deduplicacion actual"""

    # Datos de prueba REALES (sin emojis)
    interacciones_test = [
        {
            "texto_semantico": "Analisis contextual completo: Se diagnosticaron 3 errores principales en la memoria semantica. Accion correctiva aplicada.",
            "endpoint": "/api/diagnostico",
            "session_id": "session-123",
            "exito": True
        },
        {
            "texto_semantico": "Analisis contextual completo: Se diagnosticaron 3 errores principales en la memoria semantica. Accion correctiva aplicada.",
            "endpoint": "/api/diagnostico",
            "session_id": "session-123",
            "exito": True
        },
        {
            "texto_semantico": "Consulta de historial completada. Total: 5 interacciones. Resumen de la ultima actividad disponible.",
            "endpoint": "/api/historial-interacciones",
            "session_id": "session-123",
            "exito": True
        },
        {
            "texto_semantico": "Ultimo tema: copiloto. Resumen de la ultima actividad: consulta de memoria previa.",
            "endpoint": "/api/memoria-global",
            "session_id": "session-123",
            "exito": True
        },
        {
            "texto_semantico": "Operacion de lectura exitosa. Archivo: function_app.py. Contenido: 15000 caracteres procesados.",
            "endpoint": "/api/leer-archivo",
            "session_id": "session-123",
            "exito": True
        },
        {
            "texto_semantico": "Comando ejecutado: az storage account list. Resultado: 3 cuentas encontradas. Tiempo: 2.1s",
            "endpoint": "/api/ejecutar-cli",
            "session_id": "session-456",
            "exito": True
        }
    ]

    print("\n" + "="*80)
    print("TEST DE DEDUPLICACION Y VALIDACION")
    print("="*80)

    # 1. DEDUPLICACION (logica actual)
    print("\n1. DEDUPLICACION POR HASH COMPLETO (SHA256):")
    vistos = set()
    deduplicados = []

    for i, item in enumerate(interacciones_test):
        texto = item.get("texto_semantico", "")
        clave = hashlib.sha256(texto.strip().lower().encode()).hexdigest()

        if clave and clave not in vistos:
            vistos.add(clave)
            deduplicados.append(item)
            print(f"   [ACEPTADO {len(deduplicados)}] {texto[:80]}...")
        else:
            print(f"   [DUPLICADO] {texto[:80]}...")

    print(f"\n   Total original: {len(interacciones_test)}")
    print(f"   Despues deduplicacion: {len(deduplicados)}")
    print(f"   Perdidos: {len(interacciones_test) - len(deduplicados)}")

    # 2. FILTRADO POR LONGITUD MINIMA
    print("\n2. FILTRADO POR LONGITUD MINIMA (>50 chars):")
    textos_validos = []

    for item in deduplicados:
        texto = item.get('texto_semantico', '').strip()
        if texto and len(texto) > 50:
            textos_validos.append(texto)
            print(f"   [VALIDO] Longitud: {len(texto)} - {texto[:60]}...")
        else:
            print(f"   [RECHAZADO] Longitud: {len(texto)} - Muy corto")

    print(f"\n   Despues filtrado: {len(textos_validos)}")
    print(f"   Perdidos: {len(deduplicados) - len(textos_validos)}")

    # 3. DETECCION DE PATRONES BASURA
    print("\n3. DETECCION DE PATRONES BASURA:")
    patrones_basura = [
        "resumen de la ultima actividad",
        "consulta de historial completada",
        "ultimo tema:",
        "sin resumen de conversacion"
    ]

    textos_limpios = []
    for texto in textos_validos:
        texto_l = texto.lower()

        # Excepción: si el patrón aparece AL INICIO pero el resto contiene detalles concretos,
        # no marcar como basura.
        def inicio_con_detalle(texto_l, patron):
            if texto_l.startswith(patron):
                resto = texto_l[len(patron):].strip()
                # criterios simples para "detalles concretos": presencia de números o keywords y longitud
                detalle_keywords = (
                    "total", "resultado", "archivo", "procesado", "encontrado",
                    "tiempo", "diagnosticado", "caracteres", "cuentas", "errores", "completado"
                )
                if len(resto) > 30 and (any(kw in resto for kw in detalle_keywords) or re.search(r'\d', resto)):
                    return True
            return False

        aparece_patron = any(p in texto_l for p in patrones_basura)
        es_inicio_excepcion = any(inicio_con_detalle(texto_l, p)
                                  for p in patrones_basura)

        es_basura = False
        if len(texto_l) < 100 and aparece_patron:
            # Si no cumple la excepción por inicio+detalles y tampoco contiene palabras clave útiles, es basura
            if not es_inicio_excepcion and not any(kw in texto_l for kw in ("diagnosticado", "encontrado", "procesado", "ejecutado", "analizado")):
                es_basura = True

        if not es_basura:
            textos_limpios.append(texto)
            print(f"   [LIMPIO] {texto[:60]}...")
        else:
            print(f"   [BASURA] {texto[:60]}...")

    print(f"\n   Despues limpieza: {len(textos_limpios)}")
    print(f"   Perdidos: {len(textos_validos) - len(textos_limpios)}")

    # 4. RESULTADO FINAL
    print("\n" + "="*80)
    print("RESULTADO FINAL:")
    print("="*80)
    print(f"   Interacciones originales: {len(interacciones_test)}")
    print(f"   Interacciones finales: {len(textos_limpios)}")
    print(
        f"   Tasa de perdida: {((len(interacciones_test) - len(textos_limpios)) / len(interacciones_test) * 100):.1f}%")

    # 5. ANALISIS DE PERDIDAS
    print("\n" + "="*80)
    print("ANALISIS DE PERDIDAS:")
    print("="*80)

    perdidas = {
        "duplicados": len(interacciones_test) - len(deduplicados),
        "muy_cortos": len(deduplicados) - len(textos_validos),
        "basura": len(textos_validos) - len(textos_limpios)
    }

    for tipo, cantidad in perdidas.items():
        if cantidad > 0:
            print(f"   [PROBLEMA] {tipo}: {cantidad} interacciones perdidas")

    # 6. RECOMENDACIONES
    print("\n" + "="*80)
    print("RECOMENDACIONES:")
    print("="*80)

    if perdidas["duplicados"] > 0:
        print("   1. Deduplicacion muy agresiva (100 chars)")
        print("      Solucion: Aumentar a 150 chars o usar hash completo")

    if perdidas["basura"] > 0:
        print("   2. Filtro de basura elimina contenido valido")
        print("      Solucion: Mejorar patrones o eliminar filtro")

    if len(textos_limpios) < len(interacciones_test) * 0.5:
        print("   3. CRITICO: Se pierde mas del 50% de interacciones")
        print("      Solucion: Revisar toda la cadena de filtros")

    return {
        "original": len(interacciones_test),
        "final": len(textos_limpios),
        "perdidas": perdidas,
        "tasa_perdida": ((len(interacciones_test) - len(textos_limpios)) / len(interacciones_test) * 100)
    }


def test_validacion_contexto():
    """Simula validacion de contexto que puede descartar interacciones"""

    print("\n" + "="*80)
    print("TEST DE VALIDACION DE CONTEXTO")
    print("="*80)

    interacciones = [
        {"texto_semantico": "Analisis completo de 3 errores",
            "timestamp": "2025-01-10T10:00:00"},
        {"texto_semantico": "", "timestamp": "2025-01-10T10:01:00"},
        {"texto_semantico": "x", "timestamp": "2025-01-10T10:02:00"},
        {"texto_semantico": "Comando ejecutado correctamente",
            "timestamp": "2025-01-10T10:03:00"},
    ]

    print(f"\n   Interacciones a validar: {len(interacciones)}")

    # Validacion actual
    validadas = []
    for i, inter in enumerate(interacciones):
        texto = inter.get("texto_semantico", "").strip()
        if texto and len(texto) > 20:
            validadas.append(inter)
            print(f"   [{i+1}] VALIDO: {texto}")
        else:
            print(f"   [{i+1}] INVALIDO: '{texto}' (longitud: {len(texto)})")

    print(
        f"\n   Resultado: {len(interacciones)} -> {len(validadas)} interacciones")

    if len(validadas) == 0:
        print("\n   [ALERTA] TODAS las interacciones fueron descartadas")
        print("   Esto causa que respuesta_usuario este vacia")

    return len(validadas)


def test_construccion_respuesta_usuario():
    """Simula como se construye respuesta_usuario final"""

    print("\n" + "="*80)
    print("TEST DE CONSTRUCCION DE RESPUESTA_USUARIO")
    print("="*80)

    textos_finales = [
        "Analisis contextual completo: 3 errores detectados y corregidos",
        "Operacion de lectura exitosa: function_app.py procesado",
        "Comando ejecutado: az storage account list - 3 cuentas encontradas"
    ]

    print(f"\n   Textos disponibles: {len(textos_finales)}")

    # Construccion actual
    respuesta = "\n\n---\n\n".join(
        textos_finales) if textos_finales else "No hay interacciones con contenido semantico disponible."

    print(f"\n   Longitud respuesta_usuario: {len(respuesta)} caracteres")
    print(f"\n   Preview:")
    print("   " + "-"*76)
    print("   " + respuesta[:200].replace("\n", "\n   "))
    if len(respuesta) > 200:
        print("   ...")
    print("   " + "-"*76)

    return len(respuesta)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("SUITE DE TESTS DE DEDUPLICACION Y VALIDACION")
    print("="*80)

    # Test 1
    resultado1 = test_deduplicacion_logica()

    # Test 2
    resultado2 = test_validacion_contexto()

    # Test 3
    resultado3 = test_construccion_respuesta_usuario()

    # Resumen final
    print("\n" + "="*80)
    print("RESUMEN EJECUTIVO")
    print("="*80)
    print(
        f"\n   Tasa de perdida en deduplicacion: {resultado1['tasa_perdida']:.1f}%")
    print(f"   Interacciones validadas: {resultado2}")
    print(f"   Longitud respuesta_usuario: {resultado3} chars")

    if resultado1['tasa_perdida'] > 30:
        print("\n   [CRITICO] Perdida excesiva de interacciones")
    elif resultado2 == 0:
        print("\n   [CRITICO] Validacion descarta todo")
    elif resultado3 < 100:
        print("\n   [ADVERTENCIA] Respuesta muy corta")
    else:
        print("\n   [OK] Sistema funcionando correctamente")

    print("\n" + "="*80)
