from dotenv import load_dotenv
import os
import pika
import json


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
        # cola de escenarios
        self.channel.queue_declare(queue="scenarios", durable=False)
        # exchange para publicar funciones (fanout)
        self.channel.exchange_declare(
            exchange="exchange.models", exchange_type="fanout", durable=True
        )

    def public_function(self, function: str):
        function_json = json.dumps(function)
        self.channel.basic_publish(  # todos los clientes con colas enlazadas recibiran el mensaje
            exchange="exchange.models",
            routing_key="",  # fanout ignora routing_key
            body=function_json,
        )

        # eliminamos todos los escenarios al publicar una nueva func
        self.channel.queue_purge(queue="scenarios")

    def public_scenario(self, scenario: list[float]):
        scenario_json = json.dumps(scenario)
        self.channel.basic_publish(
            exchange="",
            routing_key="scenarios",
            body=scenario_json,
            properties=pika.BasicProperties(delivery_mode=1),
        )

    def close_connection(self):
        self.connection.close()
