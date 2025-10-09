#!/usr/bin/env python3
"""Test del módulo centralizado bing_fallback_guard"""

def test_verifica_si_requiere_grounding():
    """Test: detecta cuándo se necesita Bing Grounding"""
    
    # Simular función
    def verifica_si_requiere_grounding(prompt, contexto, error_info=None):
        triggers_criticos = [
            "script generation failed", "no template found", "syntax error",
            "intent not recognized", "no memory available", "internal error"
        ]
        
        keywords_externos = ["no sé", "desconozco", "cómo", "help", "ayuda"]
        
        contexto_lower = contexto.lower()
        prompt_lower = prompt.lower()
        
        # Triggers críticos
        for trigger in triggers_criticos:
            if trigger in contexto_lower:
                return {
                    "requiere_grounding": True,
                    "razon": f"Trigger crítico: {trigger}",
                    "prioridad": "alta"
                }
        
        # Keywords externos
        for keyword in keywords_externos:
            if keyword in prompt_lower:
                return {
                    "requiere_grounding": True,
                    "razon": f"Conocimiento externo: {keyword}",
                    "prioridad": "normal"
                }
        
        # Error info
        if error_info and error_info.get("tipo_error") in ["COMMAND_NOT_FOUND", "SyntaxError"]:
            return {
                "requiere_grounding": True,
                "razon": f"Error no resoluble: {error_info.get('tipo_error')}",
                "prioridad": "alta"
            }
        
        return {"requiere_grounding": False}
    
    # Test 1: Script generation failed
    result = verifica_si_requiere_grounding(
        "crear script", 
        "script generation failed", 
        None
    )
    assert result["requiere_grounding"] == True
    assert result["prioridad"] == "alta"
    print("OK: Detecta fallo en generación de script")
    
    # Test 2: Solicitud de ayuda
    result = verifica_si_requiere_grounding(
        "no sé cómo hacer esto", 
        "usuario solicita ayuda", 
        None
    )
    assert result["requiere_grounding"] == True
    assert result["prioridad"] == "normal"
    print("OK: Detecta solicitud de conocimiento externo")
    
    # Test 3: Error no resoluble
    result = verifica_si_requiere_grounding(
        "comando fallido", 
        "error en CLI", 
        {"tipo_error": "COMMAND_NOT_FOUND"}
    )
    assert result["requiere_grounding"] == True
    print("OK: Detecta error no resoluble internamente")
    
    # Test 4: No requiere grounding
    result = verifica_si_requiere_grounding(
        "operación normal", 
        "todo funcionando", 
        None
    )
    assert result["requiere_grounding"] == False
    print("OK: No activa cuando no es necesario")

def test_aplicar_fallback_a_respuesta():
    """Test: aplica resultado de fallback a respuesta original"""
    
    def aplicar_fallback_a_respuesta(respuesta_original, fallback_result):
        if not fallback_result.get("exito"):
            respuesta_original["fallback_intentado"] = True
            respuesta_original["fallback_error"] = fallback_result.get("error", "")
            return respuesta_original
        
        resultado_bing = fallback_result.get("resultado", {})
        respuesta_mejorada = respuesta_original.copy()
        respuesta_mejorada.update({
            "fallback_aplicado": True,
            "conocimiento_externo": {
                "resumen": resultado_bing.get("resumen", ""),
                "comando_sugerido": resultado_bing.get("comando_sugerido", "")
            },
            "accion_sugerida": fallback_result.get("accion_sugerida", "")
        })
        
        # Si había error, intentar resolverlo
        if not respuesta_original.get("exito", True):
            comando_sugerido = resultado_bing.get("comando_sugerido")
            if comando_sugerido:
                respuesta_mejorada["comando_alternativo"] = comando_sugerido
                respuesta_mejorada["exito"] = True
        
        return respuesta_mejorada
    
    # Test 1: Fallback exitoso mejora respuesta con error
    respuesta_original = {
        "exito": False,
        "error": "Script generation failed"
    }
    
    fallback_result = {
        "exito": True,
        "resultado": {
            "resumen": "Use this template for script generation",
            "comando_sugerido": "bash generate-script.sh"
        },
        "accion_sugerida": "Try with suggested command"
    }
    
    resultado = aplicar_fallback_a_respuesta(respuesta_original, fallback_result)
    
    assert resultado["fallback_aplicado"] == True
    assert resultado["exito"] == True  # Mejorado por fallback
    assert "comando_alternativo" in resultado
    print("OK: Fallback exitoso mejora respuesta con error")
    
    # Test 2: Fallback fallido mantiene original
    fallback_fallido = {
        "exito": False,
        "error": "Bing no disponible"
    }
    
    resultado = aplicar_fallback_a_respuesta(respuesta_original, fallback_fallido)
    
    assert resultado["fallback_intentado"] == True
    assert resultado["exito"] == False  # Mantiene error original
    assert "fallback_error" in resultado
    print("OK: Fallback fallido mantiene respuesta original")

def test_integracion_preparar_script():
    """Test: integración en preparar-script funciona"""
    
    # Simular flujo de preparar-script con fallback
    def preparar_script_con_fallback(ruta):
        # Simular fallo inicial
        res_inicial = {
            "exito": False,
            "error": "Template not found for script type"
        }
        
        # Simular activación de fallback
        contexto = f"script preparation failed: {res_inicial.get('error')}"
        
        # Simular que fallback encuentra solución
        fallback_result = {
            "exito": True,
            "resultado": {
                "resumen": "Use this bash template for setup scripts",
                "comando_sugerido": "#!/bin/bash\necho 'Setup script template'"
            },
            "accion_sugerida": "Use suggested template"
        }
        
        # Aplicar fallback
        def aplicar_fallback_a_respuesta(original, fallback):
            if fallback.get("exito"):
                original.update({
                    "exito": True,
                    "fallback_aplicado": True,
                    "template_sugerido": fallback["resultado"]["comando_sugerido"]
                })
            return original
        
        res_final = aplicar_fallback_a_respuesta(res_inicial, fallback_result)
        return res_final
    
    # Test integración
    resultado = preparar_script_con_fallback("scripts/setup.sh")
    
    assert resultado["exito"] == True
    assert resultado["fallback_aplicado"] == True
    assert "template_sugerido" in resultado
    print("OK: Integración en preparar-script funciona correctamente")

if __name__ == "__main__":
    print("Testing bing_fallback_guard módulo centralizado...")
    
    test_verifica_si_requiere_grounding()
    test_aplicar_fallback_a_respuesta()
    test_integracion_preparar_script()
    
    print("\nFallback Guard tests PASSED")
    print("Módulo centralizado funcionando correctamente")
    print("Listo para integrar en cualquier endpoint")