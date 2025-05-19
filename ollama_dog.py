from lib.action_flow import ActionFlow
from audio_recorder import record_audio

import readline # optimize keyboard input, only need to import

import requests
import tempfile
from lib.pidog.pidog import Pidog
from agent_ollama import query_with_langchain

import time
import threading
import random

import os
import sys

current_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_path)

input_mode = None
with_img = False
args = sys.argv[1:]
if '--keyboard' in args:
    input_mode = 'keyboard'
else:
    input_mode = 'voice'

if '--camera' in args:
    with_img = True
else:
    with_img = False

# Ollama server configuration

TRANSCRIBE_HOST = "beast2024"
TRANSCRIBE_URL = f"http://{TRANSCRIBE_HOST}:5000/transcribe"

VOICE_ACTIONS = ["bark", "bark harder", "pant",  "howling"]

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
                print(f'state = "{_state}"')
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


def record_and_transcribe_audio():
    """Record audio and send it for transcription."""
     # Create a temporary file for the recording
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_file.close()

    record_audio(temp_file.name)

    return send_audio_for_transcription(temp_file.name)


def send_audio_for_transcription(audio_file_path):
    """Send audio file to server for transcription."""
    print("Sending audio for transcription...")
    
    url = TRANSCRIBE_URL
    
    with open(audio_file_path, 'rb') as audio_file:
        files = {'audio': audio_file}
        response = requests.post(url, files=files, timeout=15)
    
    if response.status_code == 200:
        result = response.json()
        print("\nTranscription: " + result["text"])
        print(f"Processing time: {result['processing_time']:.2f} seconds")
        return result["text"]
    else:
        print("Transcription error:", response.json())
        return ""

# main
# =================================================================
def wait_for_touch(my_dog):
    """Wait for touch detection before proceeding."""
    print("Waiting for touch to start...")
    my_dog.rgb_strip.set_mode('listen', color='yellow', bps=0.6, brightness=0.8)
    
    while True:
        touch_status = my_dog.dual_touch.read()
        if touch_status != 'N':  # Touch detected
            print("Touch detected! Starting...")
            my_dog.rgb_strip.set_mode('breath', color=[0, 255, 0], bps=1, brightness=0.8)
            time.sleep(1)
            my_dog.rgb_strip.close()
            return True
        time.sleep(0.2)

def main():
    global action_status, actions_to_be_done

    my_dog.rgb_strip.close()
    action_flow.change_status(action_flow.STATUS_SIT)
    
    # Wait for touch before proceeding
    wait_for_touch(my_dog)

    speak_thread.start()
    action_thread.start()

    while True:
        if input_mode == 'voice':
            print("listening ...")
            with action_lock:
                action_status = 'standby'
            my_dog.rgb_strip.set_mode('listen', 'cyan', 1)

            _result = record_and_transcribe_audio()

            if not _result:
                print() # new line
                continue

            # Wait for touch before starting voice recording
            print("Touch to start listening...")
            wait_for_touch(my_dog)

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
            response = query_with_langchain(SYSTEM_PROMPT, f"{_result}\n[Image attached: {img_path}]")
        else:
            print(f"Prompt: {_result}")
            response = query_with_langchain(SYSTEM_PROMPT, _result)


        try:
            response = eval(response) # convert to dict
        except Exception as e:
            response = str(response)

        print(f'chat takes: {time.time() - st:.3f} s')

        # actions & TTS
        # ---------------------------------------------------------------- 
        try:
            if isinstance(response, dict):
                if 'actions' in response:
                    print(f"Response was a dict with actions")
                    actions = list(response['actions'])
                else:
                    print(f"Response was a dict without actions")
                    actions = ['stop']

                if 'answer' in response:
                    answer = response['answer']
                    print(f"Answer: {answer}")
                else:
                    answer = ''

                if len(answer) > 0:
                    _actions = list.copy(actions)
                    for _action in _actions:
                        if _action in VOICE_ACTIONS:
                            actions.remove(_action)
            else:
                response = str(response)
                if len(response) > 0:
                    print(f"Response was a string")
                    actions = ['stop']
                    answer = response

        except:
            actions = ['stop']
            answer = ''
        
        try:

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