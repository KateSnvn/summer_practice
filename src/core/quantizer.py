from PIL import Image


def quantize_image(image, colors=256, method="Median Cut"):
    if method == "Median Cut":
        if image.mode == "RGBA":
            rgb = Image.new("RGB", image.size, (255, 255, 255))
            rgb.paste(image, mask=image.split()[3])
            return rgb.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
        return image.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
    elif method == "Octree":
        rgb = image.convert("RGB")
        return rgb.quantize(colors=colors, method=Image.Quantize.FASTOCTREE)
    elif method == "Fast Octree":
        try:
            if image.mode == "RGBA":
                return image.quantize(colors=colors, method=Image.Quantize.LIBIMAGEQUANT)
            rgb = image.convert("RGB")
            return rgb.quantize(colors=colors, method=Image.Quantize.LIBIMAGEQUANT)
        except ValueError:
            rgb = image.convert("RGB")
            return rgb.quantize(colors=colors, method=Image.Quantize.FASTOCTREE)
    else:
        return image.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)


def quantize_frame(frame, colors=256, method="Median Cut"):
    quantized = quantize_image(frame, colors, method)
    return quantized.convert("RGBA")
