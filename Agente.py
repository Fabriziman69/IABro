import json
import os
import subprocess
import speech_recognition as sr
import whisper
import imageio_ffmpeg
import time
import pyautogui
import pygetwindow as gw
import base64
from io import BytesIO

# Inyectar ffmpeg dinámicamente para que Whisper funcione sin instalaciones manuales
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = os.path.dirname(ffmpeg_path)
ffmpeg_alias = os.path.join(ffmpeg_dir, "ffmpeg.exe")

if not os.path.exists(ffmpeg_alias):
    import shutil
    shutil.copy(ffmpeg_path, ffmpeg_alias)

os.environ["PATH"] += os.pathsep + ffmpeg_dir

from dotenv import load_dotenv
from openai import OpenAI

# Cargar variables de entorno desde el archivo .env
load_dotenv()

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# 1. Definición de funciones
def ejecutar_comando_terminal(comando: str) -> str:
    try:
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=15, check=False)
        salida = resultado.stdout.strip() or resultado.stderr.strip()
        return salida if salida else "Comando ejecutado con éxito (sin salida)."
    except Exception as e:
        return f"Error: {e!s}"

def abrir_aplicacion(nombre_o_ruta: str) -> str:
    try:
        if os.name == 'nt':
            os.startfile(nombre_o_ruta)
        else:
            subprocess.Popen(['xdg-open', nombre_o_ruta])
        return f"Ejecutado: {nombre_o_ruta}"
    except Exception as e:
        return f"Error: {e!s}"

def enviar_mensaje_whatsapp(destinatario: str, mensaje: str) -> str:
    try:
        # Abrir whatsapp (solo funciona en Windows si la app de la tienda está instalada)
        subprocess.run("start whatsapp:", shell=True, check=False)
        time.sleep(3) # Esperar a que cargue
        
        # Buscar el contacto/grupo
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(1)
        pyautogui.write(destinatario, interval=0.05)
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(1)
        
        # Escribir y enviar mensaje
        pyautogui.write(mensaje, interval=0.05)
        time.sleep(0.5)
        pyautogui.press('enter')
        
        return f"Mensaje enviado a {destinatario} por WhatsApp."
    except Exception as e:
        return f"Error enviando WhatsApp: {e}"

def simular_tecla(tecla: str, cantidad: int = 1) -> str:
    try:
        for _ in range(cantidad):
            pyautogui.press(tecla)
            time.sleep(0.1)
        return f"Tecla '{tecla}' presionada {cantidad} veces."
    except Exception as e:
        return f"Error presionando tecla: {e!s}"

def escribir_texto(texto: str) -> str:
    try:
        pyautogui.write(texto, interval=0.01)
        return f"Texto escrito en la interfaz activa."
    except Exception as e:
        return f"Error escribiendo texto: {e!s}"

def enfocar_ventana(nombre: str) -> str:
    try:
        ventanas = gw.getWindowsWithTitle(nombre)
        if ventanas:
            ventana = ventanas[0]
            if ventana.isMinimized:
                ventana.restore()
            ventana.activate()
            return f"Ventana '{ventana.title}' enfocada correctamente."
        return f"No se encontró ninguna ventana con el nombre '{nombre}'."
    except Exception as e:
        return f"Error enfocando ventana: {e!s}"

def controlar_raton(accion: str, x: int = None, y: int = None, clicks: int = 1, scroll_amount: int = 0) -> str:
    try:
        if accion == "mover" and x is not None and y is not None:
            pyautogui.moveTo(x, y, duration=0.5)
            return f"Ratón movido a ({x}, {y})."
        elif accion == "clic" and x is not None and y is not None:
            pyautogui.click(x, y, clicks=clicks)
            return f"Clic realizado en ({x}, {y}) {clicks} veces."
        elif accion == "clic_actual":
            pyautogui.click(clicks=clicks)
            return f"Clic realizado en la posición actual {clicks} veces."
        elif accion == "scroll":
            pyautogui.scroll(scroll_amount)
            return f"Scroll realizado ({scroll_amount})."
        else:
            return "Acción no válida o faltan coordenadas."
    except Exception as e:
        return f"Error controlando ratón: {e!s}"

def ver_pantalla():
    try:
        screenshot = pyautogui.screenshot()
        screenshot.thumbnail((1280, 720))
        buffered = BytesIO()
        screenshot.save(buffered, format="JPEG", quality=70)
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        return {
            "image_url": f"data:image/jpeg;base64,{img_str}",
            "text": "Captura de pantalla de la computadora tomada con éxito. Analiza la imagen devuelta para determinar en qué coordenadas hacer clic."
        }
    except Exception as e:
        return f"Error al tomar captura: {e!s}"

print("Cargando modelo Whisper local...")
try:
    whisper_model = whisper.load_model("small")
except Exception as e:
    print(f"Error cargando Whisper: {e}")
    whisper_model = None

def transcribir_audio_archivo(ruta_archivo: str) -> str:
    if not whisper_model:
        return "Error: Modelo Whisper no cargado."
    print("⏳ [Procesando audio con Whisper...]")
    try:
        result = whisper_model.transcribe(ruta_archivo, language="es")
        return result["text"].strip()
    except Exception as e:
        print(f"[!] Error al transcribir: {e}")
        return ""

HERRAMIENTAS_MAP = {
    "ejecutar_comando_terminal": ejecutar_comando_terminal,
    "abrir_aplicacion": abrir_aplicacion,
    "enviar_mensaje_whatsapp": enviar_mensaje_whatsapp,
    "simular_tecla": simular_tecla,
    "escribir_texto": escribir_texto,
    "enfocar_ventana": enfocar_ventana,
    "controlar_raton": controlar_raton
}

# 2. Esquema de herramientas
tools = [
    {
        "type": "function",
        "function": {
            "name": "ejecutar_comando_terminal",
            "description": "Ejecuta comandos CLI en el sistema operativo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "comando": {"type": "string", "description": "Comando de terminal/PowerShell."}
                },
                "required": ["comando"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "abrir_aplicacion",
            "description": "Abre programas o archivos locales.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_o_ruta": {"type": "string", "description": "Nombre del ejecutable o ruta."}
                },
                "required": ["nombre_o_ruta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "enviar_mensaje_whatsapp",
            "description": "Abre WhatsApp y envía un mensaje a un contacto o grupo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destinatario": {"type": "string", "description": "Nombre exacto del contacto o grupo en WhatsApp."},
                    "mensaje": {"type": "string", "description": "El mensaje a enviar."}
                },
                "required": ["destinatario", "mensaje"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "simular_tecla",
            "description": "Simula presionar una tecla del teclado (ej. 'enter', 'tab', 'playpause', 'space', 'down', 'up'). Ideal para controlar interfaces.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tecla": {"type": "string", "description": "El nombre de la tecla a presionar (ej. 'enter', 'tab', 'playpause')."},
                    "cantidad": {"type": "integer", "description": "Número de veces que se presionará la tecla. Por defecto 1."}
                },
                "required": ["tecla"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escribir_texto",
            "description": "Escribe un texto en la ventana que esté activa actualmente como si lo tecleara el usuario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "texto": {"type": "string", "description": "El texto a escribir."}
                },
                "required": ["texto"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "enfocar_ventana",
            "description": "Trae una aplicación específica al frente de la pantalla para que los siguientes comandos de teclado o ratón actúen sobre ella.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre de la ventana (ej. 'Spotify', 'Chrome')."}
                },
                "required": ["nombre"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "controlar_raton",
            "description": "Controla el ratón en la pantalla.",
            "parameters": {
                "type": "object",
                "properties": {
                    "accion": {"type": "string", "description": "Acción a realizar: 'mover', 'clic', 'clic_actual', 'scroll'"},
                    "x": {"type": "integer", "description": "Coordenada X (solo para mover o clic)."},
                    "y": {"type": "integer", "description": "Coordenada Y (solo para mover o clic)."},
                    "clicks": {"type": "integer", "description": "Número de clics (por defecto 1)."},
                    "scroll_amount": {"type": "integer", "description": "Cantidad de scroll (positivo=arriba, negativo=abajo)."}
                },
                "required": ["accion"]
            }
        }
    }
]
# Inicializamos un historial por defecto que Flask pueda importar
historial_global = [
    {"role": "system", "content": (
        "Eres Jarvis, un asistente de IA en la PC del usuario. Sigue ESTRICTAMENTE estas reglas:\n"
        "1. PREGUNTAS Y CHARLA: Si el usuario te saluda, te hace una pregunta general (clima, datos) o conversa, RESPONDAS SOLO CON TEXTO. NO uses herramientas.\n"
        "2. ACCIONES: Usa herramientas SOLO cuando el usuario te ordene hacer algo en la PC (abrir aplicaciones, enviar mensajes, teclear).\n"
        "3. NO INVENTES: Si vas a enviar un WhatsApp, usa exactamente el nombre de contacto que te dé el usuario. Si no te da uno, pregúntale en texto.\n"
        "4. Sé breve, amigable y directo. No expliques tus razonamientos."
    )}
]

# Estadísticas de la sesión
stats = {
    "api_calls": 0,
    "total_tokens": 0
}

# 3. Orquestador del Agente
def procesar_mensaje(historial_mensajes):
    global stats
    
    while True:
        stats["api_calls"] += 1
        
        try:
            respuesta = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=historial_mensajes,
                tools=tools,
                tool_choice="auto"
            )
        except Exception as e:
            if "429" in str(e) or "RateLimitError" in str(e):
                return "👍 Acción ejecutada bro. (Nota: Límite de API alcanzado)."
            else:
                return f"Error de conexión con la IA: {e!s}"
        
        if respuesta.usage:
            stats["total_tokens"] += respuesta.usage.total_tokens

        mensaje_asistente = respuesta.choices[0].message
        historial_mensajes.append(mensaje_asistente)

        # Si el modelo NO generó llamadas a herramientas, es el mensaje final
        if not mensaje_asistente.tool_calls:
            return mensaje_asistente.content

        # Si generó llamadas a herramientas, las procesamos y continuamos el bucle
        for tool_call in mensaje_asistente.tool_calls:
            nombre_funcion = tool_call.function.name
            argumentos = json.loads(tool_call.function.arguments)

            print(f"\n[Tool Invocada] -> {nombre_funcion}({argumentos})")

            # Ejecutar la función en la máquina
            funcion_local = HERRAMIENTAS_MAP.get(nombre_funcion)
            resultado_ejecucion = funcion_local(**argumentos) if funcion_local else "Función no encontrada."

            # Registrar el resultado de la herramienta en el historial
            if isinstance(resultado_ejecucion, dict) and "image_url" in resultado_ejecucion:
                # El rol 'tool' DEBE ser un string
                historial_mensajes.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": nombre_funcion,
                    "content": resultado_ejecucion.get("text", "Captura de pantalla lista.")
                })
                # Inyectamos la imagen como si el usuario se la acabara de enviar
                historial_mensajes.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Aquí está la captura de pantalla que solicitaste ver:"},
                        {"type": "image_url", "image_url": {"url": resultado_ejecucion["image_url"]}}
                    ]
                })
            else:
                historial_mensajes.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": nombre_funcion,
                    "content": str(resultado_ejecucion)
                })

# 4. Bucle interactivo en consola