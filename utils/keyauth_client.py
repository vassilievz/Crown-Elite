import sys
import hashlib
import os
from datetime import datetime
from utils.keyauth import api
from tkinter import messagebox
import json
from pathlib import Path

def get_credentials_path():
    app_data = os.getenv('APPDATA')
    credentials_dir = Path(app_data) / 'CrownElite'
    credentials_dir.mkdir(exist_ok=True)
    return credentials_dir / 'credentials.json'

def save_credentials(key):
    try:
        credentials_path = get_credentials_path()
        with open(credentials_path, 'w') as f:
            json.dump({'key': key}, f)
    except Exception:
        pass

def load_credentials():
    try:
        credentials_path = get_credentials_path()
        if credentials_path.exists():
            with open(credentials_path) as f:
                data = json.load(f)
                return data.get('key')
    except Exception:
        pass
    return None

def get_checksum():
    try:
        if getattr(sys, 'frozen', False):
            application_path = sys.executable
        else:
            application_path = sys.argv[0]
            
        with open(application_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao gerar checksum: {str(e)}")
        sys.exit(1)

try:
    keyauthapp = api(
        name="Crown ElitE",
        ownerid="sd6hzurkWX",
        version="1.0",
        hash_to_check=get_checksum()
    )
    
    original_license = keyauthapp.license
    def license_with_expiry_check(key):
        if not original_license(key):
            return False
            
        try:
            expiry_date = datetime.fromtimestamp(int(keyauthapp.user_data.expires))
            if expiry_date < datetime.now():
                messagebox.showerror("Erro", "Sua licença expirou.")
                return False
            
            save_credentials(key)
            return True
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao verificar expiração: {str(e)}")
            return False
    
    keyauthapp.license = license_with_expiry_check
    
except Exception as e:
    messagebox.showerror("Erro Fatal", f"Erro ao inicializar KeyAuth: {str(e)}")
    sys.exit(1)
