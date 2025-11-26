from abc import ABC, abstractclassmethod


class FunctionReader(ABC):
    @abstractclassmethod
    def load_functions(source: str): ...

    @abstractclassmethod
    def read_function(): ...

    @abstractclassmethod
    def read_scenario(): ...
