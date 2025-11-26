import customtkinter as ctk
from tkinter import filedialog
import threading
import time

from src.services.functions_in_file import FileFunctionReader
from src.services.scenario_generator import ScenarioGenerator
from src.rabbitmq.connection import Connection

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

        # Inicializar servicios
        self.function_reader = FileFunctionReader()
        self.scenario_generator = None
        self.rabbitmq_connection = None
        self.is_running = False
        self.function_interval = 0
        self.scenario_interval = 0
        self.current_function = ". . ."
        self.current_distribution = ". . ."
        self.current_scenario = []
        self.current_sample_size = 1
        self.publishing_thread = None

        self.grid_columnconfigure(0, weight=1)  # Columna izquierda (Monitor)
        self.grid_columnconfigure(1, weight=2)  # Columna derecha (Carga)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Contenido

        # header
        self.create_header()

        # panel Izquierdo (Monitor y Configuracion)
        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.grid(row=1, column=0, sticky="nsew", padx=(40, 20), pady=20)
        self.create_left_column()

        # panel Derecho (Carga de archivos)
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

        # Boton de Parada/Inicio
        self.stop_btn = ctk.CTkButton(
            controls_frame,
            text="Iniciar publicacion",
            fg_color=COLORS["accent_green"],
            hover_color="#00d185",
            text_color="black",
            font=("Roboto", 13, "bold"),
            height=40,
            corner_radius=8,
            command=self.toggle_process,
        )
        self.stop_btn.pack(side="left")
        self.is_running = False

    def create_left_column(self):
        # Titulo Seccion
        ctk.CTkLabel(
            self.left_frame,
            text="Monitor y Configuracion",
            font=("Roboto", 20, "bold"),
            text_color=COLORS["text_white"],
        ).pack(anchor="w", pady=(0, 20))

        # 1. Tarjeta de Proceso Actual
        self.create_card(self.left_frame, self.card_content_process)

        # 2. Tarjeta Function Interval
        self.create_card(
            self.left_frame,
            lambda p: self.card_content_slider(
                p, "Intervalo de Funciones", "seg", 0, 60
            ),
        )

        # 3. Tarjeta Distribucion
        self.create_card(self.left_frame, self.card_content_distribution)

        # 4. Tarjeta Generation Interval
        self.create_card(
            self.left_frame,
            lambda p: self.card_content_slider(
                p, "Intervalo de Generacion", "seg", 0, 30
            ),
        )

    def create_right_column(self):
        # titulo Seccion
        ctk.CTkLabel(
            self.right_frame,
            text="Carga de Funciones",
            font=("Roboto", 20, "bold"),
            text_color=COLORS["text_white"],
        ).pack(anchor="w", pady=(0, 20))

        # Boton de carga
        ctk.CTkButton(
            self.right_frame,
            text="Cargar Archivo Funciones",
            fg_color=COLORS["primary"],
            font=("Roboto", 14, "bold"),
            height=45,
            corner_radius=8,
            command=self.load_file,
        ).pack(fill="x", pady=(0, 20))

        # Preview de Archivo
        ctk.CTkLabel(
            self.right_frame,
            text="Vista Previa del Contenido",
            font=("Roboto", 18, "bold"),
            text_color=COLORS["text_white"],
        ).pack(anchor="w", pady=(0, 10))

        preview_textbox = ctk.CTkTextbox(
            self.right_frame,
            fg_color=COLORS["panel"],
            text_color=COLORS["text_muted"],
            font=("Courier New", 12),
            corner_radius=10,
            border_width=1,
            border_color="#334866",
        )
        preview_textbox.pack(fill="both", expand=True)

        # Contenido vacio por defecto
        sample_text = ". . ."
        preview_textbox.insert("0.0", sample_text)
        preview_textbox.configure(state="disabled")

        self.preview_textbox = preview_textbox

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
        self.function_label = ctk.CTkLabel(
            frame,
            text=". . .",
            font=("Roboto", 24, "bold"),
            text_color=COLORS["primary"],
        )
        self.function_label.pack(anchor="w", pady=(5, 5))

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

        # Callback para actualizar intervalo
        def update_value(v):
            val = int(v)
            lbl_val.configure(text=str(val))
            if label_text == "Intervalo de Funciones":
                self.function_interval = val
            elif label_text == "Intervalo de Generacion":
                self.scenario_interval = val

        # Slider
        slider = ctk.CTkSlider(
            frame,
            from_=min_val,
            to=max_val,
            number_of_steps=max_val - min_val if max_val > min_val else 1,
            button_color=COLORS["primary"],
            progress_color=COLORS["primary"],
            command=update_value,
        )
        slider.set(min_val)
        slider.pack(fill="x")

    def card_content_distribution(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(
            frame,
            text="FUNCION DE DISTRIBUCION",
            font=("Roboto", 10, "bold"),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w")
        self.distribution_label = ctk.CTkLabel(
            frame,
            text=". . .",
            font=("Roboto", 18, "bold"),
            text_color=COLORS["primary"],
        )
        self.distribution_label.pack(anchor="w", pady=(2, 15))

        # Seccion de escenarios publicados
        ctk.CTkLabel(
            frame,
            text="ESCENARIOS PUBLICADOS",
            font=("Roboto", 10, "bold"),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(10, 5))

        # Textbox para mostrar los escenarios
        self.scenario_textbox = ctk.CTkTextbox(
            frame,
            fg_color=COLORS["background"],
            text_color=COLORS["text_muted"],
            font=("Courier New", 10),
            corner_radius=8,
            border_width=1,
            border_color="#334866",
            height=150,
        )
        self.scenario_textbox.pack(fill="both", expand=True)
        self.scenario_textbox.insert("0.0", "Esperando escenarios...")
        self.scenario_textbox.configure(state="disabled")

    def toggle_process(self):
        self.is_running = not self.is_running
        if self.is_running:
            self.stop_btn.configure(
                text="Parar publicacion",
                fg_color=COLORS["accent_red"],
                hover_color="#cc3333",
                text_color="white",
            )
            # Iniciar publicacion
            if self.rabbitmq_connection is None:
                try:
                    self.rabbitmq_connection = Connection()
                except Exception as e:
                    print(f"Error conectando a RabbitMQ: {e}")
                    self.is_running = False
                    return

            if self.publishing_thread is None or not self.publishing_thread.is_alive():
                self.publishing_thread = threading.Thread(
                    target=self.publish_loop, daemon=True
                )
                self.publishing_thread.start()
        else:
            self.stop_btn.configure(
                text="Iniciar envio",
                fg_color=COLORS["accent_green"],
                hover_color="#00d185",
                text_color="black",
            )

    def load_file(self):
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo de funciones",
            filetypes=(("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")),
        )

        if filename:
            self.function_reader.load_functions(filename)

            # Mostrar preview
            self.preview_textbox.configure(state="normal")
            self.preview_textbox.delete("0.0", "end")

            try:
                with open(filename, "r") as f:
                    content = f.read()
                    self.preview_textbox.insert("0.0", content)
            except Exception as e:
                self.preview_textbox.insert("0.0", f"Error cargando archivo: {e}")

            self.preview_textbox.configure(state="disabled")

            # Obtener las funciones de distribucion unicas
            distributions = list(set(self.function_reader.stored_func_scenarios))
            self.scenario_generator = ScenarioGenerator(distributions)

    def parse_function_variables(self, function_str: str) -> int:
        """
        Parsea una funcion matematica y cuenta cuantas variables tiene.
        Busca patrones como f(x), f(x,y), f(x,y,z), etc.
        """
        import re

        # Buscar el patron f(...) donde ... son las variables
        match = re.search(r"f\((.*?)\)", function_str)
        if match:
            vars_str = match.group(1)
            # Separar por comas y contar
            variables = [v.strip() for v in vars_str.split(",") if v.strip()]
            return len(variables)

        # Si no encuentra el patron, retornar 1 por defecto
        return 1

    def publish_loop(self):
        last_function_time = 0
        last_scenario_time = 0

        while self.is_running:
            current_time = time.time()

            # Publicar nueva funcion si es tiempo (solo si intervalo > 0)
            if (
                self.function_interval > 0
                and current_time - last_function_time >= self.function_interval
            ):
                try:
                    function = self.function_reader.read_function()
                    distribution = self.function_reader.read_scenario()

                    if function:
                        self.rabbitmq_connection.public_function(function)

                        # Parsear cuantas variables tiene la funcion
                        num_variables = self.parse_function_variables(function)

                        # Actualizar UI
                        self.current_function = function
                        self.current_distribution = distribution
                        self.current_sample_size = num_variables
                        self.after(0, self.update_function_display)

                        last_function_time = current_time
                        last_scenario_time = current_time  # Reset scenario timer

                except Exception as e:
                    print(f"Error publicando funcion: {e}")

            # Publicar escenario si es tiempo (solo si intervalo > 0 y hay distribucion)
            if (
                self.scenario_interval > 0
                and self.current_distribution != ". . ."
                and current_time - last_scenario_time >= self.scenario_interval
            ):
                try:
                    # Usar el tamaño de muestra basado en el numero de variables
                    scenario = self.scenario_generator.get_scenario(
                        self.current_sample_size, self.current_distribution
                    )

                    if scenario:
                        self.rabbitmq_connection.public_scenario(scenario)
                        self.current_scenario = scenario
                        self.after(0, self.update_scenario_display)

                    last_scenario_time = current_time

                except Exception as e:
                    print(f"Error publicando escenario: {e}")

            time.sleep(0.1)  # Small sleep to prevent busy waiting

    def update_function_display(self):
        self.function_label.configure(text=self.current_function)
        self.distribution_label.configure(text=self.current_distribution)

    def update_scenario_display(self):
        # Formatear todos los valores del escenario para mostrar
        if self.current_scenario:
            # Redondear valores a 2 decimales
            rounded = [round(x, 2) for x in self.current_scenario]
            scenario_text = ", ".join(map(str, rounded))
            scenario_text = f"[{scenario_text}]"
            scenario_text += f"\n\nTotal de valores: {len(self.current_scenario)}"

            self.scenario_textbox.configure(state="normal")
            self.scenario_textbox.delete("0.0", "end")
            self.scenario_textbox.insert("0.0", scenario_text)
            self.scenario_textbox.configure(state="disabled")


if __name__ == "__main__":
    app = Dashboard()
    app.mainloop()
