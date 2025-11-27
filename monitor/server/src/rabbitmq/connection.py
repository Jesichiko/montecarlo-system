import json
import os

import pika
from dotenv import load_dotenv


class Connection:
    def __init__(self):
        load_dotenv()
        credentials = pika.PlainCredentials(
            os.getenv("RABBIT_USER"), os.getenv("RABBIT_PWD")
        )
        params = pika.ConnectionParameters(
            host=os.getenv("RABBIT_HOST"), credentials=credentials
        )
        self.connection = pika.BlockingConnection(parameters=params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue="results", durable=True)
        self.channel.queue_declare(queue="scenarios", durable=False)
        self.channel.queue_declare(queue="functions", durable=True)
        # bindeamos cola functions con el exchange fanout
        self.channel.queue_bind(queue="functions", exchange="exchange.models")

    # definimos un iterador consumer de pika que devuelve constantemente
    # mensajes empujados por el broker rabbitmq
    # como un "flujo" constante de mensajes
    def message_stream(self, consume_queue: str) -> dict | None:
        # si todavia no hay conexion o canal no se puede comunicar
        if self.connection is None or self.channel is None:
            return None

        for method, properties, body in self.channel.consume(
            queue=consume_queue, inactivity_timeout=None
        ):
            data = json.loads(body.decode())
            yield data
            self.channel.basic_ack(method.delivery_tag)

    def get_amount_scenarios(self) -> int:
        res = self.channel.queue_declare(queue="scenarios", durable=False, passive=True)
        return res.method.message_count

    def close_connection(self):
        self.connection.close()
