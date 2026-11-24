# PyInstaller spec: ProjectDash Server (zentrale Datenhaltung)
# Build: pyinstaller --clean build/projectdash_server.spec

import os

block_cipher = None

a = Analysis(
    ["../run_server.py"],
    pathex=[os.path.abspath("..")],
    binaries=[],
    datas=[],
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "server.auth",
        "server.seed",
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
    name="ProjectDashServer",
    debug=False,
    console=True,
    uac_admin=False,
)
