import os
import re
import zipfile
import requests
import string
import zlib
import shutil
import threading
import customtkinter as ctk
from bs4 import BeautifulSoup
from ui.themes import get_theme

class StToLuaConverter:
    def __init__(self, folder="."):
        self.folder = folder

    def clean_lua_content(self, content):
        """Remove non-printable characters and trim leading blank lines or spaces."""
        cleaned_content = ''.join([char if char in string.printable or char in '\n\r' else '' for char in content])
        cleaned_content = cleaned_content.lstrip('\n\r')
        return cleaned_content

    def decrypt_st(self, st_file_name, lua_file_name):
        try:
            with open(st_file_name, "rb") as file:
                content = file.read()

            if len(content) < 12:
                return "File too small."

            xorkey = content[0] | (content[1] << 8) | (content[2] << 16) | (content[3] << 24)
            size = content[4] | (content[5] << 8) | (content[6] << 16) | (content[7] << 24)

            xorkey = (xorkey ^ 0xFFFEA4C8) & 0xFF
            data = bytearray(content[12:])
            for i in range(size):
                data[i] ^= (xorkey & 0xFF)

            decompressed_data = self.inflate_data(data)
            if decompressed_data:
                lua_content = decompressed_data[512:]
                cleaned_content = self.clean_lua_content(lua_content.decode("utf-8"))
                with open(lua_file_name, "w", encoding="utf-8") as lua_file:
                    lua_file.write(cleaned_content)
                return None
            else:
                return "Error decompressing data."
        except Exception as e:
            return f"Error: {str(e)}"

    def reorder_lua_content(self, lua_content):
        content = lua_content.decode("utf-8")
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        ordered_output = []
        addappid_seen = set()

        for line in lines:
            if "addappid" in line:
                parts = line.split("(")
                appid = parts[1].split(")")[0]
                if appid not in addappid_seen:
                    ordered_output.append(line)
                    addappid_seen.add(appid)
            elif "setManifestid" in line:
                ordered_output.append(line)

        final_output = "\n".join(ordered_output)
        return final_output

    def inflate_data(self, data):
        try:
            decompressed_capacity = len(data) * 2
            decompressed = bytearray(decompressed_capacity)
            strm = zlib.decompressobj()
            decompressed_data = strm.decompress(bytes(data))
            decompressed.extend(decompressed_data)

            while strm.unused_data:
                decompressed_data = strm.decompress(strm.unused_data)
                decompressed.extend(decompressed_data)

            return decompressed

        except zlib.error as e:
            return None

    def convert_st_to_lua(self):
        st_files = [file for file in os.listdir(self.folder) if file.endswith(".st")]

        if not st_files:
            return "No .st files found."

        results = []
        for st_file in st_files:
            st_file_path = os.path.join(self.folder, st_file)
            lua_file_path = os.path.join(self.folder, os.path.splitext(st_file)[0] + ".lua")
            error_message = self.decrypt_st(st_file_path, lua_file_path)
            if error_message:
                results.append(f"Error converting {st_file}: {error_message}")
            else:
                results.append(f"Successfully converted {st_file} to {lua_file_path}")
        
        return "\n".join(results)

class ManifestFixer:
    def __init__(self, folder=".", app_id=None):
        self.folder = folder
        self.app_id = app_id
        self.manifests = {}
        self.lua_files = []
        self.changes_made = False

    def create_temp_folder(self):
        """Create temporary folders based on detected .lua files and remove 'temp_None' if it exists."""
        lua_files = [file for file in os.listdir(self.folder) if file.endswith(".lua")]

        if not lua_files:
            return "No .lua files found. Skipping temp folder creation."

        results = []
        for lua_file in lua_files:
            app_id = lua_file.split('.')[0]

            if app_id.lower() == "none" or not app_id.isdigit():
                continue

            temp_folder = os.path.join(self.folder, f"temp_{app_id}")
            os.makedirs(temp_folder, exist_ok=True)
            results.append(f"Created temporary folder: {temp_folder}")

        temp_none_path = os.path.join(self.folder, "temp_None")
        if os.path.exists(temp_none_path) and os.path.isdir(temp_none_path):
            shutil.rmtree(temp_none_path)
            results.append("Deleted temporary folder: temp_None")

        return "\n".join(results)

    def move_lua_files(self, temp_folder):
        """Move each .lua file corresponding to its app_id into a separate temporary folder."""
        lua_files = [file for file in os.listdir(self.folder) if file.endswith(".lua")]

        if not lua_files:
            return "No .lua files found to move."

        results = []
        for lua_file in lua_files:
            app_id = lua_file.split('.')[0]

            if app_id == 'None':
                results.append(f"Invalid app_id extracted from filename: {lua_file}")
                continue

            temp_folder = f"temp_{app_id}"
            os.makedirs(temp_folder, exist_ok=True)
            
            lua_file_path = os.path.join(self.folder, lua_file)
            temp_file_path = os.path.join(temp_folder, lua_file)

            try:
                shutil.move(lua_file_path, temp_file_path)
                results.append(f"Moved {lua_file} to {temp_folder}")
            except Exception as e:
                results.append(f"Error moving {lua_file}: {str(e)}")
        
        return "\n".join(results)

    def download_manifests(self):
        """Download manifests for each app_id detected in the temp folders."""
        temp_folders = [
            folder for folder in os.listdir(self.folder)
            if folder.startswith("temp_") and folder != "temp_None"
        ]

        if not temp_folders:
            return "No valid temp folders found."

        results = []
        for temp_folder in temp_folders:
            app_id = temp_folder.split("_")[1]
            results.append(f"Fetching manifests for App ID: {app_id}")
            result = self._download_manifests_for_app_id(app_id, temp_folder)
            results.append(result)

        return "\n".join(results)

    def _download_manifests_for_app_id(self, app_id, temp_folder):
        """Download manifests for a specific App ID and save them in the temp folder."""
        github_token = "adicione seu TOKEN do github aqui"

        url = f"https://github.com/ZackTheGrumpy/nomoreupdate/tree/{app_id}"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Authorization": f"token {github_token}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return f"Failed to fetch manifest list for App ID {app_id} ({response.status_code})."

        soup = BeautifulSoup(response.text, 'html.parser')
        manifest_links = [
            "https://raw.githubusercontent.com" + a['href'].replace("/blob", "")
            for a in soup.find_all('a', href=True) if a['href'].endswith('.manifest')
        ]

        if not manifest_links:
            return f"No manifests found for App ID {app_id}."

        results = []
        for link in manifest_links:
            manifest_name = os.path.basename(link)
            manifest_path = os.path.join(temp_folder, manifest_name)

            if not os.path.exists(manifest_path):
                manifest_data = requests.get(link, headers=headers).content
                with open(manifest_path, 'wb') as f:
                    f.write(manifest_data)
                results.append(f"Downloaded {manifest_name}")
        
        return "\n".join(results)

    def find_manifests(self, temp_folder):
        """Find all manifest files in the temp folder and extract depot IDs and manifest IDs."""
        results = ["Searching for manifest files in the temp folder..."]
        for file in os.listdir(temp_folder):
            if file.endswith(".manifest"):
                parts = file.split("_")
                if len(parts) == 2:
                    try:
                        depot_id = int(parts[0])
                        manifest_id = parts[1].split(".")[0]
                        self.manifests[depot_id] = manifest_id
                        results.append(f"Found manifest: Depot {depot_id} -> Manifest {manifest_id}")
                    except ValueError:
                        results.append(f"Skipping invalid manifest file: {file}")
        
        return "\n".join(results)

    def find_lua_files(self):
        self.lua_files = [file for file in os.listdir(self.folder) if file.endswith(".lua")]
        return f"Found {len(self.lua_files)} Lua files"

    def correct_manifest_ids(self, temp_folder):
        """Check and fix manifest IDs inside existing Lua files in the temp folder."""
        results = [f"Checking with manifest data: {self.manifests}"]
        updated_appids = []

        for lua_file in os.listdir(temp_folder):
            if lua_file.endswith(".lua"):
                lua_path = os.path.join(temp_folder, lua_file)
                app_id = lua_file.split('.')[0]
                results.append(f"Checking {lua_file}...")

                with open(lua_path, "r", encoding="utf-8") as f:
                    content = f.readlines()

                updated_content = []
                modified = False

                for line in content:
                    match = re.search(r'setManifestid\((\d+),\s*"(\d+)"', line)

                    if match:
                        depot_id = int(match.group(1))
                        current_manifest_id = match.group(2)
                        results.append(f"Found manifest reference: Depot {depot_id} -> {current_manifest_id}")

                        if depot_id in self.manifests:
                            correct_manifest_id = self.manifests[depot_id]

                            if current_manifest_id != correct_manifest_id:
                                results.append(f"Wrong manifest ID in {lua_file} for depot {depot_id}")
                                results.append(f"Fixing {current_manifest_id} -> {correct_manifest_id}")
                                line = re.sub(r'setManifestid\(\d+,\s*"\d+"',
                                              f'setManifestid({depot_id}, "{correct_manifest_id}"', line)
                                modified = True
                            else:
                                results.append("Correct manifest ID already present.")

                    updated_content.append(line)

                if modified:
                    with open(lua_path, "w", encoding="utf-8") as f:
                        f.writelines(updated_content)
                    results.append(f"Updated {lua_file} with correct manifest IDs.")
                    updated_appids.append(app_id)
                    self.changes_made = True
                else:
                    results.append(f"No changes needed for {lua_file}.")

        if self.changes_made:
            results.append(f"The following app_ids were updated: {', '.join(updated_appids)}")
        else:
            results.append("Everything is up to date! No updates needed.")
        
        return "\n".join(results)

    def exports(self):
        """Move .manifest files to the depotcache and .lua files back to the original folder for all temp folders."""
        depotcache_path = r"C:\Program Files (x86)\Steam\depotcache"
        os.makedirs(depotcache_path, exist_ok=True)
        
        results = [f"Ensured depotcache folder exists at {depotcache_path}"]
        
        temp_folders = [folder for folder in os.listdir(self.folder) if folder.startswith("temp_")]

        if not temp_folders:
            return "No temp folders found."

        for temp_folder in temp_folders:
            results.append(f"Processing temp folder: {temp_folder}")

            for file in os.listdir(temp_folder):
                if file.endswith(".manifest"):
                    manifest_path = os.path.join(temp_folder, file)
                    destination_path = os.path.join(depotcache_path, file)

                    try:
                        shutil.move(manifest_path, destination_path)
                        results.append(f"Moved {file} to {depotcache_path}")
                    except Exception as e:
                        results.append(f"Error moving {file}: {str(e)}")

                elif file.endswith(".lua"):
                    lua_path = os.path.join(temp_folder, file)
                    destination_path = os.path.join(self.folder, file)

                    try:
                        shutil.move(lua_path, destination_path)
                        results.append(f"Moved {file} back to the original folder")
                    except Exception as e:
                        results.append(f"Error moving {file}: {str(e)}")
        
        return "\n".join(results)

    def cleanup(self):
        """Remove .st files and all temp folders."""
        results = ["Cleaning up files"]

        for file in os.listdir(self.folder):
            if file.endswith(".st"):
                file_path = os.path.join(self.folder, file)
                os.remove(file_path)
                results.append(f"Deleted: {file}")

        temp_folders = [folder for folder in os.listdir(self.folder) if folder.startswith("temp_")]

        for temp_folder in temp_folders:
            temp_folder_path = os.path.join(self.folder, temp_folder)
            if os.path.exists(temp_folder_path):
                shutil.rmtree(temp_folder_path)
                results.append(f"Deleted temporary folder: {temp_folder}")
        
        return "\n".join(results)

    def run(self):
        results = ["Starting Manifest Fixer..."]

        converter = StToLuaConverter(self.folder)
        convert_result = converter.convert_st_to_lua()
        results.append(convert_result)

        temp_result = self.create_temp_folder()
        results.append(temp_result)

        move_result = self.move_lua_files(None)
        results.append(move_result)

        download_result = self.download_manifests()
        results.append(download_result)

        temp_folders = [folder for folder in os.listdir(self.folder) if folder.startswith("temp_")]
        for temp_folder in temp_folders:
            find_result = self.find_manifests(temp_folder)
            results.append(find_result)
            
            correct_result = self.correct_manifest_ids(temp_folder)
            results.append(correct_result)

        export_result = self.exports()
        results.append(export_result)

        cleanup_result = self.cleanup()
        results.append(cleanup_result)

        results.append("Process complete!")
        return "\n".join(results)

class UpdaterPage(ctk.CTkFrame):
    def __init__(self, parent, icon=None, steam_path=None):
        super().__init__(parent)
        self.parent = parent
        self.icon = icon
        self.steam_path = steam_path
        self.current_theme = get_theme()["colors"]
        
        self.setup_ui()
        
    def setup_ui(self):
        CORES = self.current_theme
        
        self.configure(fg_color=CORES["background"])
        
        main_container = ctk.CTkFrame(self, fg_color=CORES["background"])
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            main_container,
            text="Atualizador de Arquivos Lua",
            text_color=CORES["text"],
            font=("Segoe UI", 24, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        desc_label = ctk.CTkLabel(
            main_container,
            text="Digite o caminho do diretório contendo os arquivos .lua para atualizar",
            text_color=CORES["text_secondary"],
            font=("Segoe UI", 14)
        )
        desc_label.pack(pady=(0, 20))
        
        input_frame = ctk.CTkFrame(
            main_container,
            fg_color=CORES["secondary"],
            corner_radius=10,
            border_width=1,
            border_color=CORES["border"]
        )
        input_frame.pack(fill="x", pady=(0, 20))
        
        input_label = ctk.CTkLabel(
            input_frame,
            text="Diretório dos arquivos .lua:",
            text_color=CORES["text_secondary"],
            font=("Segoe UI", 13)
        )
        input_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        self.directory_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Ex: C:\\MeusDados\\Scripts",
            height=40,
            font=("Segoe UI", 14),
            fg_color=CORES["background"],
            text_color=CORES["text"],
            placeholder_text_color=CORES["text_secondary"],
            border_color=CORES["border"]
        )
        self.directory_entry.pack(fill="x", padx=15, pady=(0, 10))
        
        buttons_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.update_button = ctk.CTkButton(
            buttons_frame,
            text="Atualizar Arquivos .lua",
            command=self.start_update,
            height=40,
            font=("Segoe UI", 14, "bold"),
            fg_color=CORES["accent"],
            hover_color=CORES["hover"],
            text_color="white"
        )
        self.update_button.pack(side="left", padx=(0, 10))
        
        browse_button = ctk.CTkButton(
            buttons_frame,
            text="Procurar",
            command=self.browse_directory,
            height=40,
            font=("Segoe UI", 14),
            fg_color=CORES["button"],
            hover_color=CORES["button_hover"],
            text_color=CORES["text"]
        )
        browse_button.pack(side="left")
        
        self.progress_frame = ctk.CTkFrame(
            main_container,
            fg_color=CORES["secondary"],
            corner_radius=10,
            border_width=1,
            border_color=CORES["border"]
        )
        self.progress_frame.pack(fill="both", expand=True)
        
        progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Log de Atualização",
            text_color=CORES["text_secondary"],
            font=("Segoe UI", 13, "bold")
        )
        progress_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        self.log_text = ctk.CTkTextbox(
            self.progress_frame,
            font=("Consolas", 12),
            fg_color=CORES["background"],
            text_color=CORES["text"],
            border_color=CORES["border"],
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        clear_button = ctk.CTkButton(
            self.progress_frame,
            text="Limpar Log",
            command=self.clear_log,
            height=30,
            font=("Segoe UI", 12),
            fg_color=CORES["button"],
            hover_color=CORES["button_hover"],
            text_color=CORES["text"]
        )
        clear_button.pack(anchor="e", padx=15, pady=(0, 15))
        
    def browse_directory(self):
        """Open file dialog to browse for directory"""
        import tkinter.filedialog as fd
        directory = fd.askdirectory(title="Selecione o diretório dos arquivos .lua")
        if directory:
            self.directory_entry.delete(0, "end")
            self.directory_entry.insert(0, directory)
    
    def log_message(self, message):
        """Add message to log"""
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.update()
    
    def clear_log(self):
        """Clear the log text area"""
        self.log_text.delete("1.0", "end")
    
    def start_update(self):
        """Start the update process in a separate thread"""
        directory = self.directory_entry.get().strip()
        
        if not directory:
            self.log_message("Erro: Por favor, digite um diretório válido.")
            return
        
        if not os.path.exists(directory):
            self.log_message(f"Erro: O diretório '{directory}' não existe.")
            return
        
        self.update_button.configure(state="disabled", text="Atualizando...")
        
        thread = threading.Thread(target=self.run_update, args=(directory,))
        thread.daemon = True
        thread.start()
    
    def run_update(self, directory):
        """Run the update process"""
        try:
            self.log_message(f"Iniciando atualização no diretório: {directory}")
            self.log_message("=" * 50)
            
            fixer = ManifestFixer(folder=directory)
            
            result = fixer.run()
            
            for line in result.split("\n"):
                if line.strip():
                    self.log_message(line)
            
            self.log_message("=" * 50)
            self.log_message("Atualização concluída com sucesso!")
            
        except Exception as e:
            self.log_message(f"Erro durante a atualização: {str(e)}")
        
        finally:
            self.after(0, lambda: self.update_button.configure(state="normal", text="Atualizar Arquivos .lua"))
    
    def update_theme(self):
        """Update the theme of all widgets"""
        self.current_theme = get_theme()["colors"]
        pass

def main():
    root = ctk.CTk()
    root.title("Updater Page Test")
    root.geometry("800x600")
    
    updater = UpdaterPage(root)
    updater.pack(fill="both", expand=True)
    
    root.mainloop()

if __name__ == "__main__":
    main()
