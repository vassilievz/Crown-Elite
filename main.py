import os
import sys
import asyncio
import threading
from pathlib import Path
from tkinter import messagebox
from utils.steam_utils import detect_steam_path
from utils.api_client import APIClient
from ui.app_ui import ManifestDownloader


def run_asyncio_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

def integrate_asyncio_tkinter(app_instance):
    loop = asyncio.new_event_loop()
    threading.Thread(target=run_asyncio_loop, args=(loop,), daemon=True).start()

    def tick():
        loop.call_soon_threadsafe(lambda: None)
        app_instance.after(10, tick)

    app_instance.after(10, tick)
    return loop

def main():
    try:

        steam_path = detect_steam_path()
        if not steam_path:
            messagebox.showerror("Erro", "Steam não encontrado!")
            return

        api_client = APIClient()
        app = ManifestDownloader(steam_path, api_client)
        app.asyncio_loop = integrate_asyncio_tkinter(app)

        app.protocol("WM_DELETE_WINDOW", app.on_closing)

        app.mainloop()


    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao iniciar o aplicativo: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
