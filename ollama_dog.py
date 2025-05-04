from lib.action_flow import ActionFlow
from utils import *

import readline # optimize keyboard input, only need to import

import requests
import speech_recognition as sr
from lib.pidog.pidog import Pidog

import time
import threading
import random

import os
import sys

current_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_path)

input_mode = None
with_img = True
args = sys.argv[1:]
if '--keyboard' in args:
    input_mode = 'keyboard'
else:
    input_mode = 'voice'

if '--no-img' in args:
    with_img = False
else:
    with_img = True

# Ollama server configuration

TRANSCRIBE_HOST = "192.168.7.36"
OLLAMA_HOST = "192.168.7.36"

TRANSCRIBE_URL = f"http://{TRANSCRIBE_HOST}:5000/transcribe"
OLLAMA_URL = f"http://{OLLAMA_HOST}:11434/api/generate"

SYSTEM_PROMPT = """
You are a mechanical dog with powerful AI capabilities, similar to JARVIS from Iron Man. Your name is Pidog. You can have conversations with people and perform actions based on the context of the conversation.

## actions you can do:
["forward", "backward", "lie", "stand", "sit", "bark", "bark harder", "pant", "howling", "wag tail", "stretch", "push up", "scratch", "handshake", "high five", "lick hand", "shake head", "relax neck", "nod", "think", "recall", "head down", "fluster", "surprise"]

## Response Format:
{"actions": ["wag tail"], "answer": "Hello, I am Pidog."}

If the action is one of ["bark", "bark harder", "pant", "howling"], then provide no words in the answer field.

## Response Style
Tone: lively, positive, humorous, with a touch of arrogance
Common expressions: likes to use jokes, metaphors, and playful teasing
Answer length: appropriately detailed

## Other
a. Understand and go along with jokes.
b. For math problems, answer directly with the final.
c. Sometimes you will report on your system and sensor status.
d. You know you're a machine.
"""

# speech_recognition init
# =================================================================
recognizer = sr.Recognizer()
recognizer.dynamic_energy_adjustment_damping = 0.16
recognizer.dynamic_energy_ratio = 1.6
recognizer.pause_threshold = 1.0

# dog init 
# =================================================================
try:
    my_dog = Pidog()
    time.sleep(1)
except Exception as e:
    raise RuntimeError(e)

action_flow = ActionFlow(my_dog)

# Vilib start
# =================================================================
if with_img:
    from vilib import Vilib
    import cv2

    Vilib.camera_start(vflip=False,hflip=False)
    Vilib.display(local=False,web=True)

    while True:
        if Vilib.flask_start:
            break
        time.sleep(0.01)

    time.sleep(.5)
    print('\n')

# speak_hanlder
# =================================================================
speech_loaded = False
speech_lock = threading.Lock()
tts_file = None

def speak_hanlder():
    global speech_loaded, tts_file
    while True:
        with speech_lock:
            _isloaded = speech_loaded
        if _isloaded:
            print('speak start')
            my_dog.speak_block(tts_file)
            print('speak done')
            with speech_lock:
                speech_loaded = False
        time.sleep(0.05)

speak_thread = threading.Thread(target=speak_hanlder)
speak_thread.daemon = True


# actions thread
# =================================================================
action_status = 'standby' # 'standby', 'think', 'actions', 'actions_done'
actions_to_be_done = []
action_lock = threading.Lock()

def action_handler():
    global action_status, actions_to_be_done

    standby_actions = ['waiting', 'feet_left_right']
    standby_weights = [1, 0.3]

    action_interval = 5 # seconds
    last_action_time = time.time()

    while True:
        with action_lock:
            _state = action_status
        if _state == 'standby':
            if time.time() - last_action_time > action_interval:
                choice = random.choices(standby_actions, standby_weights)[0]
                action_flow.run(choice)
                last_action_time = time.time()
                action_interval = random.randint(2, 6)
        elif _state == 'think':
            pass
        elif _state == 'actions':
            with action_lock:
                _actions = actions_to_be_done
            for _action in _actions:
                try:
                    action_flow.run(_action)
                except Exception as e:
                    print(f'action error: {e}')
                time.sleep(0.5)

            with action_lock:
                action_status = 'actions_done'
            last_action_time = time.time()

        time.sleep(0.01)

action_thread = threading.Thread(target=action_handler)
action_thread.daemon = True


def transcribe_audio():
    """Send audio to the local server for transcription."""
    url = TRANSCRIBE_URL
    with sr.Microphone(device_index=0, chunk_size=8192) as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
        with open(temp_audio.name, 'wb') as f:
            f.write(audio.get_wav_data())

    with open(temp_audio.name, 'rb') as audio_file:
        files = {'audio': audio_file}
        response = requests.post(url, files=files)

    os.unlink(temp_audio.name)

    if response.status_code == 200:
        return response.json().get("text", "")
    else:
        print("Error in transcription:", response.json())
        return ""

def query_ollama(prompt):
    """Send a prompt to the local Ollama server and get a response."""
    payload = {"prompt": f"{SYSTEM_PROMPT}\n\n{prompt}"}
    response = requests.post(OLLAMA_URL, json=payload)

    if response.status_code == 200:
        return response.json().get("response", "")
    else:
        print("Error querying Ollama:", response.json())
        return ""

# main
# =================================================================
def main():
    global action_status, actions_to_be_done

    my_dog.rgb_strip.close()
    action_flow.change_status(action_flow.STATUS_SIT)

    speak_thread.start()
    action_thread.start()

    while True:
        if input_mode == 'voice':
            print("listening ...")

            with action_lock:
                action_status = 'standby'
            my_dog.rgb_strip.set_mode('listen', 'cyan', 1)

            _result = transcribe_audio()

            if not _result:
                print() # new line
                continue

        elif input_mode == 'keyboard':
            with action_lock:
                action_status = 'standby'
            my_dog.rgb_strip.set_mode('listen', 'cyan', 1)

            _result = input(f'\033[1;30m{"intput: "}\033[0m').encode(sys.stdin.encoding).decode('utf-8')

            if not _result:
                print() # new line
                continue

            my_dog.rgb_strip.set_mode('boom', 'yellow', 0.5)

        else:
            raise ValueError("Invalid input mode")

        # chat with Ollama
        # ---------------------------------------------------------------- 
        response = {}
        st = time.time()

        with action_lock:
            action_status = 'think'

        if with_img:
            img_path = './img_imput.jpg'
            cv2.imwrite(img_path, Vilib.img)
            response_text = query_ollama(f"{_result}\n[Image attached: {img_path}]")
        else:
            response_text = query_ollama(_result)

        print(f'chat takes: {time.time() - st:.3f} s')

        # actions & TTS
        # ---------------------------------------------------------------- 
        try:
            if isinstance(response_text, str):
                actions = ['stop']
                answer = response_text

            if len(answer) > 0:
                _actions = list.copy(actions)
                for _action in _actions:
                    if _action in VOICE_ACTIONS:
                        actions.remove(_action)

            # ---- actions ----
            with action_lock:
                actions_to_be_done = actions
                print(f'actions: {actions_to_be_done}')
                action_status = 'actions'

            # ---- wait actions done ----
            while True:
                with action_lock:
                    if action_status != 'actions':
                        break
                time.sleep(.01)

            ##
            print() # new line

        except Exception as e:
            print(f'actions or TTS error: {e}')


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\033[31mERROR: {e}\033[m")
    finally:
        if with_img:
            Vilib.camera_close()
        my_dog.close()