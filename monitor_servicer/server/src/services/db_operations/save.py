import csv
import os


class saveDB:
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
