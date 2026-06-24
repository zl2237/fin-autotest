# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

ROOT = Path.cwd()

hiddenimports = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    'json',
    'yaml',
    'dotenv',
    'loguru',
    'requests',
    'allure',
    'pytest',
]

a = Analysis(
    ['GUI.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'testcases'), 'testcases'),
        (str(ROOT / 'data'), 'data'),
        (str(ROOT / 'api'), 'api'),
        (str(ROOT / 'core'), 'core'),
        (str(ROOT / 'workflows'), 'workflows'),
        (str(ROOT / 'utils'), 'utils'),
        (str(ROOT / 'config'), 'config'),
        (str(ROOT / 'dist' / 'jre'), 'jre'),
        (str(ROOT / 'dist' / 'allure'), 'allure'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='PRStudy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='PRStudy',
)
