import os
import sys
from PIL import Image
import customtkinter as ctk

class ResourceManager:
    def __init__(self):
        self.icons = {}

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        full_path = os.path.normpath(os.path.join(base_path, relative_path))
        return full_path

    def load_png(self, image_path, size=(20, 20)):
        try:
            png_path = image_path
            if png_path.endswith('.svg'):
                png_path = png_path.replace('.svg', '.png')
            png_path = self.resource_path(png_path)
            
            if os.path.exists(png_path):
                img = Image.open(png_path)
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                img = img.resize(size, Image.LANCZOS)
                return ctk.CTkImage(light_image=img, dark_image=img, size=size)
            print(f"Arquivo PNG não encontrado: {png_path}")
            empty_img = Image.new("RGBA", size, (0, 0, 0, 0))
            return ctk.CTkImage(light_image=empty_img, dark_image=empty_img, size=size)
        except Exception as e:
            print(f"Erro ao carregar imagem {image_path}: {e}")
            empty_img = Image.new("RGBA", size, (0, 0, 0, 0))
            return ctk.CTkImage(light_image=empty_img, dark_image=empty_img, size=size)

    def load_icons(self):
        icon_list = [
            ("logo", "assets/icon.png", (42, 42)),
            ("minimize", "assets/icons/icon_minimize.png", (20, 20)),
            ("maximize", "assets/icons/icon_maximize.png", (20, 20)),
            ("close", "assets/icons/icon_close.png", (20, 20)),
            ("home", "assets/icons/cil-home.png", (20, 20)),
            ("search", "assets/icons/cil-magnifying-glass.png", (20, 20)),
            ("settings", "assets/icons/icon_settings.png", (20, 20)),
            ("paste", "assets/icons/cil-clipboard.png", (20, 20)),
            ("download", "assets/icons/cil-cloud-download.png", (20, 20)),
            ("restart", "assets/icons/cil-reload.png", (20, 20)),
            ("remove", "assets/icons/cil-remove.png", (20, 20)),
            ("select", "assets/icons/cil-check-circle.png", (20, 20)),
            ("info", "assets/icons/cil-info.png", (20, 20)),
            ("downloads", "assets/icons/downloads.png", (20, 20)),
        ]
        for name, path, size in icon_list:
            self.icons[name] = self.load_png(path, size)
        return self.icons