import customtkinter as ctk
from ui.themes import get_theme, toggle_theme

class ThemeManager:
    def __init__(self, window):
        self.window = window
        self.CORES = get_theme()["colors"]

    def toggle_theme(self):
        global CORES
        self.CORES = toggle_theme()["colors"]
        ctk.set_appearance_mode("light" if ctk.get_appearance_mode() == "dark" else "dark")
        self.update_theme()

    def update_theme(self):
        self.window.configure(fg_color=self.CORES["background"])
        
        def update_widget_colors(widget):
            if isinstance(widget, ctk.CTkFrame):
                if "secondary" in str(widget):
                    widget.configure(fg_color=self.CORES["secondary"])
                elif "accent" in str(widget):
                    widget.configure(fg_color=self.CORES["accent"])
                else:
                    widget.configure(fg_color=self.CORES["background"])
            elif isinstance(widget, ctk.CTkButton):
                if "transparent" in str(widget.cget("fg_color")):
                    widget.configure(
                        fg_color="transparent",
                        hover_color=self.CORES["hover"],
                        text_color=self.CORES["text"]
                    )
                else:
                    widget.configure(
                        fg_color=self.CORES["button"],
                        hover_color=self.CORES["button_hover"],
                        text_color=self.CORES["text"]
                    )
            elif isinstance(widget, ctk.CTkLabel):
                if "text_secondary" in str(widget):
                    widget.configure(text_color=self.CORES["text_secondary"])
                else:
                    widget.configure(text_color=self.CORES["text"])
            elif isinstance(widget, ctk.CTkEntry):
                widget.configure(
                    fg_color=self.CORES["input"],
                    text_color=self.CORES["text"],
                    border_color=self.CORES["border"]
                )
            elif isinstance(widget, Text):
                widget.configure(
                    bg=self.CORES["input"],
                    fg=self.CORES["text"]
                )
            
            for child in widget.winfo_children():
                update_widget_colors(child)
        
        update_widget_colors(self.window)