import httpx
import json
import urllib.parse
from typing import Optional, Tuple, List
from config.constants import HEADERS

class APIClient:
    def __init__(self):
        self.client = httpx.AsyncClient(headers=HEADERS)
        self.rate_limit_remaining = None
        self.rate_limit_limit = None
        self.rate_limit_reset = None
        self.update_ui_callback = None

    async def search_game(self, query: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        try:
            if query.isdigit():
                app_id = query
                game_name = await self.fetch_game_name(app_id)
                if game_name:
                    return True, app_id, game_name, None
                return False, None, None, "AppID inválido"

            termo_encoded = urllib.parse.quote_plus(query)
            url_busca = f"https://steamcommunity.com/actions/SearchApps/{termo_encoded}"
            search_response = await self.client.get(url_busca, timeout=10)
            search_response.raise_for_status()
            search_results = search_response.json()
            if not search_results:
                return False, None, None, "Nenhum jogo encontrado"
            first_result = search_results[0]
            app_id = str(first_result["appid"])
            game_name = first_result["name"]
            return True, app_id, game_name, None

        except httpx.HTTPError as e:
            if e.response and e.response.status_code == 403:
                return False, None, None, "Acesso negado pela Steam. Tente novamente mais tarde."
            return False, None, None, f"Erro de conexão: {str(e)}"
        except Exception as e:
            return False, None, None, f"Erro inesperado: {str(e)}"

    async def fetch_game_name(self, app_id: str) -> Optional[str]:
        try:
            url_detalhes = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
            response = await self.client.get(url_detalhes, timeout=10)
            response.raise_for_status()
            data = response.json()
            if not data or str(app_id) not in data:
                return None
            app_data = data[str(app_id)]
            if not app_data.get("success"):
                return None
            return app_data["data"]["name"]

        except httpx.HTTPError as e:
            if e.response and e.response.status_code == 403:
                raise Exception("Acesso negado pela Steam ao buscar detalhes. Tente novamente mais tarde.")
            raise Exception(f"Erro de conexão ao buscar detalhes do jogo: {str(e)}")
        except Exception as e:
            raise Exception(f"Erro ao buscar informações do jogo: {str(e)}")

    async def fetch_manifest(self, repo: str, sha: str, path: str) -> bytes:
        for _ in range(3):
            try:
                url_raw = f"https://raw.githubusercontent.com/{repo}/{sha}/{path}"
                response = await self.client.get(url_raw, timeout=30)
                response.raise_for_status()
                return response.content
            except Exception:
                continue
        raise RuntimeError(f"Falha ao baixar: {path}")

    def update_rate_limits(self, response: httpx.Response):
        if "x-ratelimit-remaining" in response.headers:
            self.rate_limit_remaining = response.headers.get("x-ratelimit-remaining")
            self.rate_limit_limit = response.headers.get("x-ratelimit-limit")
            self.rate_limit_reset = response.headers.get("x-ratelimit-reset")
            if self.update_ui_callback:
                self.update_ui_callback(self.get_rate_limit_info())

    def get_rate_limit_info(self) -> Optional[str]:
        if self.rate_limit_remaining is not None:
            return f"Requisições restantes: {self.rate_limit_remaining}/{self.rate_limit_limit}"
        return None

    def set_ui_callback(self, callback):
        self.update_ui_callback = callback
