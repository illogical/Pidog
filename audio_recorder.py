import pyaudio
import wave
import audioop
import webrtcvad
import collections
import contextlib
import sys

# Audio recording parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
# WebRTC VAD requires specific sample rates: 8000, 16000, 32000, or 48000 Hz
RATE = 16000  # Changed from 44100 to be compatible with WebRTC VAD
CHUNK_DURATION_MS = 30  # Frame duration in milliseconds (10, 20, or 30 ms)
CHUNK_SIZE = int(RATE * CHUNK_DURATION_MS / 1000)  # Chunk size in frames
MAX_RECORD_SECONDS = 10  # Increased maximum recording time to 10 seconds

# WebRTC VAD configuration
VAD_AGGRESSIVENESS = 2  # Aggressiveness mode (0-3, 3 is most aggressive)
SILENCE_TIMEOUT = 1.0  # Seconds of silence before stopping
SILENCE_CHUNKS = int(SILENCE_TIMEOUT * 1000 / CHUNK_DURATION_MS)  # Number of silent chunks before stopping

def record_audio(output_filename):
    """Record audio from microphone and stop on silence using WebRTC VAD."""
    # Initialize PyAudio
    print("Initializing audio recording...")
    audio = pyaudio.PyAudio()
    
    # Open microphone stream with WebRTC-compatible parameters
    print("Opening audio stream...")
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
        start=False
    )
    
    # Initialize WebRTC VAD
    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
    
    print("Recording... (speak now, will stop after silence is detected)")
    frames = []
    ring_buffer = collections.deque(maxlen=SILENCE_CHUNKS)
    
    # Variables for voice activity detection
    num_silent_chunks = 0
    sound_started = False
    max_chunks = int((RATE * MAX_RECORD_SECONDS) / CHUNK_SIZE)
    
    # Start the stream
    stream.start_stream()
    
    try:
        for i in range(max_chunks):
            # Read audio chunk
            chunk = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            frames.append(chunk)
            
            # Check if this chunk contains speech
            is_speech = vad.is_speech(chunk, RATE)
            
            # Update ring buffer with speech status
            ring_buffer.append(1 if is_speech else 0)
            
            # Check if we've detected speech in the recent past
            recent_speech = sum(ring_buffer) > 0
            
            # State machine for detecting speech and silence
            if recent_speech:
                sound_started = True
                num_silent_chunks = 0
            elif sound_started:
                num_silent_chunks += 1
                if num_silent_chunks >= SILENCE_CHUNKS:
                    print("Silence detected, stopping recording.")
                    break
            
            # Print progress
            sys.stdout.write('.' if is_speech else '-')
            sys.stdout.flush()
        
        # If we reached max recording time
        if i >= max_chunks - 1:
            print(f"\nMaximum recording time ({MAX_RECORD_SECONDS}s) reached.")
        elif sound_started:
            print("\nFinished recording.")
        else:
            print("\nNo speech detected.")
            return False
            
    except KeyboardInterrupt:
        print("\nRecording interrupted by user.")
    finally:
        # Always clean up
        with contextlib.ExitStack() as stack:
            stack.callback(print, "\nCleaning up...")
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
    return True