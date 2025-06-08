from lib.action_flow import ActionFlow

#import readline # optimize keyboard input, only need to import

import pika
from lib.pidog.pidog import Pidog
from agent_ollama import query_with_langchain
from dotenv import load_dotenv

import time
import threading
import random

import os
import json

# Load environment variables from .env file
load_dotenv()

current_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_path)

input_mode = None
with_img = False
# args = sys.argv[1:]
# if '--keyboard' in args:
#     input_mode = 'keyboard'
# else:
#     input_mode = 'voice'

# if '--camera' in args:
#     with_img = True
# else:
#     with_img = False

# Voice2Text server configuration
TRANSCRIBE_URL = os.getenv("TRANSCRIBE_URL", "http://localhost:5000/transcribe")

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


def action_callback(ch, method, properties, body):
    print(f" [x] Received {body.decode()}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

    # convert the body to a JSON array
    global action_status, actions_to_be_done
    response = body.decode()

    global action_status, actions_to_be_done

    my_dog.rgb_strip.close()
    action_flow.change_status(action_flow.STATUS_SIT)

    action_thread.start()

    try:
        # parse the response
        parsed_response = json.loads(response)
        # parsed_response.actions = parsed_response.get('actions', [])
        # parsed_response.answer = parsed_response.get('answer', '')
        print(f"Parsed response.actions: {parsed_response.actions}")

        response = eval(parsed_response)  # convert JSON string to dict
    except Exception as e:
        print(f"Error parsing response: {e}")
        response = str(response)


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

# RabbitMQ consumer
def start_rabbitmq_consumer(callback):
    load_dotenv()
    USERNAME = os.getenv("RABBITMQ_USERNAME")
    PASSWORD = os.getenv("RABBITMQ_PASSWORD")
    HOST = os.getenv("RABBITMQ_HOST")
    QUEUE = os.getenv("RABBITMQ_QUEUE")

    print("Connecting to RabbitMQ with the following configuration:")
    print(f"Host: {HOST}")
    print(f"Queue: {QUEUE}")
    print(f"Username: {USERNAME}")

    if None in (USERNAME, PASSWORD, HOST, QUEUE):
        raise ValueError("One or more RabbitMQ environment variables are not set. Create a .env file with RABBITMQ_USERNAME, RABBITMQ_PASSWORD, RABBITMQ_HOST, and RABBITMQ_QUEUE.")
    
    credentials = pika.PlainCredentials(USERNAME, PASSWORD)
    params     = pika.ConnectionParameters(host=HOST, credentials=credentials)
    connection = pika.BlockingConnection(params)
    channel    = connection.channel()

    channel.queue_declare(queue=QUEUE, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE, on_message_callback=callback)

    print(" [*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()


if __name__ == "__main__":
    try:
        start_rabbitmq_consumer(action_callback)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\033[31mERROR: {e}\033[m")
    finally:
        my_dog.close()