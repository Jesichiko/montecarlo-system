from typing import Dict, List
import ast
import operator as op

operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.USub: lambda x: -x,
}

def safe_eval(expr, variables):
    # reemplazamos ^ con ** para potencia antes de parsear
    expr = expr.replace('^', '**')
    tree = ast.parse(expr, mode="eval")

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.Name):
            if node.id not in variables:
                raise ValueError(f"Variable '{node.id}' no encontrada")
            return variables[node.id]
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in operators:
                raise ValueError(f"Operador {op_type.__name__} no permitido")
            return operators[op_type](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in operators:
                raise ValueError(f"Operador unario {op_type.__name__} no permitido")
            return operators[op_type](_eval(node.operand))
        else:
            raise ValueError(f"Nodo {type(node).__name__} no permitido")

    return _eval(tree)

class FunctionExecuter:
    @staticmethod
    def execute(parsed_function: Dict[str, any], scenario: List[float]):
        variables = parsed_function.get("vars", [])
        expression = parsed_function.get("expression")
        
        print("Escenario:", scenario)
        print("Funcion parseada", parsed_function)
        if len(variables) != len(scenario):
            print(
                f"Error: Tamaño de variables ({len(variables)}) "
                f"no coincide con el tamaño de escenario ({len(scenario)})."
            )
            print(f"Variables: {variables}, Scenario: {scenario}")
            return None

        local_scope = dict(zip(variables, scenario))

        try:
            result = safe_eval(expression, local_scope)
            return result
        except Exception as e:
            print(f"Error evaluando expresion: {e}")
            print(f"Expresion: {expression}")
            print(f"Variables: {local_scope}")
            return None
