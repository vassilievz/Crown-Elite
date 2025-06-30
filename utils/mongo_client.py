from pymongo import MongoClient
from tkinter import messagebox

try:
    client = MongoClient('coloque sua url aqui')
    
    db = client.crown_elite
    usuarios = db.usuarios
    
    client.server_info()
    
except Exception as e:
    messagebox.showerror("Erro de Conexão", f"Erro ao conectar com o MongoDB: {str(e)}")
    raise e
