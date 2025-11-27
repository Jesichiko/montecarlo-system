import os
import threading
from time import sleep

from dotenv import load_dotenv
import grpc
from google.protobuf import empty_pb2

from src.protos import function_service_pb2_grpc
from src.rabbitmq.connection import Connection
from src.services.function_executer import FunctionExecuter
from src.services.str_function_parser import StrFunctionParser


def consume_function(
    function_container: dict, lock: threading.Lock, new_data_event: threading.Event
):
    connection = Connection()
    for msg in connection.consume_function():
        if not msg:
            continue

        with lock:
            old_func = function_container.get("function")
            if msg != old_func:
                print(f"Nueva funcion consumida: {msg}")
                function_container["function"] = msg
                # Señalar que hay nueva funcion
                new_data_event.set()


def consume_scenario(
    buffer_scenario: list, lock: threading.Lock, new_data_event: threading.Event
):
    connection = Connection()
    for msg in connection.consume_scenario():
        if not msg:
            continue

        with lock:
            # Comparar si es diferente al anterior
            if msg != buffer_scenario:
                print(f"Nuevo escenario consumido: {msg}")
                buffer_scenario.clear()
                buffer_scenario.extend(msg)
                # Señalar que hay nuevo escenario
                new_data_event.set()


def produce_result(
    function_container: dict,
    buffer_scenario: list,
    lock: threading.Lock,
    new_data_event: threading.Event,
):
    connection = Connection()
    last_function = None
    last_scenario = None

    while True:
        # Esperar hasta que haya nueva funcion o nuevo escenario
        new_data_event.wait()
        new_data_event.clear()  # Resetear el evento

        with lock:
            current_function = function_container.get("function")
            current_scenario = buffer_scenario.copy() if buffer_scenario else None

            # Verificar si son los mismos datos que ya procesamos
            if current_function == last_function and current_scenario == last_scenario:
                continue

            # Parsear la funcion
            parsed_function = StrFunctionParser.parse_function(function_container)
            if not parsed_function:
                continue

            # Ejecutar la funcion
            result = FunctionExecuter.execute(parsed_function, current_scenario)

        # Publicar resultado fuera del lock
        if result is not None:
            print(f"[RESULTADO] Generado: {result:.6f}")
            print(f"  Función: {current_function}")
            print(f"  Escenario: {[round(x, 3) for x in current_scenario]}")

            try:
                connection.publish_result(result)
                # Actualizar lo ultimo procesado
                last_function = current_function
                last_scenario = current_scenario
            except Exception as e:
                print(f"ERROR, No se pudo publicar resultado: {e}")
                # Intentar reconectar
                try:
                    connection = Connection()
                except Exception as reconnect_error:
                    print(f"ERROR, No se pudo reconectar: {reconnect_error}")

        sleep(0.1)


def main():
    load_dotenv()
    server_address = f"{os.getenv('SERVER_HOST')}:{os.getenv('SERVER_PORT')}"

    function = {"function": None}
    scenario = []
    lock = threading.Lock()

    # Evento para señalar cuando hay nueva funcion o escenario
    new_data_event = threading.Event()

    # obtenemos la funcion actual via gRPC
    try:
        with grpc.insecure_channel(server_address) as channel:
            stub = function_service_pb2_grpc.FunctionServiceStub(channel)
            response = stub.GetFuncModel(empty_pb2.Empty())
            if response and response.function:
                with lock:
                    function["function"] = response.function
                print(f"Funcion inicial obtenida: {response.function}")
    except Exception as e:
        print(f"No se pudo obtener funcion via gRPC: {e}")

    # Threads para consumir funcion y escenarios
    functions_thread = threading.Thread(
        target=consume_function, args=(function, lock, new_data_event), daemon=True
    )

    scenarios_thread = threading.Thread(
        target=consume_scenario, args=(scenario, lock, new_data_event), daemon=True
    )

    producer_thread = threading.Thread(
        target=produce_result,
        args=(function, scenario, lock, new_data_event),
        daemon=True,
    )

    # Iniciar threads
    functions_thread.start()
    scenarios_thread.start()
    producer_thread.start()

    try:
        print("Cliente consumidor iniciado")

        while True:
            sleep(10)
            with lock:
                func = function.get("function", "Esperando...")
                scen = scenario if scenario else "Esperando..."
            print(f"[ESTADO] Funcion: {func}")
            print(f"[ESTADO] Escenario: {scen}")

    except KeyboardInterrupt:
        print("\nCliente detenido por el usuario")


if __name__ == "__main__":
    main()
