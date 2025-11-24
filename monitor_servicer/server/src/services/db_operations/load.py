import csv
import os


class loadDB:
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
