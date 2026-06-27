import os
from tkinter import filedialog, messagebox
from PIL import Image


def select_image_files():
    paths = filedialog.askopenfilenames(
        title="Выберите изображения",
        filetypes=[
            ("Изображения", "*.png *.jpg *.jpeg *.bmp *.tiff *.webp"),
            ("Все файлы", "*.*")
        ]
    )
    return list(paths)


def select_single_image():
    path = filedialog.askopenfilename(
        title="Выберите изображение",
        filetypes=[
            ("Изображения", "*.png *.jpg *.jpeg *.bmp *.tiff *.webp"),
            ("Все файлы", "*.*")
        ]
    )
    return path


def save_gif_file():
    path = filedialog.asksaveasfilename(
        title="Сохранить GIF",
        defaultextension=".gif",
        filetypes=[("GIF", "*.gif")]
    )
    return path


def load_image_safe(path):
    try:
        img = Image.open(path).convert("RGBA")
        return img
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить {os.path.basename(path)}:\n{e}")
        return None
