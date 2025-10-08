// Snippet para que el agente interprete 422 y reaccione automáticamente
async function handleCliResponse(response) {
    if (response.status === 422 && response.data.tipo_error === "MissingParameter") {
        const { endpoint_alternativo, campo_faltante, contexto } = response.data;
        
        console.log(`🔧 Autorreparación: Falta ${campo_faltante}, ejecutando ${endpoint_alternativo}`);
        
        try {
            // Ejecutar endpoint alternativo automáticamente
            const altResponse = await fetch(endpoint_alternativo, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const altData = await altResponse.json();
            
            if (altData.exito && altData[campo_faltante]) {
                // Reconstruir comando con valor obtenido
                const comandoOriginal = contexto.comando;
                const valorObtenido = altData[campo_faltante];
                const comandoReparado = repararComando(comandoOriginal, campo_faltante, valorObtenido);
                
                console.log(`✅ Valor obtenido: ${campo_faltante}=${valorObtenido}`);
                console.log(`🔄 Reintentando: ${comandoReparado}`);
                
                // Reintentar comando reparado
                return await fetch('/api/ejecutar-cli', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ comando: comandoReparado })
                });
            }
        } catch (error) {
            console.error(`❌ Error en autorreparación: ${error.message}`);
        }
    }
    
    return response;
}

function repararComando(comando, campo, valor) {
    const reparaciones = {
        'resourceGroup': () => `${comando} --resource-group ${valor}`,
        'location': () => `${comando} --location ${valor}`,
        'subscriptionId': () => `${comando} --subscription ${valor}`
    };
    
    return reparaciones[campo] ? reparaciones[campo]() : comando;
}

// Uso:
// const response = await fetch('/api/ejecutar-cli', { ... });
// const finalResponse = await handleCliResponse(response);