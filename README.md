# Crown Elite

<div align="center">

<img src="assets/icon.png" width="128" height="128" alt="Crown Elite Logo">

[![Discord](https://img.shields.io/discord/YOUR_SERVER_ID?color=7289DA&label=Discord&logo=discord&logoColor=white)](https://discord.gg/crwn)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

*A Steam game manifest automation tool*

*Created by Vassiliev for educational purposes*

</div>

## 🎮 About

Crown Elite is a Windows desktop application that automates Steam game manifest management using SteamTools. This project was created by Vassiliev as a learning experience to understand Steam's manifest system and improve Python programming skills. It provides a modern, user-friendly interface for managing game installations through manifest files and integrates directly with SteamTools for seamless operation.

### ⚠️ Important Disclaimer

This project is created **STRICTLY FOR EDUCATIONAL PURPOSES**. We strongly encourage:
- Supporting game developers by purchasing their games
- Using official distribution channels
- Respecting intellectual property rights

The developers of Crown Elite do not endorse or promote any form of software piracy. This tool should be used responsibly and in accordance with all applicable laws and terms of service.

## ✨ Features

- 🎯 Modern GUI built with CustomTkinter
- 🔍 Automatic game search and manifest handling
- 📊 Detailed game information with DRM status
- 🎮 Integrated SteamTools plugin management
- 🚀 Automatic Steam path detection and restart
- 🌓 Light/Dark theme support
- 💻 Windows-optimized performance

## 🔧 Requirements

- Windows Operating System
- Steam Client installed
- Python 3.x
- SteamTools
- Internet connection

## 📦 Dependencies

```
customtkinter==5.2.1
pymongo==4.6.1
requests==2.31.0
pywin32==306
Pillow==10.1.0
aiohttp==3.9.1
PyInstaller==6.3.0
```

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/[your-username]/Crown-Elite.git
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Make sure SteamTools is installed and configured

4. Run the application:
```bash
python main.py
```

## 🌟 Usage

1. Launch Crown Elite
2. The app will automatically detect your Steam installation
3. Search for a game by name or AppID
4. View game details and DRM information
5. Use the automated manifest management features
6. Steam will restart automatically when needed

## 🤝 Community

Join our Discord community for support and updates:
[Crown Elite Discord Server](https://discord.gg/crwn)

## 🔧 Technical Details

Crown Elite features:
- Asynchronous operations with asyncio
- Direct integration with SteamTools plugin system
- Automatic Steam registry detection
- Modern Python async/await patterns
- CustomTkinter-based responsive UI

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Legal Notice

This software is provided "as is", without warranty of any kind. Users are responsible for ensuring their use of this tool complies with all applicable laws and terms of service.

---

<div align="center">
Made with ❤️ by Vassiliev for educational purposes
</div>
