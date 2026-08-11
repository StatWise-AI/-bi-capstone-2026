# -*- mode: python ; coding: utf-8 -*-
# ==============================================================================
# launcher.spec
# PyInstaller build spec for the silent Uber India Analytics Dashboard
# bootstrap launcher.
#
# Produces a single, windowless (no console, no GUI) executable:
#   dist/UberAI.exe
#
# This launcher has NO user interface of any kind (no Tkinter, no
# CustomTkinter) -- it is a pure background bootstrapper, so this spec is
# intentionally minimal: no data files, no image/font assets, no extra
# hidden imports beyond the standard library.
#
# Build with:
#   build_launcher.bat
# or manually:
#   pyinstaller launcher.spec
# ==============================================================================

import os

block_cipher = None

PROJECT_ROOT = os.path.abspath(os.path.dirname(__name__) or ".")

# Optional icon for the .exe. Drop a Windows .ico file named app_icon.ico
# next to this spec file to use it; otherwise PyInstaller's default is used.
icon_path = os.path.join(PROJECT_ROOT, "app_icon.ico")
icon_arg = icon_path if os.path.isfile(icon_path) else None

a = Analysis(
    ["launcher.py"],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "customtkinter", "PIL", "unittest", "test"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="UberAI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,        # <-- no CMD/console window, ever
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_arg,
)
