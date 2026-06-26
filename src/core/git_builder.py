import os
from PIL import Image
from src.core.stabilizer import stabilize_frames
from src.core.quantizer import quantize_frame


def build_gif_from_images(images, output_path, duration=500, loop=0,
                          stabilize=False, stabilization_alg="ECC", smoothing=0.5,
                          quantize=False, colors=256, quantize_alg="Median Cut",
                          progress_callback=None):
    frames = [img.copy().convert("RGBA") for img in images]

    total = len(frames)
    if total == 0:
        return False

    if stabilize and total > 1:
        frames = stabilize_frames(frames, stabilization_alg, smoothing)

    if quantize:
        quantized = []
        for i, frame in enumerate(frames):
            if progress_callback:
                progress_callback(int((i / total) * 50) + 50)
            q = quantize_frame(frame, colors, quantize_alg)
            quantized.append(q.convert("RGBA"))
        frames = quantized

    pil_frames = []
    for frame in frames:
        if frame.mode != "P":
            f = frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)
        else:
            f = frame
        pil_frames.append(f)

    if not pil_frames:
        return False

    pil_frames[0].save(
        output_path,
        save_all=True,
        append_images=pil_frames[1:],
        duration=duration,
        loop=loop,
        optimize=True
    )

    return True


def build_gif_from_layers(layers, output_path, duration=500, loop=0,
                          quantize=False, colors=256, quantize_alg="Median Cut",
                          stabilize=False, stabilization_alg="ECC", smoothing=0.5,
                          progress_callback=None):
    frames = [layer.copy().convert("RGBA") for layer in layers if layer is not None]

    if not frames:
        return False

    total = len(frames)

    if stabilize and total > 1:
        frames = stabilize_frames(frames, stabilization_alg, smoothing)

    if quantize:
        quantized = []
        for i, frame in enumerate(frames):
            if progress_callback:
                progress_callback(int((i / total) * 50) + 50)
            q = quantize_frame(frame, colors, quantize_alg)
            quantized.append(q.convert("RGBA"))
        frames = quantized

    pil_frames = []
    for frame in frames:
        if frame.mode != "P":
            f = frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)
        else:
            f = frame
        pil_frames.append(f)

    pil_frames[0].save(
        output_path,
        save_all=True,
        append_images=pil_frames[1:],
        duration=duration,
        loop=loop,
        optimize=True
    )

    return True


def get_gif_file_size(path):
    if os.path.exists(path):
        size = os.path.getsize(path)
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.2f} MB"
    return "N/A"
