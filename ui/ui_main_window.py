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

from ui.themes import get_theme, toggle_theme, CORES
from ui.app_logic import async_download_and_process
from ui.updater_page import UpdaterPage
from utils.steam_utils import restart_steam

class MainWindow(ctk.CTk):
    def __init__(self, steam_path, api_client, asyncio_loop, game_search_manager, ui_manager):
        super().__init__()
        self.steam_path = steam_path
        self.api_client = api_client
        self.asyncio_loop = asyncio_loop
        self.game_search_manager = game_search_manager
        self.ui_manager = ui_manager

        self.appid_to_game = {}
        self.selected_games = {}
        self.search_thread = None
        self.cancel_search = False
        self.current_row = 0
        self.current_column = 0

        self.update_queue = []
        self.update_id = None
        self.destroyed = False
        self.dpi_check_id = None
        self.after(100, self.process_updates)

        self.title("Crown EliTe")
        self.geometry("1280x720")
        self.minsize(940, 560)
        self.resizable(True, True)
        self.configure(fg_color=CORES["background"])
        self.overrideredirect(True)
        
        self._set_appearance()
        icon_path = self.resource_path("assets/icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception as e:
                print(f"Erro ao definir o ícone da barra de tarefas: {e}")
        else:
            print(f"Ícone não encontrado: {icon_path}")
        self.icons = self.load_icons()

        self.drag_start_x = 0
        self.drag_start_y = 0
        
        self.api_client.set_ui_callback(self.update_rate_limit_indicator)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.setup_ui()

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
            ("Início", self.icons["home"], lambda: self.ui_manager.switch_page("home")),
            ("Buscar", self.icons["search"], lambda: self.ui_manager.switch_page("search")),
            ("Atualizar", self.icons["downloads"], lambda: self.ui_manager.switch_page("updater")),
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
        self.ui_manager.content_frame = self.content_frame # Update content_frame in UIManager

        self.ui_manager.setup_home_page()
        self.ui_manager.setup_search_page()
        self.ui_manager.setup_settings_page()
        
        updater_page = UpdaterPage(self.content_frame, self.icons["downloads"], self.steam_path)
        self.ui_manager.pages["updater"] = updater_page
        
        self.ui_manager.switch_page("search")
        footer_frame = ctk.CTkFrame(main_layout, fg_color=CORES["secondary"], height=22, corner_radius=0)
        footer_frame.pack(fill="x")
        credits_label = ctk.CTkLabel(footer_frame, text="By: Crown System", text_color=CORES["text_secondary"], font=("Segoe UI", 11))
        credits_label.pack(side="left", padx=10)
        
        self.rate_limit_label = ctk.CTkLabel(footer_frame, text="API: N/A", text_color=CORES["text_secondary"], font=("Segoe UI", 11))
        self.rate_limit_label.pack(side="left", padx=10)
        
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
        self.geometry(f" +{x}+{y}")

    def minimize(self):
        self.withdraw()
        self.after(10, self.show_taskbar_icon)

    def show_taskbar_icon(self):
        self.overrideredirect(False)
        self.iconify()
        self.after(10, self.remove_taskbar_icon)

    def remove_taskbar_icon(self):
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

    def enable_download(self, appid, game_name):
        if appid in self.selected_games:
            del self.selected_games[appid]
        else:
            self.selected_games[appid] = game_name
        
        if self.selected_games:
            self.game_search_manager.download_button.configure(state="normal")
        else:
            self.game_search_manager.download_button.configure(state="disabled")
        
        self.game_search_manager.restart_button.configure(state="disabled")

    def download_manifest(self):
        if not self.selected_games:
            messagebox.showwarning("Erro de Seleção", "Selecione pelo menos um jogo primeiro.")
            return
        self.game_search_manager.download_button.configure(state="disabled")
        self.game_search_manager.restart_button.configure(state="disabled")

        threading.Thread(target=self.run_download_multiple, daemon=True).start()

    def run_download(self, appid, game_name):
        asyncio.run(async_download_and_process(self, appid, game_name))
        
    def run_download_multiple(self):
        games_to_download = self.selected_games.copy()
        asyncio.run(self.process_multiple_games(games_to_download))

    def restart_steam(self):
        restart_steam(self.steam_path)
        self.game_search_manager.restart_button.configure(state="disabled")

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