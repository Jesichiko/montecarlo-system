import os
import csv

class DBOperations:
    def loadDB(cls):
        csv_path = os.path.join(os.path.dirname(__file__), "../../database/results.csv")
        buffer = {}

        # si el archivo no existe retornamos buffer vacio
        if not os.path.exists(csv_path):
            return buffer

        try:
            with open(csv_path, "r", newline="") as file:
                reader = csv.reader(file)
                for row in reader:
                    if row:
                        # primera fila son ips de usuarios
                        user_ip = row[0].strip()
                        results = [float(val.strip()) for val in row[1:] if val.strip()]
                        buffer[user_ip] = {"user": user_ip, "results": results}
        except Exception:
            return {}

        return buffer

    def saveDB(cls, buffer):
        if buffer is None:
            return

        csv_path = os.path.join(os.path.dirname(__file__), "../../database/results.csv")
        # creamos dir si no existe
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)

        with open(csv_path, "w", newline="") as file:
            writer = csv.writer(file)

            # usuario y sus resultados
            for user_ip, data in buffer.items():
                results = data.get("results", [])
                row = [user_ip] + results
                writer.writerow(row)
