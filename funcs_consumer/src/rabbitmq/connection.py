import json
import os
import socket

import pika
from dotenv import load_dotenv


class Connection:
    def __init__(self, ip, user, password):
        load_dotenv()
        credentials = pika.PlainCredentials(
            os.getenv("RABBIT_USER"), os.getenv("RABBIT_PWD")
        )
        params = pika.ConnectionParameters(
            host=os.getenv("RABBIT_HOST"), credentials=credentials
        )
        self.connection = pika.BlockingConnection(parameters=params)
        self.channel = self.connection.channel()
        self._user_models_queue = f"{self._get_ip_address()}.models"
        self.channel.queue_declare(queue="results", durable=True)
        self.channel.queue_declare(
            queue=self._user_models_queue, exchange="exchange.models"
        )
        self.channel.queue_declare(queue="scenarios", durable=False)

    # funcion para poder saber nuestra ip (ya que es necesaria para identificar
    # nuestra participacion ante el monitor)
    def _get_ip_address(self):
        try:
            # abrimos un socket, tomamos nuestra ip y cerramos socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "unknown"

    def consume_function(self) -> dict | None:
        for method, properties, body in self.channel.consume(
            queue=self._user_models_queue, inactivity_timeout=None
        ):
            data = json.loads(body.decode())
            yield data
            self.channel.basic_ack(method.delivery_tag)

    def consume_scenario(self) -> dict | None:
        for method, properties, body in self.channel.consume(
            queue="scenarios", inactivity_timeout=None
        ):
            data = json.loads(body.decode())
            yield data
            self.channel.basic_ack(method.delivery_tag)

    def publish_result(self, result: int):
        result_json = json.dumps(result)
        # publicamos el mensaje
        self.channel.basic_publish(
            exchange="",
            routing_key="results",
            body=result_json,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Mensaje persistente
            ),
        )

    def close_connection(self):
        self.connection.close()

