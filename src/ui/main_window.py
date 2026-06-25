import customtkinter as ctk
from src.ui.styles import *


class MainWindow(ctk.CTkFrame):
    def __init__(self, parent, on_photo_builder, on_drawing):
        super().__init__(parent, fg_color=BG)
        self.parent = parent
        self.on_photo_builder = on_photo_builder
        self.on_drawing = on_drawing
        self._build()

    def _build(self):
        self.pack(fill="both", expand=True)

        container = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=CORNER_RADIUS)
        container.place(relx=0.5, rely=0.45, anchor="center")
        container.configure(width=380, height=320)
        container.pack_propagate(False)

        container.grid_rowconfigure(0, weight=1)
        container.grid_rowconfigure(4, weight=1)
        container.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            container, text="GIF Painter",
            font=("Helvetica", 26, "bold"),
            text_color=SECONDARY
        )
        title.grid(row=1, column=0, pady=(30, 30))

        btn_builder = ctk.CTkButton(
            container, text="GIF сборщик из фото",
            font=("Helvetica", 14, "bold"),
            fg_color=PRIMARY, text_color=WHITE,
            hover_color=HOVER_PRIMARY,
            corner_radius=CORNER_RADIUS,
            height=44, width=260,
            command=self.on_photo_builder
        )
        btn_builder.grid(row=2, column=0, pady=6)

        btn_drawing = ctk.CTkButton(
            container, text="Рисование GIF",
            font=("Helvetica", 14, "bold"),
            fg_color=PRIMARY, text_color=WHITE,
            hover_color=HOVER_PRIMARY,
            corner_radius=CORNER_RADIUS,
            height=44, width=260,
            command=self.on_drawing
        )
        btn_drawing.grid(row=3, column=0, pady=6)
