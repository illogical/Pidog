# agent_tool.py
#!/usr/bin/env python3
"""
Voice‑controlled OpenAI agent with tooling for robot commands.

Dependencies:
    pip install openai sounddevice soundfile webrtcvad

Requirements:
    - record_whisper.py (from previous script) in the same folder
    - Set your environment variable:
        export OPENAI_API_KEY="your_api_key_here"
"""
import os
import json
import openai
from transcribe import record_until_silence, transcribe_audio

# --- Sample tool function ---------------------------------------------------
def control_robot(direction: str, distance_cm: int) -> str:
    """
    Control the robot's movement. 
    direction: 'forward' | 'backward' | 'left' | 'right'
    distance_cm: distance to move in centimeters.
    Replace the print with actual GPIO calls on Raspberry Pi Zero.
    """
    # TODO: integrate with RPi.GPIO or gpiozero to drive motors
    # Example (pseudo):
    # gpio.move(direction, distance_cm)
    return f"Moving {direction} for {distance_cm} cm."

# --- OpenAI function schema ------------------------------------------------
functions = [
    {
        "name": "control_robot",
        "description": "Move the robot in a specified direction for a given distance",
        "parameters": {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": ["forward", "backward", "left", "right"]
                },
                "distance_cm": {
                    "type": "integer",
                    "description": "Distance in centimeters to move"
                }
            },
            "required": ["direction", "distance_cm"]
        }
    }
]

# --- Agent interaction ------------------------------------------------------
def call_openai_agent(user_text: str) -> str:
    """
    Sends user_text to OpenAI with function definitions. 
    If a function call is returned, executes it and sends the result back.
    Returns assistant's final response.
    """
    openai.api_key = os.getenv("OPENAI_API_KEY")
    # 1. Ask model
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a robot control agent. Use tools to fulfill user commands."},
            {"role": "user", "content": user_text}
        ],
        functions=functions,
        function_call="auto"
    )

    message = response.choices[0].message

    # 2. If model wants to call a tool
    if message.get("function_call"):
        fname = message.function_call.name
        args = json.loads(message.function_call.arguments)

        # Execute the tool
        if fname == "control_robot":
            result = control_robot(**args)
        else:
            result = f"No implementation for {fname}!"

        # 3. Send function result back to model
        followup = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a robot control agent."},
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": None, "function_call": message.function_call},
                {"role": "function", "name": fname, "content": result}
            ]
        )
        return followup.choices[0].message.content

    # Otherwise, return direct assistant reply
    return message.content

# --- Main loop --------------------------------------------------------------
def main():
    print("=== Voice‑controlled Robot Agent ===")
    while True:
        wav_path = record_until_silence(
            filename="command.wav",
            fs=16000,
            aggression=2,
            silence_limit=1.0,
            max_duration=10.0
        )
        user_input = transcribe_audio(wav_path)
        print(f"User said: {user_input}")
        response = call_openai_agent(user_input)
        print(f"Agent: {response}\n")

if __name__ == "__main__":
    main()
