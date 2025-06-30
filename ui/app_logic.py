import asyncio
import aiofiles
import vdf
from pathlib import Path
from tkinter import messagebox

from config.constants import REPOSITORIES

async def async_download_and_process(instance, query):
    try:
        success, app_id, game_name, error = await instance.api_client.search_game(query)
        if not success:
            instance.add_log(f"\n[ERROR] {error}")
            instance.download_button.configure(state="normal")
            return

        success, dlc_count = await process_appid(instance, app_id, instance.add_log)
        if success:
            instance.add_log(
                f"\n[SUCCESS] Configuração finalizada para {game_name} com {dlc_count} DLC(s)!"
            )
            instance.restart_button.configure(state="normal")
        else:
            instance.add_log(
                f"\n[ERROR] Falha ao configurar {game_name}."
            )
    except Exception as e:
        instance.add_log(f"\n[ERROR] {str(e)}")
    finally:
        instance.download_button.configure(state="normal")

async def process_appid(instance, app_id, progress_callback, return_data=False):
    for repo in REPOSITORIES:
        try:
            depot_data, depot_map, dlc_count = await handle_depot_files(instance, repo, app_id, progress_callback)
            
            if return_data:
                return True, dlc_count, depot_data, depot_map
            else:
                success = await setup_unlock_tool(depot_data, app_id, 1, depot_map, progress_callback)
                if success:
                    return True, dlc_count
                else:
                    progress_callback(f"[ERROR] Falha ao configurar no repositório {repo}")
        except Exception as e:
            progress_callback(f"[ERROR] Erro no repositório {repo}: {str(e)}")
            continue
    
    if return_data:
        return False, 0, [], {}
    return False, 0

async def handle_depot_files(instance, repo, app_id, progress_callback):
    progress_callback(f"[INFO]\n>>> Conectando ao repositório {repo}")
    try:
        branch_res = await instance.api_client.client.get(
            f"https://api.github.com/repos/{repo}/branches/{app_id}"
        )
        branch_res.raise_for_status()
        instance.api_client.update_rate_limits(branch_res)
        rate_limit_info = instance.api_client.get_rate_limit_info()
        if rate_limit_info:
            progress_callback(f"[INFO] {rate_limit_info}")
        
        commit_sha = branch_res.json()["commit"]["sha"]
        
        progress_callback(f"[SUCCESS] Branch encontrada -> {app_id}")
        tree_res = await instance.api_client.client.get(
            f"https://api.github.com/repos/{repo}/git/trees/{commit_sha}?recursive=1"
        )
        tree_res.raise_for_status()
        instance.api_client.update_rate_limits(tree_res)
        rate_limit_info = instance.api_client.get_rate_limit_info()
        if rate_limit_info:
            progress_callback(f"[INFO] {rate_limit_info}")
        
        progress_callback(f"[SUCCESS] Lista de arquivos obtida")
        depot_cache = instance.steam_path / "depotcache"
        depot_cache.mkdir(exist_ok=True)
        
        collected = []
        depot_map = {}
        dlc_count = 0
        
        for item in tree_res.json()["tree"]:
            path = item["path"]
            if path.endswith(".manifest"):
                file_path = depot_cache / path
                manifest_name = Path(path).stem
                parts = manifest_name.split("_")
                if len(parts) == 2 and all(p.isdigit() for p in parts):
                    depot_id, manifest_id = parts
                    if not file_path.exists():
                        progress_callback(f"[INFO] Baixando manifesto -> {Path(path).name}")
                        content = await instance.api_client.fetch_manifest(repo, commit_sha, path)
                        async with aiofiles.open(file_path, "wb") as f:
                            await f.write(content)
                        progress_callback(f"[SUCCESS] Manifesto salvo -> {file_path}")
                    depot_map.setdefault(depot_id, []).append(manifest_id)
                else:
                    progress_callback(f"[WARNING] Nome de manifesto inválido -> {Path(path).name}")
            elif "key.vdf" in path.lower():
                progress_callback(f"[INFO] Processando chaves -> {Path(path).name}")
                content = await instance.api_client.fetch_manifest(repo, commit_sha, path)
                collected.extend(parse_key_vdf(content))
                dlc_count += len(parse_key_vdf(content))
        
        for depot in depot_map:
            depot_map[depot].sort(key=int, reverse=True)
        
        return collected, depot_map, dlc_count
    except Exception as e:
        raise Exception(f"Erro ao processar arquivos: {str(e)}")

def parse_key_vdf(content):
    try:
        data = vdf.loads(content.decode("utf-8"))
        return [(d_id, d_info["DecryptionKey"]) for d_id, d_info in data["depots"].items()]
    except Exception:
        return []

async def setup_unlock_tool(depot_data, app_id, tool_choice, depot_map, progress_callback):
    if tool_choice == 1:
        return await setup_steamtools(depot_data, app_id, depot_map, progress_callback)
    elif tool_choice == 2:
        progress_callback("[ERROR] Suporte a GreenLuma não implementado.")
        return False
    else:
        progress_callback("[ERROR] Opção de ferramenta inválida.")
        return False

global_versionlock = None

async def setup_steamtools(depot_data, app_id, depot_map, progress_callback, ask_version_lock=True):
    global global_versionlock
    st_path = Path(progress_callback.__self__.steam_path) / "config" / "stplug-in"
    st_path.mkdir(exist_ok=True)

    if ask_version_lock or global_versionlock is None:
        choice = messagebox.askyesno("Bloqueio de Versão", "Deseja bloquear a versão? (Recomendado)")
        global_versionlock = choice
    
    versionlock = global_versionlock

    lua_content = f'addappid({app_id}, 1, "None")\n'
    for d_id, d_key in depot_data:
        if versionlock:
            for manifest_id in depot_map.get(d_id, []):
                lua_content += f'addappid({d_id}, 1, "{d_key}")\n'
                lua_content += f'setManifestid({d_id}, "{manifest_id}")\n'
        else:
            lua_content += f'addappid({d_id}, 1, "{d_key}")\n'

    lua_file = st_path / f"{app_id}.lua"
    async with aiofiles.open(lua_file, "w") as f:
        await f.write(lua_content)

    progress_callback(f"[SUCCESS] Script Lua gerado -> {lua_file}")
    return True