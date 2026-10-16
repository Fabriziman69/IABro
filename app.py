from flask import Flask, render_template, request, jsonify
from Agente import procesar_mensaje, historial_global, transcribir_audio_archivo, stats
import os
import uuid

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    texto_usuario = data.get("text", "")
    if not texto_usuario:
        return jsonify({"error": "No text provided"}), 400

    historial_global.append({"role": "user", "content": texto_usuario})
    try:
        respuesta = procesar_mensaje(historial_global)
        return jsonify({"response": respuesta, "stats": stats})
    except Exception as e:
        historial_global.pop() # Revertir si hay error
        if "429" in str(e) or "RateLimitError" in str(e):
            return jsonify({"response": "[!] Límite de la API alcanzado. Espera 30 segundos.", "stats": stats})
        return jsonify({"response": f"[!] Error: {str(e)}", "stats": stats})

@app.route("/audio", methods=["POST"])
def audio():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    archivo_audio = request.files["audio"]
    # Generar un nombre único para evitar colisiones si el usuario presiona el botón varias veces
    nombre_unico = f"temp_audio_{uuid.uuid4().hex}.webm"
    ruta_temp = os.path.join(os.getcwd(), nombre_unico)
    
    archivo_audio.save(ruta_temp)
    
    # Transcribir usando el modelo local
    texto_transcrito = transcribir_audio_archivo(ruta_temp)
    
    if os.path.exists(ruta_temp):
        try:
            os.remove(ruta_temp)
        except Exception:
            pass
        
    if not texto_transcrito:
        return jsonify({"response": "[!] No pude entender el audio.", "stats": stats})

    # Procesar como mensaje normal
    historial_global.append({"role": "user", "content": texto_transcrito})
    try:
        respuesta = procesar_mensaje(historial_global)
        return jsonify({"transcription": texto_transcrito, "response": respuesta, "stats": stats})
    except Exception as e:
        historial_global.pop()
        if "429" in str(e) or "RateLimitError" in str(e):
            return jsonify({"transcription": texto_transcrito, "response": "[!] Límite de la API alcanzado. Espera 30 segundos.", "stats": stats})
        return jsonify({"transcription": texto_transcrito, "response": f"[!] Error: {str(e)}", "stats": stats})

if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=False)
