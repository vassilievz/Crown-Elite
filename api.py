import tkinter as tk

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Crown EliTe")
        self.geometry("400x600")
        self.setup_ui()

    def setup_ui(self):
        label = tk.Label(self, text="Crown EliTe")
        label.pack(pady=20)

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()