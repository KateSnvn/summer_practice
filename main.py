import customtkinter as ctk
from src.ui.styles import *

import os

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class App:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("GIF Painter")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)

        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = (ws - 1100) // 2
        y = (hs - 750) // 2
        self.root.geometry(f"1100x750+{x}+{y}")

        self.container = ctk.CTkFrame(self.root, fg_color=BG, corner_radius=0)
        self.container.pack(fill="both", expand=True)

        self.current_frame = None
        self.temp_gif_path = None
        self.show_main_menu()

if __name__ == "__main__":
    app = App()
    app.run()