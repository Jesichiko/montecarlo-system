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
            text_color="#F5F5F5",
        )
        self.ip_label.pack(anchor="w", padx=20, pady=(20, 10))

        # frame scrollable para los puertos con scrollbar
        # usamos colores hex sin alpha
        self.ports_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color="#777777",
            scrollbar_button_hover_color="#999999",
        )
        self.ports_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # contenedor interno donde ponemos los badges en grid 3 columnas
        # (los widgets se agregan directamente a ports_frame usando grid)
        self.port_badges = []  # lista de widgets CTkLabel

        # inicializamos con valores iniciales
        self.update_values(values)

    def update_values(self, values):
        # destruir badges previos
        for badge in self.port_badges:
            try:
                badge.destroy()
            except Exception:
                pass
        self.port_badges = []

        # crear nuevos badges segun values
        for i, val in enumerate(values):
            port_badge = ctk.CTkLabel(
                self.ports_frame,
                text=str(val),
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#CCCCCC",  # color seguro sin alpha
                text_color="#000000",
                corner_radius=15,
                width=60,
                height=28,
            )
            row_pos = i // 3
            col_pos = i % 3
            port_badge.grid(row=row_pos, column=col_pos, padx=4, pady=4, sticky="w")
            self.port_badges.append(port_badge)
