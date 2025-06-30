import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path

class GameRemover:
    def __init__(self, window, steam_path, CORES):
        self.window = window
        self.steam_path = steam_path
        self.CORES = CORES

    def open_remove_game_dialog(self):
        dialog = ctk.CTkInputDialog(
            text="Digite o AppID do jogo que deseja remover:",
            title="Remove Game",
            fg_color=self.CORES["background"],
            button_fg_color=self.CORES["accent"],
            button_hover_color=self.CORES["hover"],
            entry_fg_color=self.CORES["secondary"],
            entry_border_color=self.CORES["secondary"],
            entry_text_color=self.CORES["text_secondary"],
            text_color=self.CORES["text_secondary"]
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