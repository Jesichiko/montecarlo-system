import json
import os
import threading

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from src.rabbitmq.connection import Connection
from src.services.db_operations.load import loadDB
from src.services.db_operations.save import saveDB


def run_consumer(buffer, connection):
    for msg in connection.message_stream("results"):
        if msg is not None:
            user_ip = msg.get("user")

            if user_ip:
                # Si el usuario ya existe, apendizamos los nuevos resultados
                if user_ip in buffer:
                    existing_results = buffer[user_ip].get("results", [])
                    buffer[user_ip]["results"] = existing_results + msg.get(
                        "results", []
                    )
                    return
                buffer[user_ip] = msg


def main():
    load_dotenv()
    connection = Connection()
    buffer_results = loadDB()
    app = FastAPI()

    # endpoints
    @app.get("/results")
    async def users():
        return json.dumps(buffer_results)

    # startup event
    @app.on_event("startup")
    def startup_event():
        t = threading.Thread(
            target=run_consumer, args=(buffer_results, connection), daemon=True
        )
        t.start()

    # shutdown event
    @app.on_event("shutdown")
    def shutdown_event():
        saveDB(buffer_results)
        connection.close_connection()

    # corremos el server dada ip y port en .env
    uvicorn.run(app, host=os.getenv("SERVER_HOST"), port=int(os.getenv("SERVER_PORT")))


if __name__ == "__main__":
    main()
