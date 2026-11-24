# PyInstaller spec: ProjectDash Client (Desktop-App)
# Build: pyinstaller --clean build/projectdash_client.spec

import os

block_cipher = None

a = Analysis(
    ["../run_client.py"],
    pathex=[os.path.abspath("..")],
    binaries=[],
    datas=[],
    hiddenimports=[
        "PySide6.QtCharts",
        "PySide6.QtSvg",
        "server.auth",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "PyQt5", "PyQt6"],
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="ProjectDashClient",
    icon="projectdash.ico" if os.path.exists("projectdash.ico") else None,
    debug=False,
    console=False,
    uac_admin=False,
)
