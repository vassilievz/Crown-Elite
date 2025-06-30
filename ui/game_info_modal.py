import customtkinter as ctk
from PIL import Image
from io import BytesIO
import urllib.request
import aiohttp
import asyncio
import re

class GameInfoModal(ctk.CTkToplevel):
    def __init__(self, parent, appid, game_name, api_client):
        super().__init__(parent)
        self.geometry("700x500")
        self.resizable(False, False)
        self.configure(fg_color="#1A1A2E")
        self.attributes("-topmost", True)
        self.overrideredirect(True)
        self.lift()
        self.grab_set()
        self.api_client = api_client
        self.appid = appid
        self.game_name = game_name
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.setup_ui()
        self.load_game_info()
        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.on_drag)

    def start_drag(self, event):
        self.drag_start_x = event.x_root - self.winfo_x()
        self.drag_start_y = event.y_root - self.winfo_y()

    def on_drag(self, event):
        x = event.x_root - self.drag_start_x
        y = event.y_root - self.drag_start_y
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color="#1A1A2E")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        self.content_frame = ctk.CTkScrollableFrame(main_frame, fg_color="#262640", corner_radius=10, border_width=2, border_color="#4A4A78")
        self.content_frame.pack(fill="both", expand=True)
        self.title_label = ctk.CTkLabel(self.content_frame, text=self.game_name, text_color="#FF4D4D", font=("Segoe UI", 26, "bold"))
        self.title_label.pack(pady=(15, 5), padx=15, anchor="w")
        self.appid_label = ctk.CTkLabel(self.content_frame, text=f"AppID: {self.appid}", text_color="#A3A3A3", font=("Segoe UI", 14, "italic"))
        self.appid_label.pack(pady=(0, 15), padx=15, anchor="w")
        self.image_label = ctk.CTkLabel(self.content_frame, text="")
        self.image_label.pack(pady=10, padx=15)
        self.desc_label = ctk.CTkLabel(self.content_frame, text="Carregando descrição...", text_color="#F5F5F5", font=("Segoe UI", 15), wraplength=580, justify="left", anchor="w")
        self.desc_label.pack(pady=(5, 10), padx=20, fill="x", expand=True)
        self.drm_label = ctk.CTkLabel(self.content_frame, text="Verificando DRM...", text_color="#F5F5F5", font=("Segoe UI", 16, "bold"))
        self.drm_label.pack(pady=(5, 10), padx=20, anchor="w")
        self.requirements_label = ctk.CTkLabel(self.content_frame, text="Carregando requisitos...", text_color="#F5F5F5", font=("Segoe UI", 16), wraplength=580, justify="left", anchor="w")
        self.requirements_label.pack(pady=(5, 10), padx=20, fill="x", expand=True)
        close_button = ctk.CTkButton(main_frame, text="Fechar", command=self.destroy, fg_color="#FF4D4D", hover_color="#FF6666", corner_radius=10, font=("Segoe UI", 16, "bold"), text_color="#FFFFFF", height=40, width=200)
        close_button.pack(pady=(10, 20))

    def load_game_info(self):
        asyncio.run(self.async_load_game_info())

    async def async_load_game_info(self):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
            }

            url = f"https://store.steampowered.com/api/appdetails?appids={self.appid}&l=portuguese"
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data[self.appid]["success"]:
                            game_data = data[self.appid]["data"]
                            if not game_data.get("short_description") or game_data.get("short_description") == "":
                                game_data["short_description"] = game_data.get("about_the_game", "Descrição não disponível")
                                url_pt_br = f"https://store.steampowered.com/api/appdetails?appids={self.appid}&l=brazilian"
                                async with session.get(url_pt_br) as response_pt_br:
                                    if response_pt_br.status == 200:
                                        data_pt_br = await response_pt_br.json()
                                        if data_pt_br[self.appid]["success"]:
                                            game_data_pt_br = data_pt_br[self.appid]["data"]
                                            game_data["short_description"] = game_data_pt_br.get("short_description", game_data.get("short_description", "Descrição não disponível"))
                            self.update_game_info(game_data)
                        else:
                            self.show_error("Erro ao carregar informações do jogo")
                    else:
                        self.show_error("Erro ao carregar informações do jogo")
        except Exception as e:
            self.show_error(f"Erro ao carregar informações: {str(e)}")

    def clean_html(self, html_text):
        if not html_text or html_text == "Não especificado":
            return ["Não especificado"]
        html_text = html_text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
        clean_text = re.sub(r"<[^>]+>", "", html_text)
        lines = [line.strip() for line in clean_text.split("\n") if line.strip()]
        lines = [line for line in lines if not line.startswith(("Mínimos:", "Recomendados:"))]
        if not lines:
            return ["Não especificado"]
        return lines

    def format_requirements(self, requirements_list):
        if not requirements_list or requirements_list == ["Não especificado"]:
            return "Não especificado"
        formatted_lines = []
        for line in requirements_list:
            line = line.strip()
            if not line:
                continue
            if ":" in line:
                key, value = [part.strip() for part in line.split(":", 1)]
                formatted_lines.append(f"• {key}: {value}")
            else:
                formatted_lines.append(f"• {line}")
        return "\n".join(formatted_lines)

    def update_game_info(self, game_data):
        try:
            if game_data.get("header_image"):
                with urllib.request.urlopen(game_data["header_image"]) as response:
                    img_data = response.read()
                img = Image.open(BytesIO(img_data))
                img = img.resize((400, 225), Image.LANCZOS)
                photo = ctk.CTkImage(light_image=img, dark_image=img, size=(400, 225))
                self.image_label.configure(image=photo)
        except Exception:
            self.image_label.configure(text="Erro ao carregar imagem")
        desc = game_data.get("short_description", "Descrição não disponível")
        self.desc_label.configure(text=desc)
        drm_notice = game_data.get("drm_notice", "")
        if drm_notice:
            self.drm_label.configure(text=f"DRM: {drm_notice}", text_color="#FF4D4D")
        else:
            self.drm_label.configure(text="DRM: Não possui DRM Denuvo", text_color="#66FF66")
        pc_requirements = game_data.get("pc_requirements", {})
        if pc_requirements:
            minimum_raw = pc_requirements.get("minimum", "")
            if minimum_raw:
                minimum_lines = self.clean_html(minimum_raw)
                minimum_formatted = self.format_requirements(minimum_lines)
            else:
                minimum_formatted = "Não especificado"
            recommended_raw = pc_requirements.get("recommended", "")
            if recommended_raw:
                recommended_lines = self.clean_html(recommended_raw)
                recommended_formatted = self.format_requirements(recommended_lines)
            else:
                recommended_formatted = "Não especificado"
            requirements_text = f"MÍNIMOS:\n{minimum_formatted}\n\nRECOMENDADOS:\n{recommended_formatted}"
        else:
            requirements_text = "Requisitos não disponíveis"
        self.requirements_label.configure(text=requirements_text)

    def show_error(self, message):
        self.desc_label.configure(text=message, text_color="#FF4D4D")
        self.drm_label.configure(text="")
        self.requirements_label.configure(text="")
