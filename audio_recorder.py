import pyaudio
import wave
import audioop

# Audio recording parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 4096
MAX_RECORD_SECONDS = 6  # Maximum recording time as a safety limit
SILENCE_THRESHOLD = 300  # Adjust based on your microphone and environment
SILENCE_CHUNKS = 5  # Number of consecutive silent chunks to stop recording (30 chunks @ 1028 ≈ 1.5 seconds)

def record_audio(output_filename):
    """Record audio from microphone and stop on silence."""
    # Initialize PyAudio
    print("Initializing audio recording...")
    audio = pyaudio.PyAudio()
    
    # Open microphone stream
    print("Opening audio stream...")
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    
    print("Recording... (will stop automatically after silence is detected)")
    frames = []
    
    # Variables for silence detection
    silent_chunks = 0
    sound_started = False
    
    # Record audio in chunks until silence is detected or max time reached
    max_chunks = int(RATE / CHUNK * MAX_RECORD_SECONDS)
    
    for i in range(max_chunks):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        
        # Calculate audio level (RMS)
        rms = audioop.rms(data, 2)  # width=2 for FORMAT=paInt16
        
        # If we detect sound above threshold
        if rms > SILENCE_THRESHOLD:
            silent_chunks = 0
            sound_started = True
        # If we detect silence after sound has started
        elif sound_started:
            silent_chunks += 1
            if silent_chunks >= SILENCE_CHUNKS:
                print("Silence detected, stopping recording.")
                break
    
    # If we reached max recording time
    if i >= max_chunks - 1:
        print(f"Maximum recording time ({MAX_RECORD_SECONDS}s) reached.")
    
    print("Recording finished.")
    
    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    print("Processing audio...")

    # Save the recorded audio as WAV file
    with wave.open(output_filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    print(f"Audio saved to {output_filename}")