def _reparar_comando_con_memoria(comando: str, campo: str, valor: str) -> str:
    """Repara comando CLI agregando parámetro faltante desde memoria"""
    if campo == "resourceGroup" and "--resource-group" not in comando and "-g" not in comando:
        return f"{comando} --resource-group {valor}"
    elif campo == "location" and "--location" not in comando and "-l" not in comando:
        return f"{comando} --location {valor}"
    elif campo == "subscriptionId" and "--subscription" not in comando:
        return f"{comando} --subscription {valor}"
    return comando

def _ejecutar_comando_reparado(comando_reparado: str) -> func.HttpResponse:
    """Ejecuta comando reparado con memoria"""
    try:
        result = subprocess.run(
            comando_reparado,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        return func.HttpResponse(
            json.dumps({
                "exito": result.returncode == 0,
                "comando_reparado": comando_reparado,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "autorreparado": True
            }),
            mimetype="application/json"
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "exito": False,
                "error": f"Error ejecutando comando reparado: {str(e)}",
                "comando_reparado": comando_reparado
            }),
            mimetype="application/json",
            status_code=500
        )