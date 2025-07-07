# nlp_processor.py
import re
import json
from typing import Dict, Any, List, Tuple, Optional
from difflib import SequenceMatcher

class ProcesadorSemantico:
    """Procesador de lenguaje natural para interpretar comandos semánticos"""
    
    def __init__(self):
        # Definir patrones de intenciones y sus variaciones
        self.intenciones = {
            "ejecutar_comando": {
                "patrones": [
                    r"(?:ejecuta|corre|run|execute|lanza|inicia)\s+(?:el\s+)?(?:comando\s+)?(.+)",
                    r"(?:por favor\s+)?(?:puedes\s+)?ejecutar\s+(.+)",
                    r"comando:\s*(.+)",
                    r"(?:quiero|necesito|quisiera)\s+(?:que\s+)?(?:ejecutes|corras)\s+(.+)",
                    r"(.+)\s+(?:desde|en)\s+(?:la\s+)?(?:terminal|consola|shell)",
                    r"(?:muestra|dame|dime)\s+(?:el\s+)?(?:resultado|output|salida)\s+de\s+(.+)",
                ],
                "palabras_clave": ["ejecutar", "correr", "run", "comando", "terminal", "shell", "consola", "execute", "lanzar"],
                "ejemplos": [
                    "ejecuta echo hola mundo",
                    "por favor corre ls -la",
                    "necesito que ejecutes npm test",
                    "muéstrame el resultado de pwd"
                ]
            },
            "crear_archivo": {
                "patrones": [
                    r"(?:crea|crear|create|genera|generar)\s+(?:un\s+)?(?:archivo|file)\s+(?:llamado\s+)?([^\s]+)(?:\s+con\s+(?:el\s+)?(?:contenido|content)?\s*[:：]?\s*(.+))?",
                    r"(?:nuevo|new)\s+(?:archivo|file)\s+([^\s]+)",
                    r"(?:guarda|save|guardar)\s+(?:esto\s+)?(?:en|como)\s+([^\s]+)(?:\s*[:：]\s*(.+))?",
                    r"archivo\s+([^\s]+)\s+con\s+(.+)",
                ],
                "palabras_clave": ["crear", "archivo", "generar", "nuevo", "guardar", "file", "create", "save"],
                "ejemplos": [
                    "crea un archivo test.py con print('hola')",
                    "nuevo archivo config.json",
                    "guarda esto en notas.txt: recordar hacer deploy"
                ]
            },
            "listar_archivos": {
                "patrones": [
                    r"(?:lista|list|muestra|show)\s+(?:los\s+)?(?:archivos|files|directorios|carpetas)",
                    r"(?:qué|que)\s+(?:archivos|files)\s+(?:hay|tengo|existen)",
                    r"(?:muéstrame|mostrar)\s+(?:el\s+)?(?:contenido|content)\s+(?:del\s+)?(?:directorio|carpeta|folder)",
                    r"ls\s*(.*)",
                    r"dir\s*(.*)"
                ],
                "palabras_clave": ["listar", "lista", "archivos", "mostrar", "ver", "files", "directorio", "ls", "dir"],
                "ejemplos": [
                    "lista los archivos",
                    "qué archivos hay en src",
                    "muéstrame el contenido del directorio"
                ]
            },
            "leer_archivo": {
                "patrones": [
                    r"(?:lee|leer|read|muestra|show|abre|open)\s+(?:el\s+)?(?:archivo|file)?\s+([^\s]+)",
                    r"(?:qué|que)\s+(?:contiene|dice|hay\s+en)\s+(?:el\s+)?(?:archivo\s+)?([^\s]+)",
                    r"(?:muéstrame|mostrar|ver)\s+(?:el\s+)?(?:contenido|content)\s+(?:de|del)\s+([^\s]+)",
                    r"cat\s+([^\s]+)"
                ],
                "palabras_clave": ["leer", "lee", "mostrar", "abrir", "contenido", "cat", "read", "open"],
                "ejemplos": [
                    "lee el archivo config.json",
                    "qué contiene package.json",
                    "muéstrame el contenido de README.md"
                ]
            },
            "deploy": {
                "patrones": [
                    r"(?:deploy|desplegar|despliegue|publicar|publish)",
                    r"(?:sube|subir|upload)\s+(?:a\s+)?(?:producción|production|servidor|server)",
                    r"(?:hacer|haz)\s+(?:el\s+)?deploy",
                    r"serverless\s+deploy"
                ],
                "palabras_clave": ["deploy", "desplegar", "publicar", "producción", "serverless"],
                "ejemplos": [
                    "haz deploy",
                    "despliega la aplicación",
                    "sube a producción"
                ]
            },
            "instalar_dependencias": {
                "patrones": [
                    r"(?:instala|install|instalar)\s+(?:las\s+)?(?:dependencias|dependencies|paquetes|packages)",
                    r"npm\s+install",
                    r"(?:ejecuta|run)\s+npm\s+install",
                    r"(?:instala|install)\s+([a-zA-Z0-9\-@/]+)"
                ],
                "palabras_clave": ["instalar", "install", "npm", "dependencias", "paquetes"],
                "ejemplos": [
                    "instala las dependencias",
                    "npm install",
                    "instala express"
                ]
            },
            "ayuda": {
                "patrones": [
                    r"(?:ayuda|help|ayúdame|qué puedes hacer|what can you do)",
                    r"(?:no\s+)?(?:sé|se)\s+(?:qué|que|cómo|como)",
                    r"(?:explica|explicar|explain)",
                    r"(?:comandos|commands)\s+(?:disponibles|available)"
                ],
                "palabras_clave": ["ayuda", "help", "explicar", "comandos", "qué", "cómo"],
                "ejemplos": [
                    "ayuda",
                    "qué puedes hacer",
                    "no sé cómo empezar"
                ]
            }
        }
        
        # Mapeo de intenciones a acciones del sistema
        self.mapeo_acciones = {
            "ejecutar_comando": self._generar_accion_ejecutar,
            "crear_archivo": self._generar_accion_crear_archivo,
            "listar_archivos": self._generar_accion_listar,
            "leer_archivo": self._generar_accion_leer,
            "deploy": self._generar_accion_deploy,
            "instalar_dependencias": self._generar_accion_npm,
            "ayuda": self._generar_accion_ayuda
        }
    
    def procesar_comando_semantico(self, mensaje: str, contexto: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Procesa un comando en lenguaje natural y devuelve la acción correspondiente"""
        
        # Limpiar y normalizar el mensaje
        mensaje_limpio = self._limpiar_mensaje(mensaje)
        
        # Detectar intención
        intencion, confianza, datos_extraidos = self._detectar_intencion(mensaje_limpio)
        
        # Si no se detecta intención clara, intentar procesamiento más flexible
        if confianza < 0.5:
            return self._procesar_comando_flexible(mensaje_limpio, contexto)
        
        # Generar acción basada en la intención
        if intencion in self.mapeo_acciones:
            accion = self.mapeo_acciones[intencion](datos_extraidos, mensaje_limpio, contexto)
            accion["intencion_detectada"] = intencion
            accion["confianza"] = confianza
            return accion
        
        # Si no hay mapeo, devolver comando por defecto
        return self._generar_accion_por_defecto(mensaje_limpio, contexto)
    
    def _limpiar_mensaje(self, mensaje: str) -> str:
        """Limpia y normaliza el mensaje"""
        # Eliminar @architect o prefijos similares
        mensaje = re.sub(r'^@\w+\s*', '', mensaje)
        # Eliminar espacios múltiples
        mensaje = re.sub(r'\s+', ' ', mensaje)
        # Eliminar caracteres especiales al inicio/final
        mensaje = mensaje.strip(':;,.')
        return mensaje.strip()
    
    def _detectar_intencion(self, mensaje: str) -> Tuple[Optional[str], float, Dict[str, Any]]:
        """Detecta la intención del mensaje y extrae datos relevantes"""
        mejor_intencion = None
        mejor_confianza = 0.0
        mejores_datos = {}
        
        mensaje_lower = mensaje.lower()
        
        for intencion, config in self.intenciones.items():
            # Verificar palabras clave
            palabras_encontradas = sum(1 for palabra in config["palabras_clave"] if palabra in mensaje_lower)
            confianza_palabras = palabras_encontradas / len(config["palabras_clave"]) if config["palabras_clave"] else 0
            
            # Verificar patrones regex
            for patron in config["patrones"]:
                match = re.search(patron, mensaje, re.IGNORECASE | re.DOTALL)
                if match:
                    # Calcular confianza basada en la coincidencia
                    confianza_patron = 0.8  # Base alta por coincidencia de patrón
                    
                    # Extraer datos del match
                    datos = {"grupos": match.groups(), "match_completo": match.group(0)}
                    
                    # Confianza total
                    confianza_total = max(confianza_patron, confianza_palabras)
                    
                    if confianza_total > mejor_confianza:
                        mejor_confianza = confianza_total
                        mejor_intencion = intencion
                        mejores_datos = datos
                        break
            
            # Si no hay match de patrón pero sí palabras clave significativas
            if not mejor_intencion and confianza_palabras > 0.3:
                if confianza_palabras > mejor_confianza:
                    mejor_confianza = confianza_palabras
                    mejor_intencion = intencion
                    mejores_datos = {"mensaje_original": mensaje}
        
        return mejor_intencion, mejor_confianza, mejores_datos
    
    def _procesar_comando_flexible(self, mensaje: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Procesamiento flexible para comandos no reconocidos"""
        # Si parece un comando shell directo
        if self._es_comando_shell(mensaje):
            return {
                "accion": "ejecutar comando",
                "comando": mensaje,
                "contexto": {
                    "directorio_trabajo": contexto.get("workspace", "."),
                    "capturar_salida": True,
                    "timeout": 30
                },
                "procesado_como": "comando_shell_directo"
            }
        
        # Si menciona archivos
        if any(ext in mensaje for ext in ['.py', '.js', '.json', '.txt', '.md', '.yml', '.yaml']):
            if any(palabra in mensaje.lower() for palabra in ['crear', 'nuevo', 'generar']):
                return self._intentar_extraer_crear_archivo(mensaje, contexto)
            elif any(palabra in mensaje.lower() for palabra in ['leer', 'mostrar', 'ver', 'abrir']):
                return self._intentar_extraer_leer_archivo(mensaje, contexto)
        
        # Último recurso: interpretar como solicitud de ejecución
        return {
            "accion": "ejecutar comando",
            "comando": mensaje,
            "contexto": contexto,
            "procesado_como": "comando_interpretado",
            "advertencia": "No se pudo determinar la intención exacta, interpretando como comando a ejecutar"
        }
    
    def _es_comando_shell(self, mensaje: str) -> bool:
        """Determina si el mensaje parece ser un comando shell"""
        comandos_shell = ['ls', 'pwd', 'cd', 'echo', 'cat', 'grep', 'find', 'mkdir', 'rm', 'cp', 'mv', 'npm', 'node', 'python', 'git']
        primer_palabra = mensaje.split()[0].lower() if mensaje.split() else ""
        return primer_palabra in comandos_shell
    
    # Métodos para generar acciones específicas
    
    def _generar_accion_ejecutar(self, datos: Dict[str, Any], mensaje: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Genera acción para ejecutar comando"""
        comando = ""
        if "grupos" in datos and datos["grupos"]:
            comando = datos["grupos"][0] if datos["grupos"][0] else mensaje
        else:
            # Extraer todo después de palabras clave de ejecución
            palabras_exec = ["ejecutar", "ejecuta", "correr", "corre", "run", "execute"]
            for palabra in palabras_exec:
                if palabra in mensaje.lower():
                    idx = mensaje.lower().find(palabra)
                    comando = mensaje[idx + len(palabra):].strip()
                    break
        
        if not comando:
            comando = mensaje
        
        return {
            "accion": "ejecutar comando",
            "comando": comando.strip(),
            "contexto": {
                "directorio_trabajo": contexto.get("workspace", "."),
                "capturar_salida": True,
                "timeout": 30
            }
        }
    
    def _generar_accion_crear_archivo(self, datos: Dict[str, Any], mensaje: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Genera acción para crear archivo"""
        if "grupos" in datos and len(datos["grupos"]) >= 1:
            archivo = datos["grupos"][0]
            contenido = datos["grupos"][1] if len(datos["grupos"]) > 1 and datos["grupos"][1] else ""
            
            # Si no hay contenido, buscar después de ":" o "con"
            if not contenido:
                if ":" in mensaje:
                    contenido = mensaje.split(":", 1)[1].strip()
                elif " con " in mensaje.lower():
                    contenido = mensaje.lower().split(" con ", 1)[1].strip()
            
            return {
                "accion": "crear archivo",
                "ruta": archivo,
                "contenido": contenido,
                "metadatos": {"origen": "procesador_semantico"}
            }
        
        return self._intentar_extraer_crear_archivo(mensaje, contexto)
    
    def _generar_accion_listar(self, datos: Dict[str, Any], mensaje: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Genera acción para listar archivos"""
        directorio = "."
        
        # Buscar directorio específico en el mensaje
        if "grupos" in datos and datos["grupos"] and datos["grupos"][0]:
            directorio = datos["grupos"][0]
        else:
            # Buscar palabras como "en", "de", "del"
            for prep in [" en ", " de ", " del "]:
                if prep in mensaje:
                    partes = mensaje.split(prep)
                    if len(partes) > 1:
                        directorio = partes[-1].strip()
                        break
        
        return {
            "agente": "file_manager",
            "accion": "listar_archivos",
            "parametros": {
                "directorio": directorio,
                "recursivo": "recursiv" in mensaje.lower()
            }
        }
    
    def _generar_accion_leer(self, datos: Dict[str, Any], mensaje: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Genera acción para leer archivo"""
        archivo = ""
        
        if "grupos" in datos and datos["grupos"] and datos["grupos"][0]:
            archivo = datos["grupos"][0]
        else:
            # Buscar archivos por extensión
            palabras = mensaje.split()
            for palabra in palabras:
                if '.' in palabra and any(palabra.endswith(ext) for ext in ['.py', '.js', '.json', '.txt', '.md', '.yml', '.yaml']):
                    archivo = palabra
                    break
        
        if archivo:
            return {
                "agente": "file_manager",
                "accion": "leer_archivo",
                "parametros": {
                    "archivo": archivo
                }
            }
        
        return {
            "error": "No se pudo identificar el archivo a leer",
            "sugerencia": "Por favor especifica el nombre del archivo con su extensión"
        }
    
    def _generar_accion_deploy(self, datos: Dict[str, Any], mensaje: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Genera acción para deploy"""
        stage = "dev"  # Por defecto
        
        # Buscar stage específico
        if "prod" in mensaje.lower() or "production" in mensaje.lower():
            stage = "prod"
        elif "staging" in mensaje.lower():
            stage = "staging"
        
        return {
            "agente": "serverless_deployer",
            "accion": "deploy",
            "parametros": {
                "stage": stage,
                "region": contexto.get("region", "us-east-1")
            }
        }
    
    def _generar_accion_npm(self, datos: Dict[str, Any], mensaje: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Genera acción para comandos npm"""
        comando = "npm install"
        
        # Verificar si se especifica un paquete
        if "grupos" in datos and datos["grupos"] and datos["grupos"][0]:
            paquete = datos["grupos"][0]
            comando = f"npm install {paquete}"
        
        return {
            "accion": "ejecutar comando",
            "comando": comando,
            "contexto": {
                "directorio_trabajo": contexto.get("workspace", "."),
                "capturar_salida": True,
                "timeout": 120  # npm install puede tomar tiempo
            }
        }
    
    def _generar_accion_ayuda(self, datos: Dict[str, Any], mensaje: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Genera respuesta de ayuda"""
        ejemplos = []
        for intencion, config in self.intenciones.items():
            if "ejemplos" in config:
                ejemplos.extend(config["ejemplos"][:2])  # Tomar máximo 2 ejemplos por categoría
        
        return {
            "accion": "mostrar_ayuda",
            "contenido": {
                "mensaje": "Puedo ayudarte con las siguientes tareas:",
                "categorias": list(self.intenciones.keys()),
                "ejemplos": ejemplos,
                "sugerencia": "Simplemente dime qué necesitas hacer en lenguaje natural"
            }
        }
    
    def _generar_accion_por_defecto(self, mensaje: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Genera una acción por defecto cuando no se puede determinar la intención"""
        return {
            "accion": "ejecutar comando",
            "comando": mensaje,
            "contexto": contexto,
            "procesado_como": "comando_por_defecto",
            "nota": "No se pudo determinar una intención específica"
        }
    
    def _intentar_extraer_crear_archivo(self, mensaje: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Intenta extraer información para crear un archivo del mensaje"""
        # Buscar nombre de archivo
        palabras = mensaje.split()
        archivo = None
        contenido = ""
        
        for palabra in palabras:
            if '.' in palabra and any(palabra.endswith(ext) for ext in ['.py', '.js', '.json', '.txt', '.md', '.yml', '.yaml']):
                archivo = palabra
                # Buscar contenido después del nombre del archivo
                idx = mensaje.find(archivo)
                resto = mensaje[idx + len(archivo):].strip()
                if resto.startswith(":"):
                    contenido = resto[1:].strip()
                elif " con " in resto:
                    contenido = resto.split(" con ", 1)[1].strip()
                break
        
        if archivo:
            return {
                "accion": "crear archivo",
                "ruta": archivo,
                "contenido": contenido,
                "metadatos": {"origen": "procesador_semantico", "extraccion": "flexible"}
            }
        
        return {
            "error": "No se pudo determinar el nombre del archivo",
            "sugerencia": "Por favor especifica el nombre del archivo con su extensión, por ejemplo: 'crea archivo test.py'"
        }
    
    def _intentar_extraer_leer_archivo(self, mensaje: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Intenta extraer información para leer un archivo del mensaje"""
        palabras = mensaje.split()
        
        for palabra in palabras:
            if '.' in palabra and any(palabra.endswith(ext) for ext in ['.py', '.js', '.json', '.txt', '.md', '.yml', '.yaml']):
                return {
                    "agente": "file_manager",
                    "accion": "leer_archivo",
                    "parametros": {
                        "archivo": palabra
                    }
                }
        
        return {
            "error": "No se pudo identificar el archivo a leer",
            "sugerencia": "Por favor especifica el nombre del archivo con su extensión"
        }

# Crear instancia global del procesador
procesador_semantico = ProcesadorSemantico()

def procesar_lenguaje_natural(comando: str, contexto: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Función principal para procesar comandos en lenguaje natural"""
    return procesador_semantico.procesar_comando_semantico(comando, contexto)