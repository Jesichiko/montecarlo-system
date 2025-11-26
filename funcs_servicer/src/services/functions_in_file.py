from src.services.interfaces.Function_Reader import FunctionReader
import os


class FileFunctionReader(FunctionReader):
    def __init__(self):
        self.index = -1
        self.stored_functions = []
        self.stored_func_scenarios = []

    def load_functions(self, source_path: str):
        if not os.path.exists(source_path):
            return None

        self.index = -1
        self.stored_functions = []
        self.stored_func_scenarios = []

        with open(source_path, "r") as file:
            for line in file:
                if line.strip():
                    parts = line.rsplit(",", maxsplit=1)
                    if len(parts) == 2:
                        self.stored_functions.append(parts[0].strip())
                        self.stored_func_scenarios.append(parts[1].strip())

    def _advance_index(self) -> int:
        size = len(self.stored_functions)
        if size > 0:
            self.index = (self.index + 1) % size
        return self.index

    def read_function(self) -> str:
        if not self.stored_functions:
            return ""
        self._advance_index()
        return self.stored_functions[self.index]

    def read_scenario(self) -> str:
        if not self.stored_func_scenarios:
            return ""
        return self.stored_func_scenarios[self.index]
