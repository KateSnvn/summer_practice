import customtkinter as ctk
import tkinter as tk
from tkinter import colorchooser, messagebox
import os
from PIL import Image, ImageTk
from src.ui.styles import *
from src.ui.shape_selector import ShapeSelector
from src.drawing.tools import Tool, ShapeType
from src.drawing.layer_manager import LayerManager
from src.drawing.canvas_handler import CanvasHandler
from src.utils.file_utils import select_single_image, load_image_safe
from src.core.gif_builder import build_gif_from_layers, get_gif_file_size


class DrawingWindow(ctk.CTkFrame):
    CANVAS_W = 700
    CANVAS_H = 500

    def __init__(self, parent, on_back, on_preview):
        super().__init__(parent, fg_color=BG)
        self.parent = parent
        self.on_back = on_back
        self.on_preview = on_preview
        self.layer_manager = LayerManager(self.CANVAS_W, self.CANVAS_H)
        self.canvas_handler = CanvasHandler(self.layer_manager)
        self.current_tool_btn = None
        self._build()

    def _build(self):
        self.pack(fill="both", expand=True)

        top_bar = ctk.CTkFrame(self, fg_color=PRIMARY, height=40, corner_radius=0)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)

        ctk.CTkButton(
            top_bar, text="← Назад",
            fg_color=PRIMARY, text_color=WHITE,
            hover_color=HOVER_PRIMARY,
            font=("Helvetica", 11), corner_radius=CORNER_RADIUS_SM,
            command=self.on_back, width=60, height=28
        ).pack(side="left", padx=6, pady=6)

        filters = [("Ч/Б", "Grayscale"), ("Сепия", "Sepia"),
                ("Инверсия", "Invert"), ("Размытие", "Blur"),
                ("Резкость", "Sharpen"), ("Рельеф", "Emboss")]
        for label, name in filters:
            btn = ctk.CTkButton(
                top_bar, text=label,
                fg_color=PRIMARY, text_color=WHITE,
                hover_color=HOVER_PRIMARY,
                font=("Helvetica", 11), corner_radius=CORNER_RADIUS_SM,
                height=28, width=60,
                command=lambda n=name: self._apply_filter(n)
            )
            btn.pack(side="left", padx=2, pady=6)

        sep = ctk.CTkFrame(top_bar, fg_color=WHITE, width=1, height=22, corner_radius=0)
        sep.pack(side="left", padx=6)

        for text, cmd in [("↺", lambda: self._rotate("left")),
                        ("↻", lambda: self._rotate("right")),
                        ("↔", lambda: self._flip("horizontal")),
                        ("↕", lambda: self._flip("vertical"))]:
            ctk.CTkButton(
                top_bar, text=text,
                fg_color=PRIMARY, text_color=WHITE,
                hover_color=HOVER_PRIMARY,
                font=("Helvetica", 15), corner_radius=CORNER_RADIUS_SM,
                height=28, width=36, command=cmd
            ).pack(side="left", padx=2, pady=6)

        mid = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        mid.pack(fill="both", expand=True)

        left_tools = ctk.CTkFrame(
            mid, fg_color=WHITE,
            corner_radius=CORNER_RADIUS, width=68,
            border_width=1, border_color=LIGHT_GRAY
        )
        left_tools.pack(side="left", fill="y", padx=(0, 5))
        left_tools.pack_propagate(False)

        tool_items = [
            ("✏️", Tool.BRUSH, "Кисть"),
            ("🧹", Tool.ERASER, "Ластик"),
            ("◇", Tool.SHAPE, "Фигура"),
            ("🪣", Tool.FILL, "Заливка"),
            ("💉", Tool.EYEDROPPER, "Пипетка"),
        ]

        self.tool_buttons = {}
        for icon, tool, tip in tool_items:
            btn = ctk.CTkButton(
                left_tools, text=icon,
                fg_color=LIGHT_GRAY, text_color=DARK_TEXT,
                hover_color=PRIMARY,
                font=("Helvetica", 18), corner_radius=CORNER_RADIUS_SM,
                height=38, width=50,
                command=lambda t=tool, b=None: self._select_tool(t)
            )
            btn.pack(pady=3, padx=6)
            self.tool_buttons[tool] = btn
            self._add_tooltip(btn, tip)

        ctk.CTkButton(
            left_tools, text="🖼️",
            fg_color=LIGHT_GRAY, text_color=DARK_TEXT,
            hover_color=PRIMARY,
            font=("Helvetica", 18), corner_radius=CORNER_RADIUS_SM,
            height=38, width=50,
            command=self._add_photo
        ).pack(pady=3, padx=6)

        self.color_btn = ctk.CTkButton(
            left_tools, text="",
            fg_color="#000000", hover_color="#000000",
            corner_radius=CORNER_RADIUS_SM,
            height=30, width=50,
            command=self._choose_color
        )
        self.color_btn.pack(pady=6)

        size_frame = ctk.CTkFrame(left_tools, fg_color=WHITE, corner_radius=0)
        size_frame.pack(pady=4, padx=6)
        ctk.CTkLabel(
            size_frame, text="Размер",
            font=("Helvetica", 10), text_color=GRAY
        ).pack()
        self.size_var = ctk.IntVar(value=3)
        self.size_slider = ctk.CTkSlider(
            size_frame, from_=1, to=30,
            orientation="vertical", variable=self.size_var,
            fg_color=LIGHT_GRAY, progress_color=PRIMARY,
            button_color=PRIMARY, button_hover_color=HOVER_PRIMARY,
            height=80, width=16,
            command=self._on_size_change
        )
        self.size_slider.pack(pady=2)

        canvas_container = ctk.CTkFrame(
            mid, fg_color=WHITE,
            corner_radius=CORNER_RADIUS,
            border_width=1, border_color=LIGHT_GRAY
        )
        canvas_container.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(
            canvas_container, bg="white",
            width=self.CANVAS_W, height=self.CANVAS_H,
            highlightthickness=0, cursor="crosshair"
        )
        self.canvas.pack(expand=True, padx=10, pady=10)

        self.canvas.bind("<Button-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)

        right_panel = ctk.CTkFrame(
            mid, fg_color=WHITE,
            corner_radius=CORNER_RADIUS, width=180,
            border_width=1, border_color=LIGHT_GRAY
        )
        right_panel.pack(side="right", fill="y", padx=(5, 0))
        right_panel.pack_propagate(False)

        ctk.CTkLabel(
            right_panel, text="Слои",
            font=("Helvetica", 16, "bold"), text_color=DARK_TEXT
        ).pack(pady=(12, 8))

        self.layer_scroll = ctk.CTkScrollableFrame(
            right_panel, fg_color=WHITE, corner_radius=0
        )
        self.layer_scroll.pack(fill="both", expand=True, padx=8)

        self.layer_widgets = []

        ctk.CTkButton(
            right_panel, text="+ Слой",
            font=("Helvetica", 13, "bold"),
            fg_color=PRIMARY, text_color=WHITE,
            hover_color=HOVER_PRIMARY,
            corner_radius=CORNER_RADIUS_SM,
            height=34,
            command=self._add_layer
        ).pack(pady=(6, 3), padx=8, fill="x")

        ctk.CTkButton(
            right_panel, text="Удалить слой",
            font=("Helvetica", 12),
            fg_color=LIGHT_GRAY, text_color=DARK_TEXT,
            hover_color="#C0C0C0",
            corner_radius=CORNER_RADIUS_SM,
            height=32,
            command=self._remove_layer
        ).pack(pady=2, padx=8, fill="x")

        ctk.CTkButton(
            right_panel, text="Дублировать",
            font=("Helvetica", 12),
            fg_color=LIGHT_GRAY, text_color=DARK_TEXT,
            hover_color="#C0C0C0",
            corner_radius=CORNER_RADIUS_SM,
            height=32,
            command=self._duplicate_layer
        ).pack(padx=8, fill="x", pady=(2, 10))

        bottom = ctk.CTkFrame(self, fg_color=BG, height=60, corner_radius=0)
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
        ).pack(pady=10)

        self._select_tool(Tool.BRUSH)
        self._update_layer_list()
        self._render_canvas()

    def _add_tooltip(self, widget, text):
        tip = None
        def show(event):
            nonlocal tip
            if tip:
                return
            x = widget.winfo_rootx() + 30
            y = widget.winfo_rooty() + 5
            tip = ctk.CTkToplevel(widget)
            tip.wm_overrideredirect(True)
            tip.wm_geometry(f"+{x}+{y}")
            tip.attributes("-topmost", True)
            ctk.CTkLabel(
                tip, text=text,
                font=("Helvetica", 10),
                text_color=WHITE, fg_color="#333333",
                corner_radius=4
            ).pack()
        def hide(event):
            nonlocal tip
            if tip:
                tip.destroy()
                tip = None
        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)

    def _select_tool(self, tool, btn=None):
        self.canvas_handler.set_tool(tool)
        for t, b in self.tool_buttons.items():
            b.configure(fg_color=LIGHT_GRAY, text_color=DARK_TEXT)
        if tool in self.tool_buttons:
            self.tool_buttons[tool].configure(fg_color=PRIMARY, text_color=WHITE)
        if tool == Tool.BRUSH:
            self.size_var.set(self.canvas_handler.brush_size)
        elif tool == Tool.ERASER:
            self.size_var.set(self.canvas_handler.eraser_size)
        elif tool == Tool.SHAPE:
            ShapeSelector(
                self,
                current_shape=self.canvas_handler.shape_type,
                callback=self.canvas_handler.set_shape
            )

    def _choose_color(self):
        color = colorchooser.askcolor(
            title="Выберите цвет",
            initialcolor=self.canvas_handler.brush_color
        )
        if color and color[1]:
            self.canvas_handler.set_color(color[1])
            self.color_btn.configure(fg_color=color[1], hover_color=color[1])

    def _on_size_change(self, val):
        size = int(val)
        if self.canvas_handler.tool == Tool.ERASER:
            self.canvas_handler.set_eraser_size(size)
        else:
            self.canvas_handler.set_brush_size(size)

    def _add_photo(self):
        path = select_single_image()
        if path:
            img = load_image_safe(path)
            if img:
                img.thumbnail((self.CANVAS_W, self.CANVAS_H), Image.LANCZOS)
                x = (self.CANVAS_W - img.width) // 2
                y = (self.CANVAS_H - img.height) // 2
                self.canvas_handler.paste_image(img, x, y)
                self._render_canvas()

    def _apply_filter(self, name):
        self.canvas_handler.apply_filter(name)
        self._render_canvas()

    def _rotate(self, direction):
        self.canvas_handler.rotate(direction)
        self._render_canvas()

    def _flip(self, direction):
        self.canvas_handler.flip(direction)
        self._render_canvas()

    def _on_mouse_down(self, event):
        if self.canvas_handler.tool == Tool.SHAPE:
            self.canvas_handler.on_mouse_down(event)
            return
        if self.canvas_handler.tool == Tool.EYEDROPPER:
            color = self.canvas_handler.pick_color(event.x, event.y)
            self.color_btn.configure(fg_color=color, hover_color=color)
            self._select_tool(Tool.BRUSH)
            return
        self.canvas_handler.on_mouse_down(event)

    def _on_mouse_move(self, event):
        self.canvas_handler.on_mouse_move(event)
        if self.canvas_handler.drawing and self.canvas_handler.tool in (Tool.BRUSH, Tool.ERASER):
            self._render_canvas()

    def _on_mouse_up(self, event):
        self.canvas_handler.on_mouse_up(event)
        if self.canvas_handler.tool in (Tool.BRUSH, Tool.ERASER, Tool.SHAPE):
            self._render_canvas()

    def _add_layer(self):
        self.layer_manager.add_layer()
        self._update_layer_list()
        self._render_canvas()
        self._select_tool(Tool.BRUSH)

    def _remove_layer(self):
        if self.layer_manager.active_index is not None:
            if self.layer_manager.remove_layer(self.layer_manager.active_index):
                self._update_layer_list()
                self._render_canvas()

    def _duplicate_layer(self):
        if self.layer_manager.active_index is not None:
            self.layer_manager.duplicate_layer(self.layer_manager.active_index)
            self._update_layer_list()
            self._render_canvas()

    def _on_layer_click(self, index):
        self.layer_manager.active_index = index
        self._update_layer_list()
        self._render_canvas()

    def _update_layer_list(self):
        for w in self.layer_widgets:
            w.destroy()
        self.layer_widgets = []

        for i, layer in enumerate(self.layer_manager.layers):
            is_active = i == self.layer_manager.active_index
            item = ctk.CTkFrame(
                self.layer_scroll, fg_color=PRIMARY if is_active else WHITE,
                corner_radius=CORNER_RADIUS_SM,
                border_width=1 if not is_active else 0,
                border_color=LIGHT_GRAY,
                height=32
            )
            item.pack(fill="x", pady=2)
            item.pack_propagate(False)

            inner = ctk.CTkFrame(item, fg_color="transparent", corner_radius=0)
            inner.pack(fill="both", expand=True, padx=6)

            label = ctk.CTkLabel(
                inner, text=layer.name,
                font=("Helvetica", 12),
                text_color=WHITE if is_active else DARK_TEXT,
                anchor="w"
            )
            label.pack(side="left", fill="x", expand=True)

            vis_btn = ctk.CTkButton(
                inner, text="👁" if layer.visible else "○",
                fg_color="transparent",
                text_color=WHITE if is_active else GRAY,
                hover_color=PRIMARY if is_active else LIGHT_GRAY,
                font=("Helvetica", 10),
                width=24, height=24, corner_radius=4,
                command=lambda idx=i: self._toggle_visibility(idx)
            )
            vis_btn.pack(side="right", padx=(2, 0))

            if not is_active:
                item.bind("<Button-1>", lambda e, idx=i: self._on_layer_click(idx))
                label.bind("<Button-1>", lambda e, idx=i: self._on_layer_click(idx))
                inner.bind("<Button-1>", lambda e, idx=i: self._on_layer_click(idx))

            self.layer_widgets.append(item)

    def _toggle_visibility(self, index):
        if 0 <= index < len(self.layer_manager.layers):
            self.layer_manager.layers[index].visible = not self.layer_manager.layers[index].visible
            self._update_layer_list()
            self._render_canvas()

    def _render_canvas(self):
        self.canvas.delete("all")
        composite = self.layer_manager.get_composite_image()
        self.tk_image = ImageTk.PhotoImage(composite)
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

    def _assemble(self):
        if len(self.layer_manager.layers) < 1:
            messagebox.showwarning("Предупреждение", "Создайте хотя бы один слой.")
            return

        output_dir = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))), "output")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "preview.gif")

        layer_images = self.layer_manager.get_layer_images_for_gif()

        success = build_gif_from_layers(
            layer_images, output_path,
            duration=500,
            quantize=False,
            colors=256,
            quantize_alg="Median Cut"
        )

        if success:
            info = {
                "Кадров": len(layer_images),
                "Размер файла": get_gif_file_size(output_path),
            }
            self.on_preview(output_path, info)
        else:
            messagebox.showerror("Ошибка", "Не удалось создать GIF.")
