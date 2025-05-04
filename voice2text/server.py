# voice2text/server.py
# This is a simple Flask server that uses OpenAI's Whisper model to transcribe audio files.
from flask import Flask, request, jsonify
import whisper
import tempfile
import os
import time
from pydub import AudioSegment
import threading

app = Flask(__name__)

# Get model name from environment variable or use "base" as default
# Options: tiny, base, small, medium, large
MODEL_NAME = os.environ.get("WHISPER_MODEL", "large")

# Load the Whisper model
print(f"Loading Whisper model: {MODEL_NAME}")
model = whisper.load_model(MODEL_NAME)
print("Model loaded successfully!")

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files['audio']
    
    # Save the uploaded file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
        audio_file.save(temp_audio.name)
        temp_audio_path = temp_audio.name
    
    try:
        # Transcribe with Whisper
        start_time = time.time()
        result = model.transcribe(temp_audio_path)
        processing_time = time.time() - start_time
        
        return jsonify({
            "text": result["text"],
            "processing_time": processing_time
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temporary file
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

@app.route('/healthcheck', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok", 
        "model": f"Whisper {MODEL_NAME}"
    })

@app.route('/', methods=['GET'])
def index():
    return """
    <html>
        <head>
            <title>Whisper Voice-to-Text Server</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #333; }
                code { background-color: #f4f4f4; padding: 2px 5px; border-radius: 3px; }
                pre { background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }
            </style>
        </head>
        <body>
            <h1>Whisper Voice-to-Text Server</h1>
            <p>This server provides speech-to-text conversion using OpenAI's Whisper model.</p>
            <h2>API Endpoints:</h2>
            <ul>
                <li><code>POST /transcribe</code> - Submit an audio file for transcription</li>
                <li><code>GET /healthcheck</code> - Check server status</li>
            </ul>
            <h2>Example curl command:</h2>
            <pre>curl -X POST -F "audio=@your-audio-file.wav" http://localhost:5000/transcribe</pre>
            <p>Currently running model: <strong>""" + MODEL_NAME + """</strong></p>
        </body>
    </html>
    """

if __name__ == '__main__':
    # Run the application on all network interfaces (0.0.0.0)
    # This makes it accessible from other devices on the network
    app.run(host='0.0.0.0', port=5000, debug=False)