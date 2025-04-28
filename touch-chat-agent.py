''' Touch sensor-triggered ChatGPT agent with voice-to-text support.

Dependencies:
    - Requires `touch-read.py`, `transcribe.py`, and `pidog-agent.py` in the same folder.
    - Ensure the environment variable `OPENAI_API_KEY` is set.
'''

from pidog import Pidog
from transcribe import record_until_silence, transcribe_audio
from pidog_agent import call_openai_agent
import time

def main():
    my_dog = Pidog()
    print("=== Touch-triggered ChatGPT Agent ===")
    print("Touch the left sensor to start recording.")

    touch_active = False  # Flag to track touch state

    while True:
        touch_status = my_dog.dual_touch.read()
        if touch_status == 'L' and not touch_active:  # Trigger only on new touch
            touch_active = True
            print("✓ Left touch detected. Starting voice recording...")
            
            # Record voice input
            wav_path = record_until_silence(
                filename="command.wav",
                fs=16000,
                aggression=2,
                silence_limit=1.0,
                max_duration=10.0
            )
            
            # Transcribe audio to text
            print("→ Transcribing audio...")
            user_input = transcribe_audio(wav_path)
            print(f"User said: {user_input}")
            
            # Send transcribed text to the agent
            print("→ Sending to ChatGPT agent...")
            response = call_openai_agent(user_input)
            print(f"Agent: {response}\n")
        
        elif touch_status != 'L':  # Reset flag when touch is released
            touch_active = False

        time.sleep(0.5)  # Polling interval for touch sensor

if __name__ == "__main__":
    main()
