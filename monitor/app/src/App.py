import os
import threading
from collections import deque
from datetime import datetime
import customtkinter as ctk
from dotenv import load_dotenv
import grpc
from google.protobuf import empty_pb2
from shared_lib.protos import information_service_pb2_grpc
from src.client_card import ClientCard
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class NetworkMonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Monitor de Red - Tiempo Real")
        self.geometry("1600x1000")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Estado
        self.monitoring = False
        self.monitor_thread = None
        self.user_results_data = {}
        self.published_functions = set()  # Cambio a set para evitar duplicados
        self.total_scenarios = 0
        self.connection_error = False

        # Estructuras para las cards
        self.client_cards = {}
        self.card_order = []

        # Datos históricos para graficas
        self.scenarios_history = deque(maxlen=20)
        self.time_labels = deque(maxlen=20)
        self.global_average_history = deque(maxlen=20)
        
        # Variables de entorno
        load_dotenv()

        # UI
        self.create_ui()

    def show_error_dialog(self, title, message):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("500x250")
        dialog.configure(fg_color="#1E1E1E")
        dialog.resizable(False, False)

        # Centrar el dialogo
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (250 // 2)
        dialog.geometry(f"500x250+{x}+{y}")

        dialog.transient(self)
        dialog.grab_set()

        content_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # Texto con wrapping adecuado
        message_label = ctk.CTkLabel(
            content_frame,
            text=message,
            font=("Roboto", 13),
            text_color="#F5F5F5",
            wraplength=440,
            justify="left"
        )
        message_label.pack(pady=(0, 20), fill="both", expand=True)

        ctk.CTkButton(
            content_frame,
            text="OK",
            fg_color="#E74C3C",
            hover_color="#cc3333",
            command=dialog.destroy,
            width=100,
        ).pack()

    def create_ui(self):
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)

        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(fill="x", padx=40, pady=15)

        title_label = ctk.CTkLabel(
            header_content,
            text="Monitor de Modelos/Escenarios y Usuarios",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#F5F5F5",
        )
        title_label.pack(side="left")

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

        # Contenedor principal con scroll
        main_container = ctk.CTkFrame(self, fg_color="#1E1E1E")
        main_container.pack(fill="both", expand=True, padx=40, pady=20)

        self.scrollable_frame = ctk.CTkScrollableFrame(
            main_container,
            fg_color="transparent",
            scrollbar_button_color="#3A3A3A",
            scrollbar_button_hover_color="#4A4A4A",
        )
        self.scrollable_frame.pack(fill="both", expand=True)

        # Seccion 1: Cards de usuarios
        self.create_user_cards_section()
        
        # Seccion 2: Informacion de funciones y escenarios
        self.create_functions_section()
        
        # Seccion 3: Graficas
        self.create_charts_section()

    def create_user_cards_section(self):
        section_title = ctk.CTkLabel(
            self.scrollable_frame,
            text="Actividad de Red por Usuario",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="#F5F5F5",
        )
        section_title.pack(anchor="w", padx=10, pady=(20, 10))

        # Frame para las cards (grid de 4 columnas)
        self.cards_container = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        self.cards_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        for i in range(4):
            self.cards_container.grid_columnconfigure(i, weight=1)

    def create_functions_section(self):
        section_title = ctk.CTkLabel(
            self.scrollable_frame,
            text="Informacion del Generador de Funciones y Escenarios",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#F5F5F5",
        )
        section_title.pack(anchor="w", padx=10, pady=(40, 10))

        info_container = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        info_container.pack(fill="x", padx=10, pady=10)
        info_container.grid_columnconfigure(0, weight=1)
        info_container.grid_columnconfigure(1, weight=1)

        # Panel izquierdo: Funciones publicadas
        functions_panel = ctk.CTkFrame(
            info_container,
            fg_color="#2A2A2A",
            corner_radius=12,
            border_width=1,
            border_color="#3A3A3A"
        )
        functions_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            functions_panel,
            text="Funciones Publicadas por el Servidor",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F5F5F5",
        ).pack(anchor="w", padx=20, pady=(20, 10))

        # Scrollable frame para funciones
        self.functions_scroll = ctk.CTkScrollableFrame(
            functions_panel,
            fg_color="transparent",
            height=250,
        )
        self.functions_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Diccionario para rastrear widgets de funciones
        self.function_widgets = {}

        # Panel derecho: Total de escenarios
        scenarios_panel = ctk.CTkFrame(
            info_container,
            fg_color="#2A2A2A",
            corner_radius=12,
            border_width=1,
            border_color="#3A3A3A"
        )
        scenarios_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ctk.CTkLabel(
            scenarios_panel,
            text="Total de Escenarios Publicados",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F5F5F5",
        ).pack(pady=(60, 10))

        self.scenarios_label = ctk.CTkLabel(
            scenarios_panel,
            text="0",
            font=ctk.CTkFont(size=80, weight="bold"),
            text_color="#F44725",
        )
        self.scenarios_label.pack(pady=10)

        ctk.CTkLabel(
            scenarios_panel,
            text="Escenarios actualmente disponibles para ejecucion",
            font=ctk.CTkFont(size=12),
            text_color="#888888",
        ).pack(pady=(0, 40))

    def create_charts_section(self):
        section_title = ctk.CTkLabel(
            self.scrollable_frame,
            text="Gráficas de Monitoreo",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#F5F5F5",
        )
        section_title.pack(anchor="w", padx=10, pady=(40, 10))

        charts_container = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        charts_container.pack(fill="both", expand=True, padx=10, pady=10)
        charts_container.grid_columnconfigure(0, weight=1)
        charts_container.grid_columnconfigure(1, weight=1)

        # Gráfica 1: Escenarios en el tiempo (span completo)
        chart1_frame = ctk.CTkFrame(
            charts_container,
            fg_color="#2A2A2A",
            corner_radius=12,
            border_width=1,
            border_color="#3A3A3A"
        )
        chart1_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 20))

        ctk.CTkLabel(
            chart1_frame,
            text="Total de escenarios brindados",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#F5F5F5",
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.create_scenarios_chart(chart1_frame)

        # Grafica 2: Comparativa por usuario
        chart2_frame = ctk.CTkFrame(
            charts_container,
            fg_color="#2A2A2A",
            corner_radius=12,
            border_width=1,
            border_color="#3A3A3A"
        )
        chart2_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            chart2_frame,
            text="Comparativa de Resultados por Usuario",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#F5F5F5",
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.create_users_chart(chart2_frame)

        # Gráfica 3: Promedio global
        chart3_frame = ctk.CTkFrame(
            charts_container,
            fg_color="#2A2A2A",
            corner_radius=12,
            border_width=1,
            border_color="#3A3A3A"
        )
        chart3_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 0))

        ctk.CTkLabel(
            chart3_frame,
            text="Promedio de Resultados (Global)",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#F5F5F5",
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.create_average_chart(chart3_frame)

    def create_scenarios_chart(self, parent):
        fig = Figure(figsize=(12, 4), facecolor='#2A2A2A')
        self.scenarios_ax = fig.add_subplot(111)
        self.scenarios_ax.set_facecolor('#1E1E1E')
        self.scenarios_ax.tick_params(colors='white')
        self.scenarios_ax.spines['bottom'].set_color('#3A3A3A')
        self.scenarios_ax.spines['top'].set_color('#3A3A3A')
        self.scenarios_ax.spines['left'].set_color('#3A3A3A')
        self.scenarios_ax.spines['right'].set_color('#3A3A3A')
        
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.scenarios_canvas = canvas

    def create_users_chart(self, parent):
        fig = Figure(figsize=(6, 4), facecolor='#2A2A2A')
        self.users_ax = fig.add_subplot(111)
        self.users_ax.set_facecolor('#1E1E1E')
        self.users_ax.tick_params(colors='white')
        self.users_ax.spines['bottom'].set_color('#3A3A3A')
        self.users_ax.spines['top'].set_color('#3A3A3A')
        self.users_ax.spines['left'].set_color('#3A3A3A')
        self.users_ax.spines['right'].set_color('#3A3A3A')
        
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.users_canvas = canvas

    def create_average_chart(self, parent):
        fig = Figure(figsize=(6, 4), facecolor='#2A2A2A')
        self.average_ax = fig.add_subplot(111)
        self.average_ax.set_facecolor('#1E1E1E')
        self.average_ax.tick_params(colors='white')
        self.average_ax.spines['bottom'].set_color('#3A3A3A')
        self.average_ax.spines['top'].set_color('#3A3A3A')
        self.average_ax.spines['left'].set_color('#3A3A3A')
        self.average_ax.spines['right'].set_color('#3A3A3A')
        
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.average_canvas = canvas

    def update_charts(self):
        # Grafica 1: Escenarios en el tiempo
        self.scenarios_ax.clear()
        self.scenarios_ax.set_facecolor('#1E1E1E')
        if len(self.scenarios_history) > 0:
            self.scenarios_ax.plot(
                list(self.time_labels),
                list(self.scenarios_history),
                color='#2ECC71',
                linewidth=2,
                marker='o'
            )
            self.scenarios_ax.fill_between(
                range(len(self.scenarios_history)),
                self.scenarios_history,
                alpha=0.3,
                color='#2ECC71'
            )
        self.scenarios_ax.set_xlabel('Tiempo', color='white')
        self.scenarios_ax.set_ylabel('Número de Escenarios', color='white')
        # Asegurar que el eje Y comience en 0
        self.scenarios_ax.set_ylim(bottom=0)
        self.scenarios_ax.grid(True, alpha=0.1, color='white')
        self.scenarios_canvas.draw()

        # Grafica 2: Comparativa por usuario (barras verticales)
        self.users_ax.clear()
        self.users_ax.set_facecolor('#1E1E1E')
        if self.user_results_data:
            colors = ['#2ECC71', '#FF8C00', '#9B59B6', '#F1C40F', '#E74C3C', '#1ABC9C']
            users = list(self.user_results_data.keys())
            counts = [len(data["values"]) for data in self.user_results_data.values()]
            
            x_positions = range(len(users))
            bars = self.users_ax.bar(x_positions, counts, width=0.6)
            
            for i, bar in enumerate(bars):
                bar.set_color(colors[i % len(colors)])
                bar.set_alpha(0.7)
            
            self.users_ax.set_xticks(x_positions)
            self.users_ax.set_xticklabels(users, rotation=45, ha='right', fontsize=8)
            self.users_ax.set_ylabel('Resultados Brindados', color='white')
                
        self.users_ax.grid(True, alpha=0.1, color='white', axis='y')
        self.users_canvas.draw()

        # Grafica 3: Promedio global (solo actualiza si hay cambios reales)
        self.average_ax.clear()
        self.average_ax.set_facecolor('#1E1E1E')
        if len(self.global_average_history) > 0:
            self.average_ax.plot(
                range(len(self.global_average_history)),
                list(self.global_average_history),
                color='#F44725',
                linewidth=2,
                marker='o'
            )
            self.average_ax.set_xlabel('Tiempo', color='white')
            self.average_ax.set_ylabel('Promedio', color='white')
            self.average_ax.grid(True, alpha=0.1, color='white')
        self.average_canvas.draw()

    def create_card(self, ip_address, ports, color, row, col):
        card = ClientCard(self.cards_container, ip_address, ports, color=color)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        return card

    def update_cards(self):
        if self.connection_error:
            error_label = ctk.CTkLabel(
                self.cards_container,
                text="Error de conexion con el servidor\n\nNo se pueden obtener los resultados",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="#E74C3C",
            )
            error_label.grid(row=0, column=0, columnspan=4, pady=100)
            return

        colors = ["#2ECC71", "#FF8C00", "#9B59B6", "#F1C40F", "#E74C3C", "#1ABC9C"]
        for idx, (ip_address, data) in enumerate(self.user_results_data.items()):
            ports = [int(val) for val in data.get("values", [])]

            if ip_address in self.client_cards:
                card = self.client_cards[ip_address]
                try:
                    card.update_values(ports)
                except Exception as e:
                    print(f"Error actualizando card {ip_address}: {e}")
                    try:
                        index = self.card_order.index(ip_address)
                    except ValueError:
                        index = None
                    if index is not None:
                        row = index // 4
                        col = index % 4
                    else:
                        index = len(self.card_order)
                        self.card_order.append(ip_address)
                        row = index // 4
                        col = index % 4

                    new_color = colors[len(self.card_order) % len(colors)]
                    new_card = self.create_card(ip_address, ports, new_color, row, col)
                    self.client_cards[ip_address] = new_card
            else:
                insert_index = len(self.card_order)
                self.card_order.append(ip_address)
                row = insert_index // 4
                col = insert_index % 4
                color = colors[insert_index % len(colors)]

                new_card = self.create_card(ip_address, ports, color, row, col)
                self.client_cards[ip_address] = new_card

    def update_functions_display(self):
        # Solo agregar funciones nuevas, no eliminar las existentes
        if not self.published_functions:
            if not self.function_widgets:  # Solo mostrar mensaje si no hay funciones
                no_func_label = ctk.CTkLabel(
                    self.functions_scroll,
                    text="No hay funciones disponibles",
                    font=ctk.CTkFont(size=12),
                    text_color="#888888",
                )
                no_func_label.pack(pady=20)
                self.function_widgets["_empty_"] = no_func_label
        else:
            # Eliminar mensaje de "no hay funciones" si existe
            if "_empty_" in self.function_widgets:
                self.function_widgets["_empty_"].destroy()
                del self.function_widgets["_empty_"]
            
            # Agregar solo funciones nuevas
            for func in self.published_functions:
                if func not in self.function_widgets:
                    func_frame = ctk.CTkFrame(
                        self.functions_scroll,
                        fg_color="#1E1E1E",
                        corner_radius=8,
                    )
                    func_frame.pack(fill="x", pady=5)

                    ctk.CTkLabel(
                        func_frame,
                        text=func,
                        font=ctk.CTkFont(size=13),
                        text_color="#CCCCCC",
                    ).pack(padx=15, pady=12)
                    
                    self.function_widgets[func] = func_frame

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
                    stub = information_service_pb2_grpc.InformationServiceStub(channel)

                    response = stub.GetInformation(empty_pb2.Empty())
                    
                    # Actualizar resultados de usuarios
                    new_data = {}
                    for ip_address, result_list in response.user_results.items():
                        new_data[ip_address] = {"values": list(result_list.values)}

                    self.user_results_data = new_data
                    
                    # Actualizar funciones publicadas (agregar a set)
                    for func in response.published_functions:
                        self.published_functions.add(func)
                    
                    # Actualizar total de escenarios
                    self.total_scenarios = response.total_scenarios
                    
                    # Actualizar historico para graficas
                    current_time = datetime.now().strftime("%H:%M")
                    self.time_labels.append(current_time)
                    self.scenarios_history.append(self.total_scenarios)
                    
                    # Calcular promedio global actual
                    if self.user_results_data:
                        all_values = []
                        for data in self.user_results_data.values():
                            all_values.extend(data["values"])
                        
                        if all_values:
                            current_avg = sum(all_values) / len(all_values)
                            self.global_average_history.append(current_avg)
                    
                    self.connection_error = False
                    
                    # Actualizar UI
                    self.after(0, self.update_cards)
                    self.after(0, self.update_functions_display)
                    self.after(0, lambda: self.scenarios_label.configure(text=str(self.total_scenarios)))
                    self.after(0, self.update_charts)

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

                self.after(
                    0,
                    lambda: self.monitor_button.configure(
                        text="Iniciar Monitoreo",
                        fg_color="#2ECC71",
                        hover_color="#27AE60",
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
                        fg_color="#2ECC71",
                        hover_color="#27AE60",
                    ),
                )
                break

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
