DARK_THEME = {
    "name": "Escuro",
    "colors": {
        "background": "#1E1E1E",
        "secondary": "#252526",
        "accent": "#3C3C3C",
        "text": "#FFFFFF",
        "text_secondary": "#B0B0B0",
        "border": "#454545",
        "hover": "#505050",
        "button": "#3C3C3C",
        "button_hover": "#505050",
        "input": "#2D2D2D",
        "success": "#28A745",
        "error": "#DC3545",
        "warning": "#FFC107"
    }
}

LIGHT_THEME = {
    "name": "Claro",
    "colors": {
        "background": "#FFFFFF",
        "secondary": "#F5F5F5",
        "accent": "#E0E0E0",
        "text": "#000000",
        "text_secondary": "#666666",
        "border": "#CCCCCC",
        "hover": "#E8E8E8",
        "button": "#E0E0E0",
        "button_hover": "#D0D0D0",
        "input": "#FFFFFF",
        "success": "#28A745",
        "error": "#DC3545",
        "warning": "#FFC107"
    }
}

AVAILABLE_THEMES = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME
}

current_theme = "dark"

def get_theme(theme_name=None):
    global current_theme
    if theme_name:
        current_theme = theme_name
    return AVAILABLE_THEMES.get(current_theme, DARK_THEME)

def toggle_theme():
    global current_theme
    current_theme = "light" if current_theme == "dark" else "dark"
    return get_theme()