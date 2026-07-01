from PIL import Image, ImageDraw


class Layer:
    def __init__(self, width, height, name="Слой"):
        self.name = name
        self.width = width
        self.height = height
        self.image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        self.visible = True
        self.opacity = 255

    def get_draw(self):
        return ImageDraw.Draw(self.image)

    def clear(self):
        self.image = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))


class LayerManager:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.layers = []
        self.active_index = 0
        self._add_layer("Фон")

    def _add_layer(self, name):
        layer = Layer(self.width, self.height, name)
        self.layers.append(layer)
        return layer

    def add_layer(self, name=None):
        idx = len(self.layers)
        if name is None:
            name = f"Слой {idx}"
        layer = Layer(self.width, self.height, name)
        self.layers.append(layer)
        self.active_index = len(self.layers) - 1
        return layer

    def remove_layer(self, index):
        if len(self.layers) <= 1:
            return False
        if 0 <= index < len(self.layers):
            self.layers.pop(index)
            if self.active_index >= len(self.layers):
                self.active_index = len(self.layers) - 1
            return True
        return False

    def get_active_layer(self):
        if 0 <= self.active_index < len(self.layers):
            return self.layers[self.active_index]
        return None

    def get_composite_image(self):
        composite = Image.new("RGBA", (self.width, self.height), (255, 255, 255, 255))
        for layer in self.layers:
            if layer.visible:
                composite = Image.alpha_composite(composite, layer.image)
        return composite

    def get_layer_images_for_gif(self):
        images = []
        for layer in self.layers:
            img = Image.new("RGBA", (self.width, self.height), (255, 255, 255, 255))
            if layer.visible:
                img = Image.alpha_composite(img, layer.image)
            images.append(img)
        return images

    def reorder_layer(self, old_index, new_index):
        if 0 <= old_index < len(self.layers) and 0 <= new_index < len(self.layers):
            layer = self.layers.pop(old_index)
            self.layers.insert(new_index, layer)
            self.active_index = new_index
            return True
        return False

    def duplicate_layer(self, index):
        if 0 <= index < len(self.layers):
            original = self.layers[index]
            new_layer = Layer(self.width, self.height, f"{original.name} копия")
            new_layer.image = original.image.copy()
            new_layer.visible = original.visible
            self.layers.insert(index + 1, new_layer)
            self.active_index = index + 1
            return new_layer
        return None
