import os
import threading
import customtkinter as ctk
from dotenv import load_dotenv
import grpc
from google.protobuf import empty_pb2
from protos import results_service_pb2_grpc


class NetworkMonitorApp(ctk.CTk):
    def __init__(self):
        self.title("Monitor de resultados")
        self.geometry("1400x900")
        
        # tema oscuro
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        super().__init__()

        # estado
        self.monitoring = False
        self.monitor_thread = None
        self.results_data = {}
        
        # variables de entorno
        load_dotenv()
        
        # UI
        self.create_ui()
        
    def create_ui(self):
        # header
        header_frame = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        
        # contenedor para título y botón
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(fill="x", padx=40, pady=15)
        
        # titulo
        title_label = ctk.CTkLabel(
            header_content,
            text="Monitoreo de Resultados",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#F5F5F5"
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
            corner_radius=8
        )
        self.monitor_button.pack(side="right")
        
        # Contenedor principal con scroll
        main_container = ctk.CTkFrame(self, fg_color="#1E1E1E")
        main_container.pack(fill="both", expand=True, padx=40, pady=20)
         
        # ScrollableFrame para las tarjetas
        self.scrollable_frame = ctk.CTkScrollableFrame(
            main_container,
            fg_color="transparent",
            scrollbar_button_color="#3a3a3a",
            scrollbar_button_hover_color="#4a4a4a"
        )
        self.scrollable_frame.pack(fill="both", expand=True)
        
        # Configurar grid para las tarjetas
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(1, weight=1)
        self.scrollable_frame.grid_columnconfigure(2, weight=1)
        self.scrollable_frame.grid_columnconfigure(3, weight=1)
        
        # Frame para las tarjetas (se actualizará dinámicamente)
        self.cards_container = self.scrollable_frame
        
    def create_card(self, ip_address, ports, color, row, col):
        """Crea una tarjeta de dispositivo de red"""
        card = ctk.CTkFrame(
            self.cards_container,
            fg_color=f"{color}1A",  # Color con transparencia
            border_color=f"{color}4D",
            border_width=2,
            corner_radius=12,
            width=280,
            height=400
        )
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_propagate(False)
        
        # IP Address (título)
        ip_label = ctk.CTkLabel(
            card,
            text=ip_address,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#F5F5F5"
        )
        ip_label.pack(anchor="w", padx=20, pady=(20, 10))
        
        # Frame scrollable para los puertos con scrollbar personalizado
        ports_frame = ctk.CTkScrollableFrame(
            card,
            fg_color="transparent",
            scrollbar_button_color="#FFFFFF33",
            scrollbar_button_hover_color="#FFFFFF4D",
            scrollbar_fg_color="transparent"
        )
        ports_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Crear badges de puertos en un contenedor con wrap
        for i, port in enumerate(ports):
            port_badge = ctk.CTkLabel(
                ports_frame,
                text=str(port),
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#FFFFFF1A",
                text_color="#F5F5F5",
                corner_radius=15,
                width=60,
                height=28
            )
            # Calcular posición en grid (3 columnas)
            row_pos = i // 3
            col_pos = i % 3
            port_badge.grid(row=row_pos, column=col_pos, padx=4, pady=4, sticky="w")
    
    def update_cards(self):
        """Actualiza las tarjetas con los datos del servidor"""
        # Limpiar tarjetas existentes
        for widget in self.cards_container.winfo_children():
            widget.destroy()
        
        # Colores para las tarjetas (ciclan)
        colors = ["#2ECC71", "#FF8C00", "#9B59B6", "#F1C40F", "#E74C3C", "#1ABC9C"]
        
        # Crear tarjetas para cada IP
        row = 0
        col = 0
        for idx, (ip_address, data) in enumerate(self.results_data.items()):
            ports = [int(val) for val in data.get("values", [])]
            color = colors[idx % len(colors)]
            
            self.create_card(ip_address, ports, color, row, col)
            
            col += 1
            if col >= 4:  # 4 columnas
                col = 0
                row += 1
    
    def toggle_monitoring(self):
        """Inicia o detiene el monitoreo"""
        if not self.monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """Inicia el monitoreo de red"""
        self.monitoring = True
        self.monitor_button.configure(
            text="Stop Monitor",
            fg_color="#E74C3C",
            hover_color="#C0392B"
        )
        
        # Iniciar thread de monitoreo
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Detiene el monitoreo de red"""
        self.monitoring = False
        self.monitor_button.configure(
            text="Start Monitor",
            fg_color="#2ECC71",
            hover_color="#27AE60"
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
                        new_data[ip_address] = {
                            "values": list(result_list.values)
                        }
                    
                    self.results_data = new_data
                    self.after(0, self.update_cards)
                    
            except Exception as e:
                print(f"Error connecting to gRPC server: {e}")
            
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
