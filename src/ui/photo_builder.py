import customtkinter as ctk
from tkinter import messagebox
import os
from src.ui.styles import *
from src.utils.file_utils import select_image_files, load_image_safe
from src.core.gif_builder import build_gif_from_images, get_gif_file_size


class PhotoBuilderWindow(ctk.CTkFrame):
    def __init__(self, parent, on_back, on_preview):
        super().__init__(parent, fg_color=BG)
        self.parent = parent
        self.on_back = on_back
        self.on_preview = on_preview
        self.images = []
        self.image_paths = []
        self._build()

    def _build(self):
        self.pack(fill="both", expand=True)

        top_bar = ctk.CTkFrame(self, fg_color=PRIMARY, height=50, corner_radius=0)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)

        ctk.CTkButton(
            top_bar, text="← Назад",
            fg_color=PRIMARY, text_color=WHITE,
            hover_color=HOVER_PRIMARY,
            font=("Helvetica", 12), corner_radius=CORNER_RADIUS_SM,
            command=self.on_back, width=80
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkLabel(
            top_bar, text="GIF сборщик из фото",
            font=("Helvetica", 16), text_color=WHITE
        ).pack(side="left", padx=20)

        main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        main.pack(fill="both", expand=True, padx=15, pady=15)

        left = ctk.CTkFrame(
            main, fg_color=WHITE,
            corner_radius=CORNER_RADIUS, width=280,
            border_width=1, border_color=LIGHT_GRAY
        )
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        ctk.CTkLabel(
            left, text="Файлы",
            font=("Helvetica", 16, "bold"), text_color=DARK_TEXT
        ).pack(pady=(12, 8))

        scroll_frame = ctk.CTkScrollableFrame(
            left, fg_color=WHITE, corner_radius=0
        )
        scroll_frame.pack(fill="both", expand=True, padx=10)
        self.file_scroll = scroll_frame

        self.file_labels = []

        add_btn = ctk.CTkButton(
            left, text="+",
            font=("Helvetica", 26, "bold"),
            fg_color=PRIMARY, text_color=WHITE,
            hover_color=HOVER_PRIMARY,
            corner_radius=CORNER_RADIUS,
            height=40, width=50,
            command=self._add_images
        )
        add_btn.pack(pady=10)

        right = ctk.CTkFrame(
            main, fg_color=WHITE,
            corner_radius=CORNER_RADIUS,
            border_width=1, border_color=LIGHT_GRAY
        )
        right.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(
            right, text="Настройки",
            font=("Helvetica", 16, "bold"), text_color=DARK_TEXT
        ).pack(pady=(12, 15))

        block1 = ctk.CTkFrame(
            right, fg_color=WHITE,
            corner_radius=CORNER_RADIUS_SM,
            border_width=1, border_color=LIGHT_GRAY
        )
        block1.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(
            block1, text="Стабилизация",
            font=("Helvetica", 13, "bold"), text_color=DARK_TEXT
        ).pack(pady=(10, 5), padx=12, anchor="w")

        self.stab_var = ctk.BooleanVar(value=False)
        self.stab_check = ctk.CTkCheckBox(
            block1, text="Включить стабилизацию",
            variable=self.stab_var, font=("Helvetica", 12),
            text_color=DARK_TEXT, fg_color=PRIMARY,
            hover_color=HOVER_PRIMARY,
            command=self._toggle_stab
        )
        self.stab_check.pack(anchor="w", padx=12, pady=2)

        self.smooth_frame = ctk.CTkFrame(block1, fg_color=WHITE, corner_radius=0)
        self.smooth_frame.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(
            self.smooth_frame, text="Сглаживание:",
            font=("Helvetica", 12), text_color=GRAY, width=110, anchor="w"
        ).pack(side="left")
        self.smooth_var = ctk.DoubleVar(value=0.5)
        self.smooth_slider = ctk.CTkSlider(
            self.smooth_frame, from_=0, to=1, number_of_steps=10,
            variable=self.smooth_var,
            fg_color=LIGHT_GRAY, progress_color=PRIMARY,
            button_color=PRIMARY, button_hover_color=HOVER_PRIMARY,
            width=140
        )
        self.smooth_slider.pack(side="left", padx=(5, 0))
        self.smooth_label = ctk.CTkLabel(
            self.smooth_frame, text="0.5",
            font=("Helvetica", 11), text_color=GRAY, width=30
        )
        self.smooth_label.pack(side="left", padx=(5, 0))
        self.smooth_slider.configure(command=lambda v: self.smooth_label.configure(text=f"{v:.1f}"))
        self.smooth_frame.pack_forget()

        self.alg_frame = ctk.CTkFrame(block1, fg_color=WHITE, corner_radius=0)
        self.alg_frame.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(
            self.alg_frame, text="Алгоритм:",
            font=("Helvetica", 12), text_color=GRAY, width=110, anchor="w"
        ).pack(side="left")
        self.stab_alg = ctk.CTkOptionMenu(
            self.alg_frame, values=["ECC", "ORB", "SIFT"],
            fg_color=WHITE, text_color=DARK_TEXT,
            button_color=PRIMARY, button_hover_color=HOVER_PRIMARY,
            dropdown_fg_color=WHITE, dropdown_text_color=DARK_TEXT,
            dropdown_hover_color=PRIMARY,
            corner_radius=CORNER_RADIUS_SM,
            font=("Helvetica", 11)
        )
        self.stab_alg.pack(side="left", padx=(5, 0))
        self.alg_frame.pack_forget()

        block1.pack_configure(pady=(5, 0), padx=20)

        block2 = ctk.CTkFrame(
            right, fg_color=WHITE,
            corner_radius=CORNER_RADIUS_SM,
            border_width=1, border_color=LIGHT_GRAY
        )
        block2.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            block2, text="Квантизация палитры",
            font=("Helvetica", 13, "bold"), text_color=DARK_TEXT
        ).pack(pady=(10, 5), padx=12, anchor="w")

        self.quant_var = ctk.BooleanVar(value=False)
        self.quant_check = ctk.CTkCheckBox(
            block2, text="Включить квантизацию",
            variable=self.quant_var, font=("Helvetica", 12),
            text_color=DARK_TEXT, fg_color=PRIMARY,
            hover_color=HOVER_PRIMARY,
            command=self._toggle_quant
        )
        self.quant_check.pack(anchor="w", padx=12, pady=2)

        self.color_frame = ctk.CTkFrame(block2, fg_color=WHITE, corner_radius=0)
        self.color_frame.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(
            self.color_frame, text="Цветов:",
            font=("Helvetica", 12), text_color=GRAY, width=110, anchor="w"
        ).pack(side="left")
        self.color_var = ctk.IntVar(value=64)
        self.color_slider = ctk.CTkSlider(
            self.color_frame, from_=2, to=256, number_of_steps=254,
            variable=self.color_var,
            fg_color=LIGHT_GRAY, progress_color=PRIMARY,
            button_color=PRIMARY, button_hover_color=HOVER_PRIMARY,
            width=140
        )
        self.color_slider.pack(side="left", padx=(5, 0))
        self.color_label = ctk.CTkLabel(
            self.color_frame, text="64",
            font=("Helvetica", 11), text_color=GRAY, width=30
        )
        self.color_label.pack(side="left", padx=(5, 0))
        self.color_slider.configure(command=lambda v: self.color_label.configure(text=str(int(v))))
        self.color_frame.pack_forget()

        self.quant_alg_frame = ctk.CTkFrame(block2, fg_color=WHITE, corner_radius=0)
        self.quant_alg_frame.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(
            self.quant_alg_frame, text="Метод:",
            font=("Helvetica", 12), text_color=GRAY, width=110, anchor="w"
        ).pack(side="left")
        self.quant_alg = ctk.CTkOptionMenu(
            self.quant_alg_frame, values=["Median Cut", "Octree", "Fast Octree"],
            fg_color=WHITE, text_color=DARK_TEXT,
            button_color=PRIMARY, button_hover_color=HOVER_PRIMARY,
            dropdown_fg_color=WHITE, dropdown_text_color=DARK_TEXT,
            dropdown_hover_color=PRIMARY,
            corner_radius=CORNER_RADIUS_SM,
            font=("Helvetica", 11)
        )
        self.quant_alg.pack(side="left", padx=(5, 0))
        self.quant_alg_frame.pack_forget()

        bottom = ctk.CTkFrame(self, fg_color=BG, height=70, corner_radius=0)
        bottom.pack(fill="x")
        bottom.pack_propagate(False)

        ctk.CTkButton(
            bottom, text="Собрать GIF",
            font=("Helvetica", 15, "bold"),
            fg_color=SECONDARY, text_color=WHITE,
            hover_color=HOVER_SECONDARY,
            corner_radius=CORNER_RADIUS,
            height=42, width=240,
            command=self._assemble
        ).pack(pady=12)

    def _toggle_stab(self):
        if self.stab_var.get():
            self.smooth_frame.pack(fill="x", padx=12, pady=4)
            self.alg_frame.pack(fill="x", padx=12, pady=4)
        else:
            self.smooth_frame.pack_forget()
            self.alg_frame.pack_forget()

    def _toggle_quant(self):
        if self.quant_var.get():
            self.color_frame.pack(fill="x", padx=12, pady=4)
            self.quant_alg_frame.pack(fill="x", padx=12, pady=4)
        else:
            self.color_frame.pack_forget()
            self.quant_alg_frame.pack_forget()

    def _refresh_file_list(self):
        for w in self.file_labels:
            w.destroy()
        self.file_labels = []
        for i, path in enumerate(self.image_paths):
            name = os.path.basename(path)
            lbl = ctk.CTkLabel(
                self.file_scroll, text=name,
                font=("Helvetica", 11),
                text_color=DARK_TEXT,
                anchor="w",
                fg_color=WHITE
            )
            lbl.pack(fill="x", padx=4, pady=1)
            self.file_labels.append(lbl)

    def _add_images(self):
        paths = select_image_files()
        for path in paths:
            if path not in self.image_paths:
                self.image_paths.append(path)
                img = load_image_safe(path)
                if img:
                    self.images.append(img)
        self._refresh_file_list()

    def _assemble(self):
        if len(self.images) < 2:
            messagebox.showwarning(
                "Предупреждение",
                "Добавьте минимум 2 изображения для создания GIF."
            )
            return

        output_dir = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))), "output")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "preview.gif")

        success = build_gif_from_images(
            self.images, output_path,
            duration=500,
            stabilize=self.stab_var.get(),
            stabilization_alg=self.stab_alg.get(),
            smoothing=self.smooth_var.get(),
            quantize=self.quant_var.get(),
            colors=self.color_var.get(),
            quantize_alg=self.quant_alg.get()
        )

        if success:
            info = {
                "Кадров": len(self.images),
                "Стабилизация": "Вкл" if self.stab_var.get() else "Выкл",
                "Квантизация": "Вкл" if self.quant_var.get() else "Выкл",
            }
            if self.stab_var.get():
                info["Алгоритм стаб."] = self.stab_alg.get()
            if self.quant_var.get():
                info["Метод квант."] = self.quant_alg.get()
                info["Цветов"] = str(self.color_var.get())
            info["Размер файла"] = get_gif_file_size(output_path)
            self.on_preview(output_path, info)
        else:
            messagebox.showerror(
                "Ошибка",
                "Не удалось создать GIF."
            )
