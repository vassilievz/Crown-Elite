import customtkinter as ctk
from tkinter import END, messagebox
from ui.themes import CORES, get_theme, AVAILABLE_THEMES
from ui.updater_page import UpdaterPage

class UIManager:
    def __init__(self, master, icons, steam_path, api_client, pages, content_frame, game_input, download_button, restart_button, results_container, appid_to_game, selected_games, cancel_search, current_row, current_column, update_theme_callback, show_game_info_callback, enable_download_callback):
        self.master = master
        self.icons = icons
        self.steam_path = steam_path
        self.api_client = api_client
        self.pages = pages
        self.content_frame = content_frame
        self.game_input = game_input
        self.download_button = download_button
        self.restart_button = restart_button
        self.results_container = results_container
        self.appid_to_game = appid_to_game
        self.selected_games = selected_games
        self.cancel_search = cancel_search
        self.current_row = current_row
        self.current_column = current_column
        self.update_theme_callback = update_theme_callback
        self.show_game_info_callback = show_game_info_callback
        self.enable_download_callback = enable_download_callback

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
        
        terms_text = """AVISO IMPORTANTE:\n• Este software é exclusivo para DOADORES AUTORIZADOS\n• Compartilhamento ou vazamento resultará em:\n  - Banimento permanente e irrevogável\n  - Bloqueio total do acesso VIP\n  - Possível responsabilização legal\n• Ao utilizar, você concorda com estes termos"""
        
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
            
        paste_button = ctk.CTkButton(input_frame, text="", image=self.icons["paste"], command=self.master.paste_from_clipboard, **button_style)
        paste_button.pack(padx=5, pady=5, side="left")
        search_button = ctk.CTkButton(input_frame, text="", image=self.icons["search"], command=self.master.search_game, **button_style)
        search_button.pack(padx=5, pady=5, side="left")
        self.download_button = ctk.CTkButton(input_frame, text="", image=self.icons["download"], command=self.master.download_manifest, state="disabled", **button_style)
        self.download_button.pack(padx=5, pady=5, side="left")
        self.restart_button = ctk.CTkButton(input_frame, text="", image=self.icons["restart"], command=self.master.restart_steam, state="normal", **button_style)
        self.restart_button.pack(padx=5, pady=5, side="left")
        remove_button = ctk.CTkButton(input_frame, text="", image=self.icons["remove"], command=self.master.open_remove_game_dialog, **button_style)
        remove_button.pack(padx=5, pady=5, side="left")

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

        theme_frame = ctk.CTkFrame(settings_page, fg_color=CORES["secondary"], corner_radius=10)
        theme_frame.pack(fill="x", padx=20, pady=10)

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
                self.update_theme_callback()
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