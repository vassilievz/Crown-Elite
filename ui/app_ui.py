import asyncio
import aiohttp
import threading
import json
import sys
import os
import ctypes
from functools import partial
from tkinter import END, Text, Scrollbar, messagebox
import customtkinter as ctk
from pathlib import Path
from PIL import Image
import urllib.request
from io import BytesIO
import requests
import io

from ui.themes import get_theme
from ui.ui_window_manager import WindowManager
from ui.ui_theme_manager import ThemeManager
from ui.ui_rate_limit_manager import RateLimitManager
from ui.ui_game_remover import GameRemover
from ui.ui_resource_manager import ResourceManager
from ui.ui_download_manager import DownloadManager
from ui.ui_game_search_manager import GameSearchManager
from ui.app_logic import async_download_and_process

ctk.set_appearance_mode("dark")

CORES = get_theme()["colors"]

class ManifestDownloader(ctk.CTk):
    def __init__(self, steam_path, api_client):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
            
        super().__init__()
        self.title("Crown EliTe")
        self.geometry("1280x720")
        self.minsize(940, 560)
        self.resizable(True, True)
        self.configure(fg_color=CORES["background"])
        self.overrideredirect(True)
        

        self.window_manager = WindowManager(self)
        self.theme_manager = ThemeManager(self)
        self.rate_limit_manager = RateLimitManager(self)
        self.game_remover = GameRemover(self, steam_path, CORES)
        self.resource_manager = ResourceManager()
        self.icons = self.resource_manager.load_icons()
        self.download_manager = DownloadManager(self, steam_path)
        self._set_appearance()
        icon_path = self.resource_manager.resource_path("assets/icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception as e:
                print(f"Erro ao definir o ícone da barra de tarefas: {e}")
        else:
            print(f"Ícone não encontrado: {icon_path}")
        
        self.game_search_manager = GameSearchManager(self, self.icons, CORES)
        self.steam_path = steam_path
        self.api_client = api_client
        self.appid_to_game = {}
        self.selected_games = {}
        self.search_thread = None
        self.cancel_search = False
        self.current_row = 0
        self.current_column = 0
        
        self.update_queue = []
        self.update_id = None
        self.asyncio_loop = None
        self.destroyed = False
        self.dpi_check_id = None
        self.after(100, self.process_updates)
        
        self.setup_ui()
        
        self.api_client.set_ui_callback(self.rate_limit_manager.update_rate_limit_indicator)

        self.protocol("WM_DELETE_WINDOW", self.window_manager.on_closing)

    def process_updates(self):
        while self.update_queue:
            widget, config = self.update_queue.pop(0)
            try:
                if widget and widget.winfo_exists():
                    widget.configure(**config)
            except Exception:
                pass
        self.update_id = self.after(100, self.process_updates) if not self.destroyed else None

    def safe_update(self, widget, **config):
        self.update_queue.append((widget, config))

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
        icons = {}
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
            icons[name] = self.load_png(path, size)
        return icons

    def _set_appearance(self):
        self.option_add("*Font", ("Segoe UI", 10))
        self.option_add("*Button.relief", "flat")
        self.option_add("*Entry.relief", "flat")

    def toggle_theme(self):
        global CORES
        CORES = toggle_theme()["colors"]
        ctk.set_appearance_mode("light" if ctk.get_appearance_mode() == "dark" else "dark")
        self.update_theme()

    def add_log(self, message):
        """Adiciona uma mensagem ao log"""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
    
    def clear_log(self):
        """Limpa o conteúdo do log"""
        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.configure(state="disabled")
    
    def update_theme(self):
        self.configure(fg_color=CORES["background"])
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                if "main_layout" in str(widget):
                    widget.configure(fg_color=CORES["background"])
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkFrame):
                            if "header_frame" in str(child):
                                child.configure(fg_color=CORES["secondary"])
                                for header_child in child.winfo_children():
                                    if isinstance(header_child, ctk.CTkFrame):
                                        header_child.configure(fg_color=CORES["secondary"])
                            elif "body_frame" in str(child):
                                child.configure(fg_color=CORES["background"])
                                for body_child in child.winfo_children():
                                    if isinstance(body_child, ctk.CTkFrame):
                                        if "left_menu" in str(body_child):
                                            body_child.configure(fg_color=CORES["secondary"])
                                        elif "content_frame" in str(body_child):
                                            body_child.configure(fg_color=CORES["background"])

    def setup_ui(self):
        main_layout = ctk.CTkFrame(self, fg_color=CORES["background"])
        main_layout.pack(fill="both", expand=True, padx=10, pady=10)
        
        header_frame = ctk.CTkFrame(main_layout, fg_color=CORES["secondary"], height=50, corner_radius=0)
        header_frame.pack(fill="x")
        
        logo_frame = ctk.CTkFrame(header_frame, fg_color=CORES["secondary"])
        logo_frame.pack(side="left", padx=(10, 0))
        
        logo_label = ctk.CTkLabel(logo_frame, text="", image=self.icons["logo"], fg_color=CORES["accent"])
        logo_label.pack(side="left", padx=(0, 10))
        
        title_label = ctk.CTkLabel(logo_frame, text="Crown EliTe", text_color=CORES["text"], font=("Segoe UI", 16, "bold"))
        title_label.pack(side="left")
        
        subtitle_label = ctk.CTkLabel(logo_frame, text="Se você vazar, eu vazarei seus dados.", text_color=CORES["text_secondary"], font=("Segoe UI", 10))
        subtitle_label.pack(side="left", padx=(10, 0))
        header_frame.bind("<Button-1>", self.start_drag)
        header_frame.bind("<B1-Motion>", self.on_drag)
        logo_frame.bind("<Button-1>", self.start_drag)
        logo_frame.bind("<B1-Motion>", self.on_drag)
        title_label.bind("<Button-1>", self.start_drag)
        title_label.bind("<B1-Motion>", self.on_drag)
        subtitle_label.bind("<Button-1>", self.start_drag)
        subtitle_label.bind("<B1-Motion>", self.on_drag)
        header_buttons = ctk.CTkFrame(header_frame, fg_color=CORES["accent"])
        header_buttons.pack(side="right", padx=(0, 10))
        
        button_size = 28
        button_style = {
            "fg_color": "transparent",
            "hover_color": CORES["hover"],
            "width": button_size,
            "height": button_size,
            "corner_radius": 5,
            "border_width": 0
        }
        
        minimize_btn = ctk.CTkButton(
            header_buttons, text="", image=self.icons["minimize"],
            command=self.minimize, **button_style
        )
        minimize_btn.pack(side="left", padx=2, pady=2)
        
        maximize_btn = ctk.CTkButton(
            header_buttons, text="", image=self.icons["maximize"],
            command=self.maximize_restore, **button_style
        )
        maximize_btn.pack(side="left", padx=2, pady=2)
        
        close_btn = ctk.CTkButton(
            header_buttons, text="", image=self.icons["close"],
            command=self.on_closing, **button_style
        )
        close_btn.pack(side="left", padx=2, pady=2)
        body_frame = ctk.CTkFrame(main_layout, fg_color=CORES["background"])
        body_frame.pack(fill="both", expand=True)
        
        left_menu = ctk.CTkFrame(body_frame, fg_color=CORES["secondary"], width=60, corner_radius=0)
        left_menu.pack(side="left", fill="y")
        
        menu_buttons = [
            ("Início", self.icons["home"], lambda: self.switch_page("home")),
            ("Buscar", self.icons["search"], lambda: self.switch_page("search")),
            ("Atualizar", self.icons["downloads"], lambda: self.switch_page("updater")),
        ]
        
        menu_button_style = {
            "fg_color": "transparent",
            "hover_color": CORES["hover"],
            "width": 60,
            "height": 45,
            "corner_radius": 0,
            "border_width": 0
        }
        
        for text, icon, command in menu_buttons:
            btn = ctk.CTkButton(
                left_menu,
                text="",
                image=icon,
                command=command,
                **menu_button_style
            )
            btn.pack(pady=5)
        
        theme_button = ctk.CTkButton(
            left_menu,
            text="",
            image=self.icons["settings"],
            command=self.toggle_theme,
            **menu_button_style
        )
        theme_button.pack(side="bottom", pady=10)
        
        self.content_frame = ctk.CTkFrame(body_frame, fg_color=CORES["background"])
        self.content_frame.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self.pages = {}
        from ui.updater_page import UpdaterPage
        
        self.setup_home_page()
        self.setup_search_page()
        self.setup_settings_page()
        
        updater_page = UpdaterPage(self.content_frame, self.icons["downloads"], self.steam_path)
        self.pages["updater"] = updater_page
        
        self.switch_page("search")
        footer_frame = ctk.CTkFrame(main_layout, fg_color=CORES["secondary"], height=22, corner_radius=0)
        footer_frame.pack(fill="x")
        credits_label = ctk.CTkLabel(footer_frame, text="By: Crown System", text_color=CORES["text_secondary"], font=("Segoe UI", 11))
        credits_label.pack(side="left", padx=10)
        
        self.rate_limit_label = ctk.CTkLabel(footer_frame, text="API: N/A", text_color=CORES["text_secondary"], font=("Segoe UI", 11))
        self.rate_limit_label.pack(side="left", padx=10)
        self.rate_limit_manager.set_rate_limit_label(self.rate_limit_label)
        
        discord_label = ctk.CTkLabel(footer_frame, text="Discord: Crown", text_color=CORES["text_secondary"], font=("Segoe UI", 11))
        discord_label.pack(side="left", padx=10)
        
        version_label = ctk.CTkLabel(footer_frame, text="v1.0.1", text_color=CORES["text_secondary"], font=("Segoe UI", 11))
        version_label.pack(side="right", padx=10)

    def start_drag(self, event):
        self.drag_start_x = event.x_root - self.winfo_x()
        self.drag_start_y = event.y_root - self.winfo_y()

    def on_drag(self, event):
        x = event.x_root - self.drag_start_x
        y = event.y_root - self.drag_start_y
        self.geometry(f"+{x}+{y}")

    def setup_home_page(self):
        page = ctk.CTkFrame(self.content_frame, fg_color=CORES["background"])
        self.pages["home"] = page
        
        label = ctk.CTkLabel(page, text="Bem-vindo ao Crown EliTe", text_color=CORES["text"], font=("Segoe UI", 20, "bold"))
        label.pack(pady=20)
        
        desc = ctk.CTkLabel(page, text="Um baixador de jogos moderno com uma interface elegante.\nSelecione 'Buscar' no menu para encontrar e baixar jogos.", text_color=CORES["text_secondary"], font=("Segoe UI", 14))
        desc.pack(pady=10)
        
        terms_frame = ctk.CTkFrame(page, fg_color=CORES["secondary"], corner_radius=10)
        terms_frame.pack(pady=20, padx=30, fill="x")
        
        terms_title = ctk.CTkLabel(terms_frame, text="TERMOS DE USO - ACESSO VIP", text_color=CORES["accent"], font=("Segoe UI", 16, "bold"))
        terms_title.pack(pady=(15,5))
        
        terms_text = """AVISO IMPORTANTE:
• Este software é exclusivo para DOADORES AUTORIZADOS
• Compartilhamento ou vazamento resultará em:
  - Banimento permanente e irrevogável
  - Bloqueio total do acesso VIP
  - Possível responsabilização legal
• Todo acesso é monitorado e possui identificação única
• Ao utilizar, você concorda com estes termos"""
        
        terms_label = ctk.CTkLabel(terms_frame, text=terms_text, text_color=CORES["text"], font=("Segoe UI", 12))
        terms_label.pack(pady=(5,15))

        
        community_frame = ctk.CTkFrame(page, fg_color=CORES["secondary"], corner_radius=10, border_width=2, border_color=CORES["border"])
        community_frame.pack(pady=15, padx=30, fill="x")
        
        community_title = ctk.CTkLabel(community_frame, text="Desenvolvido por Crown System", text_color=CORES["text"], font=("Segoe UI", 16, "bold"))
        community_title.pack(pady=(15, 5), padx=15)
        
        about_text = "Crown EliTe é uma ferramenta poderosa projetada para baixar manifestos de jogos diretamente do Steam.\n"
        about_text += "Permite que você pesquise jogos por nome ou AppID, baixe seus manifestos e reinicie o Steam para aplicar as alterações."
        about_text += "\n\nComo usar:\n"
        about_text += "1. Vá para a página de Busca\n"
        about_text += "2. Digite o nome do jogo ou AppID\n"
        about_text += "3. Selecione o jogo nos resultados da busca\n"
        about_text += "4. Clique no botão de download para obter o manifesto\n"
        about_text += "5. Reinicie o Steam quando solicitado"
        
        about_label = ctk.CTkLabel(community_frame, text=about_text, text_color=CORES["text_secondary"], font=("Segoe UI", 13), justify="left")
        about_label.pack(pady=10, padx=20, anchor="w")
        
        support_frame = ctk.CTkFrame(community_frame, fg_color=CORES["accent"], corner_radius=8)
        support_frame.pack(pady=(5, 15), padx=20, fill="x")
        
        support_label = ctk.CTkLabel(support_frame, text="Precisa de ajuda? Entre em nossa comunidade Discord para suporte:", text_color=CORES["text_secondary"], font=("Segoe UI", 13))
        support_label.pack(pady=(10, 5), padx=15)
        
        discord_label = ctk.CTkLabel(support_frame, text="https://discord.gg/crwn", text_color=CORES["text"], font=("Segoe UI", 14, "bold"))
        discord_label.pack(pady=(0, 10), padx=15)

    def setup_search_page(self):
        page = ctk.CTkFrame(self.content_frame, fg_color=CORES["background"])
        self.pages["search"] = page

        main_content = ctk.CTkFrame(page, fg_color=CORES["background"]) 
        main_content.pack(fill="both", expand=True, padx=(0, 10))

        input_frame = ctk.CTkFrame(main_content, corner_radius=5, fg_color=CORES["secondary"], border_width=1, border_color=CORES["border"])
        input_frame.pack(padx=0, pady=10, fill="x")
        input_label = ctk.CTkLabel(input_frame, text="Nome do Jogo ou AppID:", text_color=CORES["text_secondary"], font=("Segoe UI", 13))
        input_label.pack(padx=10, pady=5, anchor="w")
        self.game_input = ctk.CTkEntry(
            input_frame, placeholder_text="ex: 123456 ou Nome do Jogo", width=200, fg_color=CORES["secondary"],
            text_color=CORES["text_secondary"], border_color=CORES["secondary"], border_width=2, corner_radius=5,
            placeholder_text_color=CORES["text_secondary"], height=30, font=("Segoe UI", 13)
        )
        self.game_input.pack(padx=10, pady=5, side="left", expand=True, fill="x")
        button_style = {
            "width": 80, "height": 30, "fg_color": CORES["accent"], "hover_color": CORES["hover"],
            "corner_radius": 5, "font": ("Segoe UI", 13), "text_color": CORES["text_secondary"],
            "text_color_disabled": CORES["text_secondary"], "border_width": 2, "border_color": CORES["accent"]}
            
        paste_button = ctk.CTkButton(input_frame, text="", image=self.icons["paste"], command=self.game_search_manager.paste_from_clipboard, **button_style)
        paste_button.pack(padx=5, pady=5, side="left")
        search_button = ctk.CTkButton(input_frame, text="", image=self.icons["search"], command=self.game_search_manager.search_game, **button_style)
        search_button.pack(padx=5, pady=5, side="left")
        self.download_button = ctk.CTkButton(input_frame, text="", image=self.icons["download"], command=self.download_manager.download_manifest, state="disabled", **button_style)
        self.download_button.pack(padx=5, pady=5, side="left")
        self.restart_button = ctk.CTkButton(input_frame, text="", image=self.icons["restart"], command=self.download_manager.restart_steam, state="normal", **button_style)
        self.restart_button.pack(padx=5, pady=5, side="left")
        self.remove_button = ctk.CTkButton(input_frame, text="", image=self.icons["remove"], command=self.open_remove_game_dialog, **button_style)
        self.remove_button.pack(padx=5, pady=5, side="left")

        self.results_frame = ctk.CTkFrame(main_content, corner_radius=5, fg_color=CORES["secondary"], border_width=1, border_color=CORES["border"])
        self.results_frame.pack(padx=0, pady=10, fill="both", expand=True)
        self.results_label = ctk.CTkLabel(self.results_frame, text="Resultados da Busca", text_color=CORES["text_secondary"], font=("Segoe UI", 13))
        self.results_label.pack(padx=10, pady=5, anchor="w")
        self.results_container = ctk.CTkScrollableFrame(
            self.results_frame, fg_color=CORES["secondary"], scrollbar_button_color=CORES["accent"],
            scrollbar_button_hover_color=CORES["hover"], width=8
        )
        self.results_container.pack(padx=10, pady=5, fill="both", expand=True)
        self.results_container.grid_columnconfigure((0, 1, 2), weight=1, uniform="card")
        self.results_container.grid_rowconfigure(0, weight=0)

        self.log_frame = ctk.CTkFrame(main_content, corner_radius=5, fg_color=CORES["secondary"], border_width=1, border_color=CORES["border"], height=100)
        self.log_frame.pack(padx=0, pady=10, fill="x")
        self.log_frame.pack_propagate(False)
        
        log_header = ctk.CTkFrame(self.log_frame, fg_color="transparent")
        log_header.pack(fill="x", padx=10, pady=5)
        
        log_label = ctk.CTkLabel(log_header, text="Log de Instalação", text_color=CORES["text_secondary"], font=("Segoe UI", 13))
        log_label.pack(side="left")
        
        self.clear_log_button = ctk.CTkButton(
            log_header, text="Limpar", width=60, height=24,
            fg_color=CORES["accent"], hover_color=CORES["hover"],
            corner_radius=5, font=("Segoe UI", 11),
            command=self.clear_log
        )
        self.clear_log_button.pack(side="right")
        
        self.log_text = ctk.CTkTextbox(
            self.log_frame,
            fg_color=CORES["background"],
            text_color=CORES["text"],
            font=("Segoe UI", 12),
            wrap="word",
            height=60
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.log_text.configure(state="disabled")



    def update_theme(self):
        self.configure(fg_color=CORES["background"])
        
        def update_widget_colors(widget):
            if isinstance(widget, ctk.CTkFrame):
                if "secondary" in str(widget):
                    widget.configure(fg_color=CORES["secondary"])
                elif "accent" in str(widget):
                    widget.configure(fg_color=CORES["accent"])
                    widget.configure(fg_color=CORES["background"])
            elif isinstance(widget, ctk.CTkButton):
                if "transparent" in str(widget.cget("fg_color")):
                    widget.configure(
                        fg_color="transparent",
                        hover_color=CORES["hover"],
                        text_color=CORES["text"]
                    )
                    widget.configure(
                        fg_color=CORES["button"],
                        hover_color=CORES["button_hover"],
                        text_color=CORES["text"]
                    )
            elif isinstance(widget, ctk.CTkLabel):
                if "text_secondary" in str(widget):
                    widget.configure(text_color=CORES["text_secondary"])
                    widget.configure(text_color=CORES["text"])
            elif isinstance(widget, ctk.CTkEntry):
                widget.configure(
                    fg_color=CORES["input"],
                    text_color=CORES["text"],
                    border_color=CORES["border"]
                )
            elif isinstance(widget, Text):
                widget.configure(
                    bg=CORES["input"],
                    fg=CORES["text"]
                )
            
            for child in widget.winfo_children():
                update_widget_colors(child)
        
        update_widget_colors(self)

    def setup_settings_page(self):
        settings_page = ctk.CTkFrame(self.content_frame, fg_color=CORES["background"])
        self.pages["settings"] = settings_page

        title = ctk.CTkLabel(
            settings_page,
            text="Configurações",
            font=("Segoe UI", 24, "bold"),
            text_color=CORES["text"]
        )
        title.pack(anchor="w", padx=20, pady=(20, 10))

        theme_frame = ctk.CTkFrame(
            settings_page,
            fg_color=CORES["secondary"],
            corner_radius=10,
            border_width=1,
            border_color=CORES["border"]
        )
        theme_frame.pack(fill="x", padx=20, pady=20)

        theme_header = ctk.CTkFrame(theme_frame, fg_color="transparent")
        theme_header.pack(fill="x", padx=15, pady=(15, 5))

        theme_icon = ctk.CTkLabel(theme_header, text="🎨", font=("Segoe UI", 24))
        theme_icon.pack(side="left", padx=(0, 10))

        theme_title = ctk.CTkLabel(
            theme_header,
            text="Seleção de Tema",
            font=("Segoe UI", 18, "bold"),
            text_color=CORES["text"]
        )
        theme_title.pack(side="left")

        theme_description = ctk.CTkLabel(
            theme_frame,
            text="Escolha o tema da interface do aplicativo:",
            font=("Segoe UI", 13),
            text_color=CORES["text_secondary"]
        )
        theme_description.pack(anchor="w", padx=15, pady=(5, 15))

        themes_container = ctk.CTkFrame(theme_frame, fg_color="transparent")
        themes_container.pack(fill="x", padx=15, pady=(0, 15))

        def change_theme(theme_name):
            global CORES
            theme_data = get_theme(theme_name)
            if theme_data and "colors" in theme_data:
                CORES = theme_data["colors"]
                self.update_theme()
                for card in theme_cards:
                    card_theme = card["theme_id"]
                    card["frame"].configure(
                        border_width=2,
                        border_color=CORES["accent"] if card_theme == theme_name else "transparent"
                    )
                    card["select_btn"].configure(
                        state="disabled" if card_theme == theme_name else "normal",
                        text="Selecionado" if card_theme == theme_name else "Selecionar"
                    )

        from ui.themes import AVAILABLE_THEMES

        max_cols = 2
        row = 0
        col = 0
        theme_cards = []

        for theme_id, theme_data in AVAILABLE_THEMES.items():
            theme_button_frame = ctk.CTkFrame(
                themes_container,
                fg_color=theme_data["colors"]["secondary"],
                width=280,
                height=200,
                corner_radius=10,
                border_width=2,
                border_color=theme_data["colors"]["secondary"]
            )
            theme_button_frame.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
            theme_button_frame.grid_propagate(False)

            preview_container = ctk.CTkFrame(
                theme_button_frame,
                fg_color=theme_data["colors"]["background"],
                corner_radius=8
            )
            preview_container.pack(fill="x", padx=10, pady=10)

            preview_header = ctk.CTkFrame(
                preview_container,
                fg_color=theme_data["colors"]["secondary"],
                height=30,
                corner_radius=5
            )
            preview_header.pack(fill="x", padx=5, pady=5)

            preview_buttons = ctk.CTkFrame(
                preview_container,
                fg_color="transparent"
            )
            preview_buttons.pack(fill="x", padx=5, pady=5)

            ctk.CTkButton(
                preview_buttons,
                text="Botão Demo",
                width=100,
                height=30,
                fg_color=theme_data["colors"]["button"],
                hover_color=theme_data["colors"]["button_hover"],
                text_color=theme_data["colors"]["text"],
                corner_radius=5
            ).pack(side="left", padx=5)

            ctk.CTkButton(
                preview_buttons,
                text="Ação",
                width=80,
                height=30,
                fg_color=theme_data["colors"]["accent"],
                hover_color=theme_data["colors"]["hover"],
                text_color=theme_data["colors"]["text"],
                corner_radius=5
            ).pack(side="left", padx=5)

            theme_info = ctk.CTkFrame(
                theme_button_frame,
                fg_color="transparent"
            )
            theme_info.pack(fill="x", padx=10, pady=5)

            theme_name = ctk.CTkLabel(
                theme_info,
                text=theme_data["name"],
                font=("Segoe UI", 16, "bold"),
                text_color=theme_data["colors"]["text"]
            )
            theme_name.pack(anchor="w")

            select_btn = ctk.CTkButton(
                theme_button_frame,
                text="Selecionar",
                width=120,
                height=35,
                fg_color=theme_data["colors"]["button"],
                hover_color=theme_data["colors"]["button_hover"],
                text_color=theme_data["colors"]["text"],
                command=lambda t=theme_id: change_theme(t),
                corner_radius=5
            )
            select_btn.pack(pady=10)

            theme_cards.append({
                "theme_id": theme_id,
                "frame": theme_button_frame,
                "select_btn": select_btn
            })

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        themes_container.grid_columnconfigure(tuple(range(max_cols)), weight=1)
        current_theme = next((theme_id for theme_id, theme_data in AVAILABLE_THEMES.items()
                            if theme_data["colors"] == CORES), None)
        if current_theme:
            for card in theme_cards:
                if card["theme_id"] == current_theme:
                    card["frame"].configure(border_color=CORES["accent"])
                    card["select_btn"].configure(state="disabled", text="Selecionado")

        other_settings_frame = ctk.CTkFrame(settings_page, fg_color=CORES["secondary"], corner_radius=10)
        other_settings_frame.pack(fill="x", padx=20, pady=10)

        dev_message = ctk.CTkLabel(
            other_settings_frame,
            text="Mais opções de configurações estão em desenvolvimento.",
            font=("Segoe UI", 13),
            text_color=CORES["text_secondary"]
        )
        dev_message.pack(padx=15, pady=15)

    def switch_page(self, page_name):
        for page in self.pages.values():
            page.pack_forget()
        self.pages[page_name].pack(fill="both", expand=True)

    def minimize(self):
        self.withdraw()
        self.after(10, self.show_taskbar_icon)

    def show_taskbar_icon(self):
        self.overrideredirect(False)
        self.iconify()
        self.after(10, self.remove_taskbar_icon)

    def remove_taskbar_icon(self):
        self.withdraw()
        self.overrideredirect(True)
        self.deiconify()

    def maximize_restore(self):
        if self.state() == "normal":
            self.attributes("-fullscreen", True)
            self.overrideredirect(True)
        else:
            self.attributes("-fullscreen", False)
            self.overrideredirect(True)
            self.state("normal")






    def select_game(self, appid, game_name):
        """Função para selecionar/deselecionar um jogo"""
        if appid in self.selected_games:
            del self.selected_games[appid]
        else:
            self.selected_games[appid] = game_name
        
        # Atualizar o estado do botão de download
        if self.selected_games:
            self.safe_update(self.download_button, state="normal")
        else:
            self.safe_update(self.download_button, state="disabled")
        
        # Atualizar visualmente todos os cards para refletir o estado de seleção
        self.update_card_selection_states()
    
    def update_card_selection_states(self):
        """Atualiza visualmente o estado de seleção de todos os cards"""
        # Atualizar apenas os botões de seleção em cada card
        for widget in self.results_container.winfo_children():
            if isinstance(widget, ctk.CTkFrame):  # Card frame
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkFrame):  # Info frame
                        for info_child in child.winfo_children():
                            if isinstance(info_child, ctk.CTkFrame):  # Buttons frame
                                for button in info_child.winfo_children():
                                    if isinstance(button, ctk.CTkButton):
                                        # Encontrar o appid associado ao card
                                        appid = None
                                        for label in child.winfo_children():
                                            if isinstance(label, ctk.CTkLabel):
                                                text = label.cget("text")
                                                if text.startswith("Steam AppID: "):
                                                    appid = text.split("Steam AppID: ")[1]
                                                    break
                                        
                                        if appid and button.cget("text") in ["Selecionar", "Selecionado"]:
                                            is_selected = appid in self.selected_games
                                            button.configure(
                                                text="Selecionado" if is_selected else "Selecionar",
                                                fg_color=self.game_search_manager.CORES["hover"] if is_selected else self.game_search_manager.CORES["accent"],
                                                hover_color=self.game_search_manager.CORES["accent"] if is_selected else self.game_search_manager.CORES["hover"]
                                            )
    
    def show_game_info(self, appid, game_name):
        """Função para mostrar informações do jogo"""
        try:
            steam_link = f"https://store.steampowered.com/app/{appid}/"
            messagebox.showinfo(
                "Informações do Jogo",
                f"Nome: {game_name}\nAppID: {appid}\nLink Steam: {steam_link}"
            )
        except:
            pass









    def on_closing(self):
        if messagebox.askokcancel("Sair", "Tem certeza que deseja sair?"):
            if self.update_id:
                self.after_cancel(self.update_id)
            if self.dpi_check_id:
                self.after_cancel(self.dpi_check_id)
            if self.asyncio_loop and self.asyncio_loop.is_running():
                self.asyncio_loop.call_soon_threadsafe(self.asyncio_loop.stop)

            self.destroyed = True
            self.destroy()
            
    def update_rate_limit_indicator(self, rate_limit_info):
        """Atualiza o indicador visual de limite de requisições da API do GitHub"""
        def inner():
            if rate_limit_info:
                try:
                    remaining, total = rate_limit_info.split(":")[1].strip().split("/")
                    if int(remaining) < 10:
                        color = "#FF5555"
                    elif int(remaining) < 50:
                        color = "#FFAA55"
                    else:
                        color = "#55FF55"
                    
                    self.rate_limit_label.configure(text=f"API: {remaining}/{total}", text_color=color)
                except Exception:
                    self.rate_limit_label.configure(text=f"API: {rate_limit_info}", text_color="#717E95")
            else:
                self.rate_limit_label.configure(text="API: N/A", text_color="#717E95")
        self.after(0, inner)

    def open_remove_game_dialog(self):
        dialog = ctk.CTkInputDialog(
            text="Digite o AppID do jogo que deseja remover:",
            title="Remove Game",
            fg_color=CORES["background"],
            button_fg_color=CORES["accent"],
            button_hover_color=CORES["hover"],
            entry_fg_color=CORES["secondary"],
            entry_border_color=CORES["secondary"],
            entry_text_color=CORES["text_secondary"],
            text_color=CORES["text_secondary"]
        )
        appid = dialog.get_input()
        if appid:
            if appid.isdigit():
                self.remove_game_by_appid(appid)
            else:
                messagebox.showerror("Error", "Invalid AppID. Please enter a valid number.")

    def remove_game_by_appid(self, appid):
        st_path = self.steam_path / "config" / "stplug-in"
        lua_file = st_path / f"{appid}.lua"
        st_file = st_path / f"{appid}.st"
        files_removed = 0
        if lua_file.exists():
            lua_file.unlink()
            files_removed += 1
        if st_file.exists():
            st_file.unlink()
            files_removed += 1
        if files_removed > 0:
            messagebox.showinfo("Success", f"Removed {files_removed} file(s) for AppID {appid}")
        else:
            messagebox.showwarning("Warning", f"No files found for AppID {appid}")