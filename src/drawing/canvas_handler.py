import math
from PIL import Image, ImageDraw, ImageFilter
from src.drawing.tools import Tool, ShapeType


class CanvasHandler:
    def __init__(self, layer_manager):
        self.layer_manager = layer_manager
        self.tool = Tool.BRUSH
        self.shape_type = ShapeType.RECTANGLE
        self.brush_color = "#000000"
        self.brush_size = 3
        self.eraser_size = 10
        self.last_x = None
        self.last_y = None
        self.start_x = None
        self.start_y = None
        self.drawing = False

    def set_tool(self, tool):
        self.tool = tool

    def set_shape(self, shape_type):
        self.shape_type = shape_type

    def set_color(self, color):
        self.brush_color = color

    def set_brush_size(self, size):
        self.brush_size = size

    def set_eraser_size(self, size):
        self.eraser_size = size

    def on_mouse_down(self, event):
        self.drawing = True
        self.last_x = event.x
        self.last_y = event.y
        self.start_x = event.x
        self.start_y = event.y

        if self.tool == Tool.FILL:
            self._flood_fill(event.x, event.y)
            self.drawing = False

    def on_mouse_move(self, event):
        if not self.drawing:
            return
        if self.tool in (Tool.BRUSH, Tool.ERASER):
            self._draw_line(event.x, event.y)
        self.last_x = event.x
        self.last_y = event.y

    def on_mouse_up(self, event):
        if not self.drawing:
            return
        if self.tool == Tool.SHAPE:
            self._draw_shape(self.start_x, self.start_y, event.x, event.y)
        self.drawing = False
        self.last_x = None
        self.last_y = None
        self.start_x = None
        self.start_y = None

    def _draw_line(self, x, y):
        layer = self.layer_manager.get_active_layer()
        if layer is None:
            return
        draw = layer.get_draw()
        if self.tool == Tool.BRUSH:
            if self.last_x is not None and self.last_y is not None:
                draw.line([(self.last_x, self.last_y), (x, y)],
                        fill=self.brush_color, width=self.brush_size, joint="curve")
        elif self.tool == Tool.ERASER:
            if self.last_x is not None and self.last_y is not None:
                draw.line([(self.last_x, self.last_y), (x, y)],
                        fill=(0, 0, 0, 0), width=self.eraser_size, joint="curve")

    def _draw_shape(self, x1, y1, x2, y2):
        layer = self.layer_manager.get_active_layer()
        if layer is None:
            return
        draw = layer.get_draw()
        left, right = min(x1, x2), max(x1, x2)
        top, bottom = min(y1, y2), max(y1, y2)
        if self.shape_type == ShapeType.RECTANGLE:
            draw.rectangle([left, top, right, bottom], outline=self.brush_color, width=self.brush_size)
        elif self.shape_type == ShapeType.OVAL:
            draw.ellipse([left, top, right, bottom], outline=self.brush_color, width=self.brush_size)
        elif self.shape_type == ShapeType.LINE:
            draw.line([(x1, y1), (x2, y2)], fill=self.brush_color, width=self.brush_size)
        elif self.shape_type == ShapeType.TRIANGLE:
            cx = (x1 + x2) // 2
            draw.polygon([(cx, y1), (x1, y2), (x2, y2)],
                        outline=self.brush_color, width=self.brush_size)
        elif self.shape_type == ShapeType.HEART:
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            rx = max(abs(x2 - x1) / 2, 1)
            ry = max(abs(y2 - y1) / 2, 1)
            heart_pts = []
            for i in range(120):
                t = 2 * math.pi * i / 120
                x = cx + rx * math.sin(t) ** 3
                y = cy - ry * (13 * math.cos(t) - 5 * math.cos(2 * t)
                               - 2 * math.cos(3 * t) - math.cos(4 * t)) / 17
                heart_pts.append((x, y))
            draw.polygon(heart_pts, outline=self.brush_color, width=self.brush_size)
        elif self.shape_type == ShapeType.STAR:
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            outer_r = max(min(abs(x2 - x1), abs(y2 - y1)) / 2, 1)
            inner_r = outer_r * 0.4
            star_pts = []
            for i in range(5):
                angle = math.radians(-90 + i * 72)
                star_pts.append((cx + outer_r * math.cos(angle),
                                 cy + outer_r * math.sin(angle)))
                angle = math.radians(-90 + i * 72 + 36)
                star_pts.append((cx + inner_r * math.cos(angle),
                                 cy + inner_r * math.sin(angle)))
            draw.polygon(star_pts, outline=self.brush_color, width=self.brush_size)

    def _flood_fill(self, x, y):
        layer = self.layer_manager.get_active_layer()
        if layer is None:
            return
        w, h = layer.image.size
        if x < 0 or x >= w or y < 0 or y >= h:
            return

        try:
            ImageDraw.floodfill(layer.image, (x, y), self._hex_to_rgba(self.brush_color),
                                thresh=30)
        except Exception:
            pass

    def _hex_to_rgba(self, hex_color):
        h = hex_color.lstrip("#")
        r, g, b = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        return (r, g, b, 255)

    def pick_color(self, x, y):
        composite = self.layer_manager.get_composite_image()
        if 0 <= x < composite.width and 0 <= y < composite.height:
            pixel = composite.getpixel((x, y))
            r, g, b = pixel[0], pixel[1], pixel[2]
            self.brush_color = f"#{r:02x}{g:02x}{b:02x}"
            return self.brush_color
        return self.brush_color

    def apply_filter(self, filter_name):
        layer = self.layer_manager.get_active_layer()
        if layer is None:
            return

        img = layer.image.copy()
        has_alpha = img.mode == "RGBA"
        if has_alpha:
            alpha = img.split()[3]
            rgb = img.convert("RGB")
        else:
            rgb = img

        if filter_name == "Grayscale":
            rgb = rgb.convert("L").convert("RGB")
        elif filter_name == "Sepia":
            pixels = list(rgb.getdata())
            sepia = []
            for rv, gv, bv in pixels:
                nr = min(int(rv * 0.393 + gv * 0.769 + bv * 0.189), 255)
                ng = min(int(rv * 0.349 + gv * 0.686 + bv * 0.168), 255)
                nb = min(int(rv * 0.272 + gv * 0.534 + bv * 0.131), 255)
                sepia.append((nr, ng, nb))
            sepia_img = Image.new("RGB", rgb.size)
            sepia_img.putdata(sepia)
            rgb = sepia_img
        elif filter_name == "Invert":
            r, g, b = rgb.split()
            rgb = Image.merge("RGB", (
                r.point(lambda x: 255 - x),
                g.point(lambda x: 255 - x),
                b.point(lambda x: 255 - x)
            ))
        elif filter_name == "Blur":
            rgb = rgb.filter(ImageFilter.BLUR)
        elif filter_name == "Sharpen":
            rgb = rgb.filter(ImageFilter.SHARPEN)
        elif filter_name == "Emboss":
            rgb = rgb.filter(ImageFilter.EMBOSS)

        if has_alpha:
            rgb = rgb.convert("RGBA")
            rgb.putalpha(alpha)

        layer.image = rgb

    def rotate(self, direction):
        layer = self.layer_manager.get_active_layer()
        if layer is None:
            return
        if direction == "left":
            layer.image = layer.image.rotate(90, expand=True)
        elif direction == "right":
            layer.image = layer.image.rotate(-90, expand=True)

    def flip(self, direction):
        layer = self.layer_manager.get_active_layer()
        if layer is None:
            return
        if direction == "horizontal":
            layer.image = layer.image.transpose(Image.FLIP_LEFT_RIGHT)
        elif direction == "vertical":
            layer.image = layer.image.transpose(Image.FLIP_TOP_BOTTOM)

    def paste_image(self, pil_image, x, y):
        layer = self.layer_manager.get_active_layer()
        if layer is None:
            return
        if pil_image.mode != "RGBA":
            pil_image = pil_image.convert("RGBA")
        layer.image.paste(pil_image, (x, y), pil_image)
