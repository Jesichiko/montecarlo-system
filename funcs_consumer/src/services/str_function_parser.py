import re
from typing import Dict


class StrFunctionParser:
    @staticmethod
    def parse_function(function_container: Dict[str, str]) -> Dict[str, any] | None:
        function_str = function_container.get("function")
        if not function_str:
            return None

        # regex a capturar:
        # 1. nombre de funcion (f)
        # 2. variables (x,y,z o vacio)
        # 3. expresion a evaluar (x*y*z)
        match = re.match(r"f\((.*?)\)\s*=\s*(.*)", function_str.strip())
        if not match:
            return None  # no se encontro formato valido

        # grupo de variables
        vars_str = match.group(1).strip()
        # separamos variables
        variables = [v.strip() for v in vars_str.split(",") if v.strip()]

        # grupo de expresion (e.g., "x*y*z" or "15")
        expression = match.group(2).strip()

        if variables is None or not expression:
            return None

        return {
            "vars": variables,
            "expression": expression,
        }
