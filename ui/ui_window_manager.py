import customtkinter as ctk
from tkinter import messagebox

class WindowManager:
    def __init__(self, window):
        self.window = window
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.update_id = None
        self.dpi_check_id = None
        self.destroyed = False

    def start_drag(self, event):
        self.drag_start_x = event.x_root - self.window.winfo_x()
        self.drag_start_y = event.y_root - self.window.winfo_y()

    def on_drag(self, event):
        x = event.x_root - self.drag_start_x
        y = event.y_root - self.drag_start_y
        self.window.geometry(f"+{x}+{y}")

    def minimize(self):
        self.window.withdraw()
        self.window.after(10, self.show_taskbar_icon)

    def show_taskbar_icon(self):
        self.window.overrideredirect(False)
        self.window.iconify()

    def remove_taskbar_icon(self):
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.deiconify()

    def maximize_restore(self):
        if self.window.state() == "normal":
            self.window.attributes("-fullscreen", True)
            self.window.overrideredirect(True)
        else:
            self.window.attributes("-fullscreen", False)
            self.window.overrideredirect(True)
            self.window.state("normal")

    def on_closing(self):
        if messagebox.askokcancel("Sair", "Tem certeza que deseja sair?"):
            if self.update_id:
                self.window.after_cancel(self.update_id)
            if self.dpi_check_id:
                self.window.after_cancel(self.dpi_check_id)
            
            if self.window.asyncio_loop and self.window.asyncio_loop.is_running():
                self.window.asyncio_loop.call_soon_threadsafe(self.window.asyncio_loop.stop)

            self.destroyed = True
            self.window.destroy()