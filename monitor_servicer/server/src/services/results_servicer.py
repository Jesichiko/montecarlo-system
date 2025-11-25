from protos import results_service_pb2, results_service_pb2_grpc


class ResultsServicer(results_service_pb2_grpc.ResultsServiceServicer):
    def __init__(self, buffer: dict):
        self.buffer = buffer

    def GetResults(self, request, context):
        response = results_service_pb2.GetResultsResponse()

        for user_ip, values in self.buffer.items():
            result_list = response.results[user_ip]
            result_list.values.extend(values.get("results", []))
        return response
