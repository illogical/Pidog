# This script receives actions from a RabbitMQ queue
"""Blocking consumer for messages published."""
import pika
from dotenv import load_dotenv
import os


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

# Example callback function
def my_callback(ch, method, properties, body):
    print(f" [x] Received {body.decode()}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == "__main__":
    start_rabbitmq_consumer(my_callback)