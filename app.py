from flask import Flask, request, jsonify, render_template
import threading
import pyaudio
import wave
import speech_recognition as sr
from pydub import AudioSegment
import re
from googletrans import Translator
from difflib import SequenceMatcher

app = Flask(__name__)

# Variables globales
is_recording = False
stream = None
frames = []

# Parámetros de grabación
RATE = 44100  # Frecuencia de muestreo
CHANNELS = 1  # Mono
SAMPLE_WIDTH = 2  # Tamaño de muestra
FRAMES_PER_BUFFER = 1024  # Tamaño del buffer

def record_audio():
    """Función para grabar el audio."""
    global is_recording, stream, frames

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=CHANNELS, rate=RATE,
                    input=True, frames_per_buffer=FRAMES_PER_BUFFER)

    frames = []
    while is_recording:
        data = stream.read(FRAMES_PER_BUFFER)
        frames.append(data)

    # Finalizar la grabación
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Guardar el archivo de audio
    with wave.open("grabado.wav", 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

def process_audio():
    """Función para procesar y transcribir el audio."""
    try:
        # Normalizar el audio con pydub
        audio = AudioSegment.from_wav("grabado.wav").normalize()
        audio.export("grabado_normalizado.wav", format="wav")

        recognizer = sr.Recognizer()
        with sr.AudioFile('grabado_normalizado.wav') as source:
            audio_data = recognizer.record(source)
            transcripcion = recognizer.recognize_google(audio_data, language='en-US')

        # Procesar el texto transcrito
        resultado = add_question_marks(transcripcion)

        # Traducir y corregir
        translator = Translator()
        translated_to_spanish = translator.translate(resultado, src='en', dest='es').text
        translated_back_to_english = translator.translate(translated_to_spanish, src='es', dest='en').text

        # Comparar diferencias
        percentage_difference, changes = calculate_difference_and_print_changes(
            transcripcion, translated_back_to_english, synonyms_dict={
                "i am": ["im", "i'm"],
                "im": ["i am", "i'm"],
            }
        )

        return {
            "transcripcion": transcripcion,
            "resultado_corregido": resultado,
            "traducido_espanol": translated_to_spanish,
            "traducido_ingles": translated_back_to_english,
            "diferencias": changes,
            "porcentaje_diferencia": f"{percentage_difference:.2f}%"
        }

    except sr.UnknownValueError:
        return {"error": "No se pudo entender el audio."}
    except sr.RequestError as e:
        return {"error": f"Error con el servicio de reconocimiento: {e}"}

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/start', methods=['POST'])
def start():
    global is_recording
    is_recording = True
    threading.Thread(target=record_audio).start()
    return jsonify({"message": "Grabación iniciada."})

@app.route('/stop', methods=['POST'])
def stop():
    global is_recording
    is_recording = False
    return jsonify({"message": "Grabación detenida."})

@app.route('/process', methods=['POST'])
def process():
    result = process_audio()
    return jsonify(result)

# Lógica de procesamiento de texto
def add_question_marks(text):
    # (Implementar tu lógica de `add_question_marks` aquí)
    return text

def calculate_difference_and_print_changes(text1, text2, synonyms_dict):
    # (Implementar tu lógica de diferencias aquí)
    return 0, []

if __name__ == '__main__':
    app.run(debug=True)
