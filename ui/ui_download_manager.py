import asyncio
import threading
from tkinter import messagebox

from ui.app_logic import async_download_and_process

class DownloadManager:
    def __init__(self, app_instance, steam_path):
        self.app_instance = app_instance
        self.steam_path = steam_path

    def enable_download(self, appid, game_name):
        if appid in self.app_instance.selected_games:
            del self.app_instance.selected_games[appid]
        else:
            self.app_instance.selected_games[appid] = game_name

        if self.app_instance.selected_games:
            self.app_instance.download_button.configure(state="normal")
        else:
            self.app_instance.download_button.configure(state="disabled")
        
        self.app_instance.restart_button.configure(state="disabled")

    def download_manifest(self):
        if not self.app_instance.selected_games:
            messagebox.showwarning("Erro de Seleção", "Selecione pelo menos um jogo primeiro.")
            return
        
        self.app_instance.clear_log()
        self.app_instance.add_log("Iniciando processo de download...")
        self.app_instance.download_button.configure(state="disabled")
        self.app_instance.restart_button.configure(state="disabled")

        threading.Thread(target=self.run_download_multiple, daemon=True).start()

    def run_download(self, appid, game_name):
        asyncio.run(async_download_and_process(self.app_instance, appid))
        
    def run_download_multiple(self):
        games_to_download = self.app_instance.selected_games.copy()

        asyncio.run(self.process_multiple_games(games_to_download))

    def restart_steam(self):
        from utils.steam_utils import restart_steam
        self.app_instance.add_log("\nReiniciando o Steam...")
        restart_steam(self.steam_path, self.app_instance.add_log)
        self.app_instance.restart_button.configure(state="disabled")

    async def process_multiple_games(self, games_to_download):
        total_games = len(games_to_download)
        current_game = 0
        
        for appid, game_name in games_to_download.items():
            current_game += 1
            self.app_instance.add_log(f"[{current_game}/{total_games}] Baixando {game_name} (AppID: {appid})...")
            
            try:
                await async_download_and_process(self.app_instance, appid)
                self.app_instance.add_log(f"✓ {game_name} baixado e instalado com sucesso!")
            except Exception as e:
                self.app_instance.add_log(f"✗ Erro ao baixar {game_name}: {str(e)}")
        
        if current_game == total_games:
            self.app_instance.add_log("\nTodos os downloads foram concluídos!")
            self.app_instance.add_log("Reinicie o Steam para aplicar as alterações.")
            self.app_instance.restart_button.configure(state="normal")