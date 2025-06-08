# This script receives actions from a RabbitMQ queue
"""Blocking consumer for messages published."""
import pika

HOST  = "beast2024.bangus-city.ts.net"
QUEUE = "pidog-actions"

def callback(ch, method, properties, body):
    print(f" [x] Received {body.decode()}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == "__main__":
    params     = pika.ConnectionParameters(host=HOST)
    connection = pika.BlockingConnection(params)
    channel    = connection.channel()

    channel.queue_declare(queue=QUEUE, durable=True)
    channel.basic_qos(prefetch_count=1)   # fair dispatch
    channel.basic_consume(queue=QUEUE, on_message_callback=callback)

    print(" [*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()