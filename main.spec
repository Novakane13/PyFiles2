# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['controllers/main.py'],
    pathex=['/path/to/project'],
    binaries=[],
    datas=[('controllers', 'controllers'), ('views', 'views'), ('resources', 'resources'), ('models/pos_system.db', 'models')],
    hiddenimports=['sqlite3', 'controllers.customersearch', 'controllers.tickettype',
                   'controllers.garmentscolors', 'controllers.ticketoptions', 'controllers.customeraccount',
                   'controllers.garmentpricing', 'controllers.detailedticket', 'controllers.quickticket', 'bcrypt'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
