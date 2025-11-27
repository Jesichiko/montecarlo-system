import os
import threading
from concurrent import futures
from pprint import pprint

import grpc
from dotenv import load_dotenv
from shared_lib.protos import information_service_pb2_grpc

from src.rabbitmq.connection import Connection
from src.services.db_operations.operations import DBOperations
from src.services.information_servicer import InformationServicer


def run_consumer(
    connection: Connection, ip_results: dict, functions: list, scenarios: dict
):
    # consumir resultados
    for msg in connection.message_stream("results"):
        if not msg:
            continue

        print(f"Mensaje {msg} consumido")
        user_ip = msg.get("user")
        result = msg.get("result")

        ip_results.setdefault(user_ip, {"user": user_ip, "results": []})[
            "results"
        ].append(result)

    # consumir funciones
    for msg in connection.message_stream("functions"):
        if not msg:
            continue

        print(f"Function recibida: {msg}")
        functions.append(msg)
    # actualizar escenarios
    scenarios["value"] = connection.get_amount_scenarios()


def main():
    amount_scenarios = {"value": 0}
    connection = Connection()
    load_dotenv()

    buffer_results, functions = DBOperations().loadDB()
    if buffer_results and functions:
        print("Resultados en cache cargados")
        pprint(buffer_results)
        print("Funciones:", functions)

    # hilo para consumir mensajes de resultados de nuevos usuarios
    consumer_thread = threading.Thread(
        target=run_consumer,
        args=(connection, buffer_results, functions, amount_scenarios),
        daemon=True,
    )

    # publicamos servicio ResultsServicer
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    information_service_pb2_grpc.add_InformationServiceServicer_to_server(
        InformationServicer(
            buffer=buffer_results, functions=functions, scenarios=amount_scenarios
        ),
        server,
    )

    server_address = f"{os.getenv('SERVER_HOST')}:{os.getenv('SERVER_PORT')}"
    server.add_insecure_port(server_address)

    # iniciamos server
    server.start()
    consumer_thread.start()
    print(f"Iniciado server consumidor/cache de resultados en {server_address}")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("Termiando servidor, guardando base de datos")
        DBOperations.saveDB(buffer_results, functions)
        connection.close_connection()
        server.stop(0)


if __name__ == "__main__":
    main()
