import asyncio
import aiohttp
import json
import requests
import io
from PIL import Image
from tkinter import END, messagebox
import customtkinter as ctk

class GameSearchManager:
    def __init__(self, app, icons, CORES):
        self.app = app
        self.icons = icons
        self.CORES = CORES
        self.appid_to_game = {}
        self.current_row = 0
        self.current_column = 0
        self.cancel_search = False

    def paste_from_clipboard(self):
        try:
            clipboard_text = self.app.clipboard_get()
            self.app.game_input.delete(0, END)
            self.app.game_input.insert(0, clipboard_text)
        except Exception as e:
            messagebox.showerror("Erro ao Colar", f"Falha ao colar da área de transferência: {e}")

    def search_game(self):
        """Inicia a busca de jogos"""
        user_input = self.app.game_input.get().strip()
        if not user_input:
            messagebox.showwarning("Aviso", "Digite o nome do jogo para pesquisar.")
            return

        for widget in self.app.results_container.winfo_children():
            widget.destroy()

        self.appid_to_game.clear()
        self.current_row = 0
        self.current_column = 0
        
        self.app.safe_update(self.app.download_button, state="disabled")
        self.app.safe_update(self.app.restart_button, state="disabled")

        self.cancel_search = False

        asyncio.run_coroutine_threadsafe(
            self.async_search_game_api(user_input), self.app.asyncio_loop
        )

    async def async_search_game_api(self, query):
        try:
            success, app_id, name, error = await self.app.api_client.search_game(query)
            if success:
                image_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg"
                valid_image_url = ""

                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.head(image_url) as response:
                            if response.status == 200:
                                valid_image_url = image_url
                except aiohttp.ClientError:
                    pass

                await self.create_game_card(app_id, name, valid_image_url)
        except Exception:
            pass

    async def async_search_game(self, user_input):
        games = await self.find_appid_by_name(user_input)
        if not games:
            return
        self.appid_to_game.clear()
        semaphore = asyncio.Semaphore(10)
        async with aiohttp.ClientSession() as session:
            tasks = []
            for game in games:
                if self.cancel_search:
                    return
                appid = str(game.get("appid", "Desconhecido"))
                tasks.append(self.process_game(session, semaphore, appid, game))
            await asyncio.gather(*tasks)

    async def process_game(self, session, semaphore, appid, game):
        async with semaphore:
            result = await self.fetch_game_details(session, appid)
            if self.cancel_search:
                return
            if not result:
                return
            game_name = result.get("name", game.get("name", "Desconhecido"))
            image_url = result.get("header_image", "")
            game_type = result.get("type", "").lower()
            if game_type == "game" and not any(keyword in game_name.lower() for keyword in ["dlc", "soundtrack", "artbook", "expansion", "upgrade"]):
                self.appid_to_game[appid] = {"name": game_name, "image": image_url}
                await self.create_game_card(appid, game_name, image_url)

    async def find_appid_by_name(self, game_name):
        try:
            url = f"https://steamui.com/loadGames.php?search={game_name}&page=1&limit=20"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    if r.status == 200:
                        content = await r.text()
                        try:
                            data = json.loads(content)
                            return data.get("games", [])
                        except json.JSONDecodeError:
                            return []
                    else:
                        return []
        except aiohttp.ClientError:
            return []

    async def fetch_game_details(self, session, appid):
        try:
            url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get(appid, {}).get("success", False):
                        game_data = data[appid]["data"]
                        return {"name": game_data.get("name", "Desconhecido"), "header_image": game_data.get("header_image", ""), "type": game_data.get("type", "")}
                return None
        except Exception:
            return None

    async def create_game_card(self, appid, game_name, image_url):
        self.appid_to_game[appid] = {
            'name': game_name,
            'image': image_url
        }
        
        card_width = 320
        card_height = 450
        image_height = int(card_width * 0.47)

        def on_enter(e):
            card_frame.configure(border_color=self.CORES["accent"])

        def on_leave(e):
            card_frame.configure(border_color=self.CORES["border"])

        card_frame = ctk.CTkFrame(
            self.app.results_container,
            fg_color=self.CORES["secondary"],
            corner_radius=12,
            width=card_width,
            height=card_height,
            border_width=2,
            border_color=self.CORES["border"]
        )

        card_frame.grid(row=self.current_row, column=self.current_column, padx=10, pady=10, sticky="nsew")
        self.app.results_container.grid_columnconfigure(self.current_column, weight=1)

        card_frame.grid_rowconfigure(0, weight=0)
        card_frame.grid_rowconfigure(1, weight=1)
        card_frame.grid_columnconfigure(0, weight=1)

        image_frame = ctk.CTkFrame(card_frame, fg_color="transparent", corner_radius=12)
        image_frame.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        if image_url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.head(image_url) as response:
                        if response.status == 200:
                            image_data = requests.get(image_url).content
                            image = Image.open(io.BytesIO(image_data))
                            image = image.resize((card_width - 16, image_height), Image.LANCZOS)
                            ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=(card_width - 16, image_height))
                            image_label = ctk.CTkLabel(image_frame, image=ctk_image, text="")
                        else:
                            raise Exception("Imagem não encontrada")
            except Exception:
                image_label = ctk.CTkLabel(
                    image_frame,
                    text="Imagem não disponível",
                    font=("Segoe UI", 13),
                    text_color=self.CORES["text_secondary"],
                    height=image_height
                )
        else:
            image_label = ctk.CTkLabel(
                image_frame,
                text="Imagem não disponível",
                font=("Segoe UI", 13),
                text_color=self.CORES["text_secondary"],
                height=image_height
            )

        image_label.grid(row=0, column=0, sticky="nsew")

        info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        info_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        info_frame.grid_columnconfigure(0, weight=1)

        name_label = ctk.CTkLabel(
            info_frame,
            text=game_name,
            font=("Segoe UI", 15, "bold"),
            wraplength=card_width - 24,
            justify="left"
        )
        name_label.grid(row=0, column=0, pady=(8, 4), sticky="w")

        id_label = ctk.CTkLabel(
            info_frame,
            text=f"Steam AppID: {appid}",
            font=("Segoe UI", 11),
            text_color=self.CORES["text_secondary"]
        )
        id_label.grid(row=1, column=0, pady=(0, 12), sticky="w")

        buttons_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, sticky="ew")
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)

        is_selected = appid in self.app.selected_games
        select_button = ctk.CTkButton(
            buttons_frame,
            text="Selecionado" if is_selected else "Selecionar",
            font=("Segoe UI", 13, "bold"),
            fg_color=self.CORES["hover"] if is_selected else self.CORES["accent"],
            hover_color=self.CORES["accent"] if is_selected else self.CORES["hover"],
            corner_radius=8,
            height=32,
            command=lambda a=appid, n=game_name: self.app.select_game(a, n)
        )
        select_button.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        info_button = ctk.CTkButton(
            buttons_frame,
            text="Info",
            font=("Segoe UI", 13, "bold"),
            fg_color=self.CORES["accent"],
            hover_color=self.CORES["hover"],
            corner_radius=8,
            height=32,
            command=lambda a=appid, n=game_name: self.app.show_game_info(a, n)
        )
        info_button.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        for widget in [card_frame, image_label, name_label, id_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

        self.current_column += 1
        if self.current_column > 2:
            self.current_column = 0
            self.current_row += 1

    def show_game_info(self, appid, game_name):
        try:
            steam_link = f"https://store.steampowered.com/app/{appid}/"
            messagebox.showinfo(
                "Informações do Jogo",
                f"Nome: {game_name}\nAppID: {appid}\nLink Steam: {steam_link}"
            )
        except:
            pass