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
    tree = ast.parse(expr, mode="eval")

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.Name):
            return variables[node.id]
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            return operators[type(node.op)](_eval(node.operand))
        else:
            print(f"Operacion {node} no permitida")
            return None

    return _eval(tree)

class FunctionExecuter:
    @staticmethod
    def execute(parsed_function: Dict[str, any], scenario: List[float]):
        variables = parsed_function.get("vars", [])
        expression = parsed_function.get("expression")

        if len(variables) != len(scenario):
            print(
                f"Error: Tamaño de variables ({
                    len(variables)
                }) no coincide con el tamaño de escenario ({len(scenario)})."
            )
            print(f"Variables: {variables}, Scenario: {scenario}")
            return None

        local_scope = dict(zip(variables, scenario))

        try:
            return safe_eval(expression, local_scope)
        except Exception as e:
            print(f"Error: {e}\nExpresion:({expression})\nVariables:{local_scope}")
            return None
