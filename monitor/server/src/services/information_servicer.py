from shared_lib.protos import information_service_pb2, information_service_pb2_grpc


class InformationServicer(information_service_pb2_grpc.InformationServiceServicer):
    def __init__(self, buffer: dict, functions: list, scenarios: dict):
        self.buffer = buffer
        self.functions = functions
        self.scenarios = scenarios

    def GetInformation(self, request, context):
        response = information_service_pb2.GetInformationResponse()

        # agregamos los resultados por usuario
        for user_ip, values in self.buffer.items():
            result_list = response.user_results[user_ip]
            result_list.values.extend(values.get("results", []))

        # agregamos funciones publicadas
        response.published_functions.extend(self.functions)

        # agregamos total de escenarios
        response.total_scenarios = self.scenarios["value"]

        return response
