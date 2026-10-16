const micBtn = document.getElementById('micBtn');
const pulseRing = document.getElementById('pulseRing');
const statusText = document.getElementById('statusText');
const chatBox = document.getElementById('chatBox');
const textInput = document.getElementById('textInput');
const sendBtn = document.getElementById('sendBtn');
const apiCallsValue = document.getElementById('apiCallsValue');
const tokensValue = document.getElementById('tokensValue');

let isRecording = false;
let mediaRecorder;
let audioChunks = [];

// Variables para detección de silencio
let audioContext;
let analyser;
let microphone;
let silenceTimer = null;
const SILENCE_THRESHOLD = 15; // Sensibilidad al silencio
const SILENCE_DURATION = 1500; // Milisegundos de silencio para cortar

// Enviar texto manualmente
sendBtn.addEventListener('click', () => {
    const text = textInput.value.trim();
    if (text) {
        addMessage(text, 'user');
        textInput.value = '';
        sendTextToServer(text);
    }
});

textInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendBtn.click();
});

// Función para agregar mensajes al chat
function addMessage(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}`;
    msgDiv.innerHTML = `<span class="sender">${sender === 'user' ? 'Tú:' : 'Jarvis:'}</span> ${text}`;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Lógica de grabación de micrófono
micBtn.addEventListener('click', async () => {
    if (!isRecording) {
        startRecording();
    } else {
        stopRecording();
    }
});

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        // Configurar detección de silencio
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        microphone = audioContext.createMediaStreamSource(stream);
        microphone.connect(analyser);
        
        analyser.fftSize = 512;
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            await sendAudioToServer(audioBlob);
            // Apagar micrófono y analizador
            stream.getTracks().forEach(track => track.stop());
            if (audioContext.state !== 'closed') {
                audioContext.close();
            }
        };

        mediaRecorder.start();
        isRecording = true;
        
        // Efectos visuales
        micBtn.classList.add('recording');
        pulseRing.classList.remove('hidden');
        pulseRing.classList.add('recording');
        statusText.textContent = 'Habla... (Se enviará automáticamente)';
        statusText.style.color = '#ef4444';
        
        // Bucle de detección de silencio
        function detectSilence() {
            if (!isRecording) return;
            
            analyser.getByteFrequencyData(dataArray);
            let sum = 0;
            for (let i = 0; i < bufferLength; i++) {
                sum += dataArray[i];
            }
            let average = sum / bufferLength;
            
            if (average < SILENCE_THRESHOLD) {
                if (!silenceTimer) {
                    silenceTimer = setTimeout(() => {
                        if (isRecording) stopRecording();
                    }, SILENCE_DURATION);
                }
            } else {
                if (silenceTimer) {
                    clearTimeout(silenceTimer);
                    silenceTimer = null;
                }
            }
            requestAnimationFrame(detectSilence);
        }
        detectSilence();
        
    } catch (err) {
        console.error("Error accediendo al micrófono:", err);
        alert("No se pudo acceder al micrófono.");
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        
        // Efectos visuales
        micBtn.classList.remove('recording');
        pulseRing.classList.remove('recording');
        statusText.textContent = 'Procesando voz...';
        statusText.style.color = 'var(--primary-color)';
    }
}

// Comunicacion con Flask
async function sendTextToServer(text) {
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });
        const data = await response.json();
        addMessage(data.response, 'system');
        updateStats(data.stats);
    } catch (err) {
        addMessage("Error de conexión con Jarvis.", 'system');
    }
}

async function sendAudioToServer(blob) {
    const formData = new FormData();
    formData.append('audio', blob, 'recording.webm');

    try {
        const response = await fetch('/audio', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.transcription) {
            addMessage(data.transcription, 'user');
        }
        if (data.response) {
            addMessage(data.response, 'system');
        }
        
        updateStats(data.stats);

        // Restaurar estado
        pulseRing.classList.add('hidden');
        statusText.textContent = 'Presiona para hablar';
        statusText.style.color = 'var(--text-muted)';
        
    } catch (err) {
        addMessage("Error procesando el audio.", 'system');
        pulseRing.classList.add('hidden');
        statusText.textContent = 'Presiona para hablar';
        statusText.style.color = 'var(--text-muted)';
    }
}

function updateStats(stats) {
    if (stats) {
        apiCallsValue.textContent = stats.api_calls;
        tokensValue.textContent = stats.total_tokens;
    }
}
