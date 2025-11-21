import customtkinter as ctk

# Paleta de colores
COLORS = {
    "background": "#111822",
    "panel": "#243347",
    "primary": "#4299E1",
    "accent_green": "#00F5A0",
    "accent_red": "#E53E3E",
    "text_white": "#FFFFFF",
    "text_muted": "#92a9c8",
    "input_bg": "#1A2634",
}


class Dashboard(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        super().__init__()

        self.title("Generador de Funciones y Escenarios")
        self.geometry("1200x800")
        self.configure(fg_color=COLORS["background"])

        self.grid_columnconfigure(0, weight=2)  # Columna izquierda
        self.grid_columnconfigure(1, weight=1)  # Columna derecha
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Contenido

        # header
        self.create_header()

        # panel Izquierdo
        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.grid(row=1, column=0, sticky="nsew", padx=(40, 20), pady=20)
        self.create_left_column()

        # panel Derecho
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=1, column=1, sticky="nsew", padx=(20, 40), pady=20)
        self.create_right_column()

    def create_header(self):
        # frame general del header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(
            row=0, column=0, columnspan=2, sticky="ew", padx=40, pady=(40, 20)
        )

        # frame del titulo
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkLabel(  # titulo
            title_frame,
            text="Generador de Funciones y Escenarios",
            font=("Roboto", 28, "bold"),
            text_color=COLORS["text_white"],
        ).pack(anchor="w")

        # frame de control
        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.pack(side="right")

        # Botón de Parada/Inicio
        self.stop_btn = ctk.CTkButton(
            controls_frame,
            text="Parar envio",
            fg_color=COLORS["accent_red"],
            hover_color="#cc3333",
            font=("Roboto", 13, "bold"),
            height=40,
            corner_radius=8,
            command=self.toggle_process,
        )
        self.stop_btn.pack(side="left")
        self.is_running = True

    def create_left_column(self):
        # titulo Sección
        ctk.CTkLabel(
            self.left_frame,
            text="Carga de Funciones",
            font=("Roboto", 20, "bold"),
            text_color=COLORS["text_white"],
        ).pack(anchor="w", pady=(0, 20))

        # area de Upload
        upload_frame = ctk.CTkFrame(
            self.left_frame,
            fg_color="#1A2330",
            border_width=2,
            border_color="#334866",
            corner_radius=15,
        )
        upload_frame.pack(fill="x", pady=(0, 30), ipady=40)

        inner_upload = ctk.CTkFrame(upload_frame, fg_color="transparent")
        inner_upload.pack(expand=True)

        ctk.CTkLabel(
            inner_upload, text="☁", font=("Arial", 40), text_color=COLORS["primary"]
        ).pack(pady=(0, 10))
        ctk.CTkLabel(
            inner_upload,
            text="Cargar Archivo de Funciones",
            font=("Roboto", 18, "bold"),
            text_color="white",
        ).pack()

        ctk.CTkButton(
            inner_upload,
            text="Seleccionar Archivo",
            fg_color=COLORS["primary"],
            font=("Roboto", 13, "bold"),
            height=35,
            width=180,
        ).pack()

        # Preview de Archivo
        ctk.CTkLabel(
            self.left_frame,
            text="Vista Previa del Contenido",
            font=("Roboto", 18, "bold"),
            text_color=COLORS["text_white"],
        ).pack(anchor="w", pady=(0, 10))

        preview_textbox = ctk.CTkTextbox(
            self.left_frame,
            fg_color=COLORS["panel"],
            text_color=COLORS["text_muted"],
            font=("Consolas", 12),
            corner_radius=10,
            border_width=1,
            border_color="#334866",
        )
        preview_textbox.pack(fill="both", expand=True)

        # Contenido vacío por defecto
        sample_text = ". . ."
        preview_textbox.insert("0.0", sample_text)
        preview_textbox.configure(state="disabled")

    def create_right_column(self):
        # Título Sección
        ctk.CTkLabel(
            self.right_frame,
            text="Monitor y Configuracion",
            font=("Roboto", 20, "bold"),
            text_color=COLORS["text_white"],
        ).pack(anchor="w", pady=(0, 20))

        # 1. Tarjeta de Proceso Actual
        self.create_card(self.right_frame, self.card_content_process)

        # 2. Tarjeta Function Interval
        self.create_card(
            self.right_frame,
            lambda p: self.card_content_slider(
                p, "Intervalo de Funciones", "seg", 5, 60
            ),
        )

        # 3. Tarjeta Distribución
        self.create_card(self.right_frame, self.card_content_distribution)

        # 4. Tarjeta Generation Interval
        self.create_card(
            self.right_frame,
            lambda p: self.card_content_slider(
                p, "Intervalo de Generacion", "seg", 2, 30
            ),
        )

    def create_card(self, parent, content_func):
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["panel"],
            corner_radius=12,
            border_width=1,
            border_color="gray25",
        )
        card.pack(fill="x", pady=(0, 20))
        content_func(card)

    def card_content_process(self, parent):
        parent.configure(fg_color=COLORS["panel"])
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(padx=20, pady=20, fill="x")

        ctk.CTkLabel(
            frame,
            text="FUNCION ACTUAL CARGADA",
            font=("Roboto", 11, "bold"),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            frame,
            text=". . .",
            font=("Roboto", 24, "bold"),
            text_color=COLORS["primary"],
        ).pack(anchor="w", pady=(5, 5))

    def card_content_slider(self, parent, label_text, unit, min_val, max_val):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(padx=20, pady=20, fill="x")

        # Header del slider (Label + Input Box)
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            header, text=label_text, font=("Roboto", 14, "bold"), text_color="white"
        ).pack(side="left")

        val_box = ctk.CTkFrame(
            header,
            fg_color=COLORS["background"],
            corner_radius=6,
            border_width=1,
            border_color="gray30",
        )
        val_box.pack(side="right")

        lbl_val = ctk.CTkLabel(
            val_box, text=str(min_val), width=30, font=("Roboto", 13, "bold")
        )
        lbl_val.pack(side="left", padx=(5, 0), pady=2)
        ctk.CTkLabel(
            val_box, text=unit, font=("Roboto", 11), text_color=COLORS["text_muted"]
        ).pack(side="left", padx=(2, 5))

        # Slider
        slider = ctk.CTkSlider(
            frame,
            from_=min_val,
            to=max_val,
            number_of_steps=max_val - min_val,
            button_color=COLORS["primary"],
            progress_color=COLORS["primary"],
            command=lambda v: lbl_val.configure(text=str(int(v))),
        )
        slider.set(min_val)
        slider.pack(fill="x")

    def card_content_distribution(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(padx=20, pady=20, fill="x")

        ctk.CTkLabel(
            frame,
            text="FUNCION DE DISTRIBUCION",
            font=("Roboto", 10, "bold"),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            frame,
            text=". . .",
            font=("Roboto", 18, "bold"),
            text_color=COLORS["primary"],
        ).pack(anchor="w", pady=(2, 10))

    def toggle_process(self):
        self.is_running = not self.is_running
        if self.is_running:
            self.stop_btn.configure(
                text="Parar envio",
                fg_color=COLORS["accent_red"],
                hover_color="#cc3333",
            )
        else:
            self.stop_btn.configure(
                text="Iniciar envio",
                fg_color=COLORS["accent_green"],
                hover_color="#00d185",
                text_color="black",
            )


if __name__ == "__main__":
    app = Dashboard()
    app.mainloop()
