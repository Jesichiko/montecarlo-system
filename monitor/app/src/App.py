import os
import threading
import customtkinter as ctk
from dotenv import load_dotenv
import grpc
from google.protobuf import empty_pb2
from shared_lib.protos import results_service_pb2_grpc
from src.client_card import ClientCard

class NetworkMonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Monitor de resultados")
        self.geometry("1400x900")

        # tema oscuro
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # estado
        self.monitoring = False
        self.monitor_thread = None
        self.results_data = {}
        self.connection_error = False

        # estructuras para manejar las cards sin destruirlas
        # client_cards: ip -> ClientCard
        self.client_cards = {}
        # card_order: lista de ips en el orden en que se mostraron las cards
        # sirve para calcular posicion en grid y mantener estabilidad visual
        self.card_order = []

        # variables de entorno
        load_dotenv()

        # UI
        self.create_ui()

    def show_error_dialog(self, title, message):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("450x220")
        dialog.configure(fg_color="#1E1E1E")
        dialog.resizable(False, False)

        # Centrar el dialogo
        dialog.transient(self)
        dialog.grab_set()

        # Contenido
        content_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # Mensaje
        ctk.CTkLabel(
            content_frame,
            text=message,
            font=("Roboto", 13),
            text_color="#F5F5F5",
            wraplength=390,
        ).pack(pady=(0, 20))

        # Boton OK
        ctk.CTkButton(
            content_frame,
            text="OK",
            fg_color="#E74C3C",
            hover_color="#cc3333",
            command=dialog.destroy,
            width=100,
        ).pack()

    def create_ui(self):
        # header
        header_frame = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)

        # contenedor para titulo y boton
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(fill="x", padx=40, pady=15)

        # titulo
        title_label = ctk.CTkLabel(
            header_content,
            text="Monitoreo de Resultados",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#F5F5F5",
        )
        title_label.pack(side="left")

        # boton de inicio de monitoreo
        self.monitor_button = ctk.CTkButton(
            header_content,
            text="Iniciar Monitoreo",
            command=self.toggle_monitoring,
            fg_color="#2ECC71",
            hover_color="#27AE60",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=150,
            height=40,
            corner_radius=8,
        )
        self.monitor_button.pack(side="right")

        # contenedor principal con scroll
        main_container = ctk.CTkFrame(self, fg_color="#1E1E1E")
        main_container.pack(fill="both", expand=True, padx=40, pady=20)

        # ScrollableFrame para las tarjetas
        # usamos colores hex validos (sin alpha)
        self.scrollable_frame = ctk.CTkScrollableFrame(
            main_container,
            fg_color="transparent",
            scrollbar_button_color="#3A3A3A",
            scrollbar_button_hover_color="#4A4A4A",
        )
        self.scrollable_frame.pack(fill="both", expand=True)

        # grid para las tarjetas: 4 columnas fijas
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(1, weight=1)
        self.scrollable_frame.grid_columnconfigure(2, weight=1)
        self.scrollable_frame.grid_columnconfigure(3, weight=1)

        # frame para las tarjetas (dinamico) -> usamos el propio scrollable_frame
        self.cards_container = self.scrollable_frame

    def create_card(self, ip_address, ports, color, row, col):
        """
        Crea una nueva ClientCard y la coloca en la grid segun row/col.
        Esta funcion NO debe llamarse si ya existe la card para esa ip.
        """
        card = ClientCard(self.cards_container, ip_address, ports, color=color)
        # colocamos usando grid para respetar la estructura de 4 columnas
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        return card

    def update_cards(self):
        """
        Actualiza las cards sin destruir las ya existentes.
        - Si la ip ya existe: solo actualiza sus valores (card.update_values)
        - Si la ip no existe: crea una nueva card y la inserta en la siguiente posicion
        - NO se eliminan cards cuando una ip deja de aparecer (si quieres eliminar,
          puedo agregar esa opcion)
        """
        # si hay error de conexion mostramos mensaje y no actualizamos cards
        if self.connection_error:
            # limpiamos el area de datos si queremos mostrar solo el mensaje de error
            # pero no destruimos las cards ya existentes para mantener estado
            # mostramos el label de error encima de las cards
            error_label = ctk.CTkLabel(
                self.cards_container,
                text="Error de conexion con el servidor\n\nNo se pueden obtener los resultados",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="#E74C3C",
            )
            # colocamos el mensaje al principio
            error_label.grid(row=0, column=0, columnspan=4, pady=100)
            # no retornamos inmediatamente para permitir que cards previas sigan visibles
            return

        # colores para las tarjetas (misma paleta que tenias)
        colors = ["#2ECC71", "#FF8C00", "#9B59B6", "#F1C40F", "#E74C3C", "#1ABC9C"]

        # recorremos los resultados nuevos y actualizamos o creamos cards
        for idx, (ip_address, data) in enumerate(self.results_data.items()):
            ports = [int(val) for val in data.get("values", [])]

            if ip_address in self.client_cards:
                # si ya existe, solo actualizamos los valores
                card = self.client_cards[ip_address]
                try:
                    card.update_values(ports)
                except Exception as e:
                    # por seguridad, si falla la actualizacion intentamos recrear la card
                    print(f"Error actualizando card {ip_address}: {e}")
                    # quitar de estructuras y recrear abajo
                    try:
                        # ubicacion anterior en card_order se mantiene; reemplazamos objeto
                        index = self.card_order.index(ip_address)
                    except ValueError:
                        index = None
                    if index is not None:
                        row = index // 4
                        col = index % 4
                    else:
                        # si no estaba en orden, lo agregamos al final
                        index = len(self.card_order)
                        self.card_order.append(ip_address)
                        row = index // 4
                        col = index % 4

                    new_color = colors[len(self.card_order) % len(colors)]
                    new_card = self.create_card(ip_address, ports, new_color, row, col)
                    self.client_cards[ip_address] = new_card

            else:
                # nueva ip: asignar posicion estable usando card_order
                insert_index = len(self.card_order)
                self.card_order.append(ip_address)
                row = insert_index // 4
                col = insert_index % 4
                color = colors[insert_index % len(colors)]

                new_card = self.create_card(ip_address, ports, color, row, col)
                self.client_cards[ip_address] = new_card

        # NOTA: No eliminamos cards de ips que ya no aparecen en results_data.
        # Si quieres que se eliminen automaticamente, dime y agrego la logica
        # para destruir y reordenar self.card_order y self.client_cards.

    def toggle_monitoring(self):
        if not self.monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def start_monitoring(self):
        self.monitoring = True
        self.connection_error = False
        self.monitor_button.configure(
            text="Detener Monitoreo", fg_color="#E74C3C", hover_color="#C0392B"
        )

        # iniciamos thread de monitoreo
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        self.monitoring = False
        self.monitor_button.configure(
            text="Iniciar Monitoreo", fg_color="#2ECC71", hover_color="#27AE60"
        )

    def monitor_loop(self):
        server_address = f"{os.getenv('SERVER_HOST')}:{os.getenv('SERVER_PORT')}"

        while self.monitoring:
            try:
                with grpc.insecure_channel(server_address) as channel:
                    stub = results_service_pb2_grpc.ResultsServiceStub(channel)

                    response = stub.GetResults(empty_pb2.Empty())
                    new_data = {}
                    for ip_address, result_list in response.results.items():
                        new_data[ip_address] = {"values": list(result_list.values)}

                    # actualizamos la estructura compartida y pedimos refrescar UI
                    self.results_data = new_data
                    self.connection_error = False
                    self.after(0, self.update_cards)

            except grpc.RpcError as e:
                print(f"Error gRPC: {e}")
                self.connection_error = True
                self.monitoring = False

                error_msg = (
                    f"No se puede conectar al servidor gRPC en {server_address}\n\n"
                )

                if e.code() == grpc.StatusCode.UNAVAILABLE:
                    error_msg += "El servidor no esta disponible o no esta ejecutandose"
                elif e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                    error_msg += "Tiempo de espera agotado al conectar"
                else:
                    error_msg += f"Error: {e.details()}"

                self.after(0, self.update_cards)
                self.after(
                    0,
                    lambda: self.show_error_dialog("Error de Conexion gRPC", error_msg),
                )

                # Detener monitoreo y cambiar boton a rojo
                self.after(
                    0,
                    lambda: self.monitor_button.configure(
                        text="Iniciar Monitoreo",
                        fg_color="#E74C3C",
                        hover_color="#C0392B",
                    ),
                )
                break

            except Exception as e:
                print(f"Error inesperado: {e}")
                self.connection_error = True
                self.monitoring = False

                self.after(0, self.update_cards)
                self.after(
                    0,
                    lambda err=e: self.show_error_dialog(
                        "Error Inesperado", f"{str(err)}"
                    ),
                )
                self.after(
                    0,
                    lambda: self.monitor_button.configure(
                        text="Iniciar Monitoreo",
                        fg_color="#E74C3C",
                        hover_color="#C0392B",
                    ),
                )
                break

            # cada segundo actualizamos la UI
            threading.Event().wait(1)

    def on_closing(self):
        self.stop_monitoring()
        self.destroy()


def main():
    app = NetworkMonitorApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
