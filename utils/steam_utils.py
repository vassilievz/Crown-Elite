import os
from pathlib import Path
import winreg

def detect_steam_path():
    try:
        steam_path = None
        try:
            hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Valve\\Steam")
            steam_path = winreg.QueryValueEx(hkey, "SteamPath")[0]
            winreg.CloseKey(hkey)
            if steam_path and os.path.exists(steam_path):
                return Path(steam_path)
        except Exception:
            pass
            
        common_paths = [
            Path(os.getenv("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Steam",
            Path(os.getenv("PROGRAMFILES", "C:/Program Files")) / "Steam",
            Path("C:/Steam"),
            Path.home() / "Steam",
            Path(os.getenv("LOCALAPPDATA", "")) / "Steam",
            Path("D:/Steam"),
            Path("E:/Steam")
        ]
        
        for path in common_paths:
            if path.exists() and (path / "steam.exe").exists():
                return path
        
        return None
    except Exception:
        return None

def restart_steam(steam_path, append_progress):
    try:
        os.system("taskkill /f /im steam.exe")
        append_progress("DEBUG: Steam fechado com sucesso")
        os.startfile(steam_path / "steam.exe")
        append_progress("DEBUG: Steam reiniciado")
        append_progress("[SUCCESS] Steam reiniciado com sucesso!")
    except Exception as e:
        append_progress(f"[ERROR] Erro ao reiniciar Steam: {str(e)}")