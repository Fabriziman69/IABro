# IABro (Jarvis OS Agent)

Estoy desarrollando un asistente local con una interfaz web para conversar por texto o voz y realizar acciones en mi computadora. El proyecto usa Groq para el chat y Whisper para transcribir audio. Incluí dos scripts pequeños para consultar los modelos disponibles en Groq y Gemini.

## Estado actual

El código incluye una interfaz Flask, transcripción con Whisper y herramientas para abrir aplicaciones, ejecutar comandos, controlar teclado y ratón, enfocar ventanas y enviar mensajes mediante la aplicación de WhatsApp. Estas funciones requieren configuración y pruebas en la computadora donde se ejecuten; publicar este repositorio no significa que todas estén verificadas en otros equipos.

## Requisitos y ejecución local

- Windows, Python y acceso a las API que se vayan a utilizar.
- Las dependencias de `requirements.txt`. Whisper descarga el modelo `small` la primera vez que se carga.
- Una clave de Groq para usar el asistente. La clave de Gemini solo se necesita para `test_gemini.py`.

En PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Después, sustituyo los valores de ejemplo en `.env` por mis claves y ejecuto:

```powershell
python app.py
```

La interfaz queda disponible en `http://127.0.0.1:5000/`. El navegador necesita permiso para usar el micrófono si quiero enviar audio.

## Seguridad

El asistente puede ejecutar comandos del sistema y operar otras aplicaciones, incluida la función de enviar mensajes. La interfaz actual no tiene autenticación. Por eso la ejecuto solo en mi equipo y no la expongo a Internet ni a una red compartida. Reviso las acciones que le pido y las respuestas del modelo antes de confiar en ellas.

El archivo `.env` contiene claves privadas y está excluido de Git. `.env.example` solo contiene nombres de variables y valores de ejemplo.
