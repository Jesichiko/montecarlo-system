from src.rabbitmq.connection import Connection
from src.services.function_executer import FunctionExecuter
from src.services.str_function_parser import StrFunctionParser
import threading


def consume_function(function_container: dict):
    connection = Connection()
    for msg in connection.consume_function():
        if not msg:
            continue
        print(f"funcion consumida: {msg}")
        function_container["function"] = msg


def consume_scenario(buffer_scenario: list):
    connection = Connection()
    for msg in connection.consume_scenario():
        if not msg:
            continue
        print(f"Escenario consumioo: {msg}")
        buffer_scenario.clear()
        buffer_scenario.extend(buffer_scenario)


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
    function = {"function": None}
    scenario = []

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
