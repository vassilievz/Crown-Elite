class RateLimitManager:
    def __init__(self, window):
        self.window = window
        self.rate_limit_label = None

    def set_rate_limit_label(self, label):
        self.rate_limit_label = label

    def update_rate_limit_indicator(self, rate_limit_info):
        def inner():
            if rate_limit_info:
                try:
                    remaining, total = rate_limit_info.split(":")[1].strip().split("/")
                    if int(remaining) < 10:
                        color = "#FF5555"
                    elif int(remaining) < 50:
                        color = "#FFAA55"
                    else:
                        color = "#55FF55"
                    
                    self.rate_limit_label.configure(text=f"API: {remaining}/{total}", text_color=color)
                except Exception:
                    self.rate_limit_label.configure(text=f"API: {rate_limit_info}", text_color="#717E95")
            else:
                self.rate_limit_label.configure(text="API: N/A", text_color="#717E95")
        self.window.after(0, inner)