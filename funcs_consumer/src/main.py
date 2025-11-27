import os
import threading

from dotenv import load_dotenv

from google.protobuf import empty_pb2
from src.protos import function_service_pb2_grpc
from src.rabbitmq.connection import Connection
from src.services.function_executer import FunctionExecuter
from src.services.str_function_parser import StrFunctionParser
import grpc


def consume_function(function_container: dict):
    connection = Connection()
    for msg in connection.consume_function():
        if not msg:
            continue

        print(f"Funcion consumida: {msg}")
        function_container["function"] = msg


def consume_scenario(buffer_scenario: list):
    connection = Connection()
    for msg in connection.consume_scenario():
        if not msg:
            continue

        print(f"Escenario consumido: {msg}")
        buffer_scenario.clear()
        buffer_scenario.extend(msg)


def produce_result(function_container: dict, buffer_scenario: list):
    connection = Connection
    if not function_container or not buffer_scenario:
        return  # no mandamos resultados vacios ya que no tenemos info

    parsed_function = StrFunctionParser.parse_function(function_container)
    if not parsed_function:
        return

    result = FunctionExecuter.execute(parsed_function, buffer_scenario)
    if result:
        connection.publish_result(result)


def main():
    load_dotenv()
    server_address = f"{os.getenv('SERVER_HOST')}:{os.getenv('SERVER_PORT')}"
    function = {"function": None}
    scenario = []

    # usamos gRPC para llamar por primera vez la funcion/modelo cargado actualmente
    try:
        with grpc.insecure_channel(server_address) as channel:
            stub = function_service_pb2_grpc.FunctionServiceStub(channel)
            response = stub.GetFuncModel(empty_pb2.Empty())
            if response:
                function["function"] = response.function
    except Exception as e:
        print(f"Error: {e}")

    functions_thread = threading.Thread(
        target=consume_function, args=(function,), daemon=True
    )

    scenarios_thread = threading.Thread(
        target=consume_scenario, args=(scenario,), daemon=True
    )

    producer_thread = threading.Thread(
        target=produce_result, args=(function, scenario), daemon=True
    )

    functions_thread.start()
    scenarios_thread.start()
    producer_thread.start()
    print("Cliente consumidor de modelos/scenarios y productor de resultados iniciado")


if __name__ == "__main__":
    main()
