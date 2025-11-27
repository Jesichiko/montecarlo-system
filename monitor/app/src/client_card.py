import customtkinter as ctk

class ClientCard(ctk.CTkFrame):
    def __init__(self, parent, ip_address, values, color="#2ECC71"):
        super().__init__(
            parent,
            fg_color=color,
            border_color=color,
            border_width=2,
            corner_radius=12,
            width=280,
            height=400,
        )
        self.ip = ip_address
        self.color = color
        self.grid_propagate(False)

        # IP Address (titulo)
        self.ip_label = ctk.CTkLabel(
            self,
            text=ip_address,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#FFFFFF",
        )
        self.ip_label.pack(anchor="w", padx=20, pady=(20, 10))

        # frame scrollable para los puertos con scrollbar
        self.ports_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color="#777777",
            scrollbar_button_hover_color="#999999",
        )
        self.ports_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # lista de widgets CTkLabel (badges)
        self.port_badges = []

        # footer para estadisticas
        self.footer_frame = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=8)  # Corregido: sin transparencia
        self.footer_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.count_label = ctk.CTkLabel(
            self.footer_frame,
            text="Resultados brindados: 0",
            font=ctk.CTkFont(size=11),
            text_color="#CCCCCC",
        )
        self.count_label.pack(anchor="w", padx=15, pady=(10, 5))

        self.average_label = ctk.CTkLabel(
            self.footer_frame,
            text="Promedio de Resultados: 0.00",
            font=ctk.CTkFont(size=11),
            text_color="#CCCCCC",
        )
        self.average_label.pack(anchor="w", padx=15, pady=(0, 10))

        # inicializamos con valores iniciales
        self.update_values(values)

    def update_values(self, values):
        num_current_badges = len(self.port_badges)
        num_new_values = len(values)

        # Caso 1: Necesitamos mas badges
        if num_new_values > num_current_badges:
            # Actualizamos los badges existentes
            for i in range(num_current_badges):
                self.port_badges[i].configure(text=str(int(values[i])))
            
            # Creamos los badges faltantes
            for i in range(num_current_badges, num_new_values):
                port_badge = ctk.CTkLabel(
                    self.ports_frame,
                    text=str(int(values[i])),
                    font=ctk.CTkFont(size=11, weight="bold"),
                    fg_color="#FFFFFF",
                    text_color="#1E1E1E",  # Corregido: texto oscuro sobre fondo blanco
                    corner_radius=15,
                    width=60,
                    height=28,
                )
                row_pos = i // 3
                col_pos = i % 3
                port_badge.grid(row=row_pos, column=col_pos, padx=4, pady=4, sticky="w")
                self.port_badges.append(port_badge)
        
        # Caso 2: Tenemos mas badges de los necesarios
        elif num_new_values < num_current_badges:
            # Actualizamos los badges que se mantendran
            for i in range(num_new_values):
                self.port_badges[i].configure(text=str(int(values[i])))
            
            # Destruimos los badges sobrantes
            for i in range(num_new_values, num_current_badges):
                try:
                    self.port_badges[i].destroy()
                except Exception:
                    pass
            
            # Actualizamos la lista
            self.port_badges = self.port_badges[:num_new_values]
        
        # Caso 3: Mismo numero de badges
        else:
            # Solo actualizamos el texto
            for i in range(num_new_values):
                self.port_badges[i].configure(text=str(int(values[i])))
        
        # estadisticas en el footer
        count = len(values)
        average = sum(values) / count if count > 0 else 0
        
        self.count_label.configure(text=f"Resultados brindados: {count}")
        self.average_label.configure(text=f"Promedio de Resultados: {average:.2f}")
