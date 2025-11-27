from src.protos import function_service_pb2, function_service_pb2_grpc
from src.services.functions_in_file import FileFunctionReader

class FunctionServicer(function_service_pb2_grpc.FunctionServiceServicer):
	def __init__(self, function_reader: FileFunctionReader):
		self.function_reader = function_reader

	def GetFuncModel(self, request, context):
		curr_func = self.function_reader.get_current_func()
		return function_service_pb2.GetFuncModelResponse(function=curr_func)
		
