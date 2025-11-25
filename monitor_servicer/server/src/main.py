import os
import threading
from concurrent import futures

import grpc
from dotenv import load_dotenv
from src.protos import results_service_pb2_grpc
from src.rabbitmq.connection import Connection
from src.services.db_operations.load import loadDB
from src.services.db_operations.save import saveDB
from src.services.results_servicer import ResultsServicer


def run_consumer(buffer, connection):
    for msg in connection.message_stream("results"):
        if msg is not None:
            user_ip = msg.get("user")
            result = msg.get("result")

            if user_ip in buffer:
                buffer[user_ip]["results"].append(result)
            else:
                buffer[user_ip] = {"user": user_ip, "results": [result]}


def main():
    load_dotenv()
    connection = Connection()
    buffer_results = loadDB()

    # hilo para consumir mensajes de resultados de nuevos usuarios
    consumer_thread = threading.Thread(
        target=run_consumer, args=(buffer_results, connection), daemon=True
    )
    consumer_thread.start()

    # publicamos servicio ResultsServicer
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    results_service_pb2_grpc.add_ResultsServiceServicer_to_server(
        ResultsServicer(buffer_results), server
    )

    # iniciamos server
    server_address = f"{os.getenv('SERVER_HOST')}:{os.getenv('SERVER_PORT')}"
    server.add_insecure_port(server_address)
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        saveDB(buffer_results)
        connection.close_connection()
        server.stop(0)


if __name__ == "__main__":
    main()
