from datetime import datetime

def get_boot_art(stage: int) -> str:
    """Return ASCII art for each boot stage"""
    boot_arts = [
        """
        ░░░░░░░░░░░░░░░░░
        ░░ SYSTEM CORE ░░
        ░░░░░░░░░░░░░░░░░
        """,
        """
        ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
        ▒ CRYPTO ENGINE ▒
        ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
        """,
        """
        ╔══════════════════╗
        ║ SATELLITE UPLINK ║
        ╚══════════════════╝
        """,
        """
        █████████████████████
        █ THREAT ASSESSMENT █
        █████████████████████
        """,
        """
        ╔═══════════════════╗
        ║ BIOMETRIC SCANNER ║
        ║ ░░░░░░░░░░░░░░░░░ ║
        ╚═══════════════════╝
        """,
        """
        ░▒▓█████████████▓▒░
        ░▒▓ AGENT COMMS ▓▒
        ░▒▓█████████████▓▒░
        """,
        """
        █▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
        █  ENCRYPTION ENG  █
        █▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█
        """,
        """
        ╔═══════════════════╗
        ║ PROTOCOL VERIFIED ║
        ╚═══════════════════╝
        """
    ]
    return boot_arts[stage % len(boot_arts)]

def get_isac_banner() -> str:
    """Return the final ISAC ready banner"""
    return """```diff
░▒▓██████████████████████████████████████████▓▒░
░▒▓█                                        █▓▒░
░▒▓█        ██╗███████╗ █████╗  ██████╗     █▓▒░
░▒▓█        ██║██╔════╝██╔══██╗██╔════╝     █▓▒░
░▒▓█        ██║███████╗███████║██║          █▓▒░
░▒▓█        ██║╚════██║██╔══██║██║          █▓▒░
░▒▓█        ██║███████║██║  ██║╚██████╗     █▓▒░
░▒▓█        ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝     █▓▒░
░▒▓█                                        █▓▒░
░▒▓█       ███████╗██╗  ██╗██████╗          █▓▒░
░▒▓█       ██╔════╝██║  ██║██╔══██╗         █▓▒░
░▒▓█       ███████╗███████║██║  ██║         █▓▒░
░▒▓█       ╚════██║██╔══██║██║  ██║         █▓▒░
░▒▓█       ███████║██║  ██║██████╔╝         █▓▒░
░▒▓█       ╚══════╝╚═╝  ╚═╝╚═════╝          █▓▒░
░▒▓█                                        █▓▒░
░▒▓█  INTELLIGENT SYSTEM ANALYTIC COMPUTER  █▓▒░
░▒▓█  SHD NETWORK: ONLINE                   █▓▒░
░▒▓█  SYSTEM TIME: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """      █▓▒░
░▒▓█  READY FOR FIELD SUPPORT               █▓▒░
░▒▓█                                        █▓▒░
░▒▓██████████████████████████████████████████▓▒░

[STATUS] All systems operational
[ALERT] Authentication required for agent access
```"""

def generate_shd_box(message: str) -> str:
    """Create SHD-styled ASCII message box"""
    lines = message.split('\n')
    max_len = max(len(line) for line in lines)
    
    top_border = f"╔{'═' * (max_len + 2)}╗"
    bottom_border = f"╚{'═' * (max_len + 2)}╝"
    
    content = []
    for line in lines:
        content.append(f"║ {line.ljust(max_len)} ║")
    
    return (
        f"```diff\n{top_border}\n"
        + "\n".join(content) +
        f"\n{bottom_border}\n```"
    )

SHD_SYMBOLS = [
    """
    ███████╗██╗  ██╗██████╗ 
    ██╔════╝██║  ██║██╔══██╗
    ███████╗███████║██║  ██║
    ╚════██║██╔══██║██║  ██║
    ███████║██║  ██║██████╔╝
    ╚══════╝╚═╝  ╚═╝╚═════╝ 
    """,
    """
    +---------------+
    |  SHD NETWORK  |
    |   ACCESSING   |
    |  DATA STREAMS |
    +---------------+
    """,
    """
    ░▒▓███████▓▒░
    ░▒▓█▓▒░░▒▓█▓▒░
    ░▒▓█▓▒░      ░▒▓█▓▒░SHD SYSTEM
    ░▒▓█▓▒░      ░▒▓█▓▒░ANALYSIS MODE
    ░▒▓█▓▒░░▒▓█▓▒░
    ░▒▓███████▓▒░
    """
]