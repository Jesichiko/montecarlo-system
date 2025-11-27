import os
import csv
from typing import Tuple, Dict, List


class DBOperations:
    def __init__(self):
        self.BASE_DIR = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../")
        )
        self.csv_path = os.path.join(self.BASE_DIR, "database", "results.csv")

    def loadDB(self) -> Tuple[Dict, List[str]]:
        user_results = {}
        published_functions = []

        # si el archivo no existe retornamos config default vacia
        if not os.path.exists(self.csv_path):
            return {}, []

        try:
            with open(self.csv_path, "r", newline="") as file:
                reader = csv.reader(file)
                for row in reader:
                    if not row:
                        continue
                    key = row[0].strip()

                    # functions
                    if key == "functions":
                        published_functions = [f.strip() for f in row[1:] if f.strip()]
                        continue

                    # ips y resultados
                    try:
                        results = [float(val.strip()) for val in row[1:] if val.strip()]
                    except ValueError:  # fila con errores (corrupta)
                        continue

                    user_results[key] = {"user": key, "results": results}

        except Exception:
            return {}, []
        return user_results, published_functions

    def saveDB(self, buffer, functions):
        if not buffer or not functions:
            return

        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        with open(self.csv_path, "w", newline="") as file:
            writer = csv.writer(file)

            # ips y resultados
            for user_ip, data in buffer.items():
                row = [user_ip] + data.get("results", [])
                writer.writerow(row)

            # functions
            if functions:
                writer.writerow(["functions"] + functions)
