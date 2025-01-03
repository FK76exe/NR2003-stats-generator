# -*- mode: python ; coding: utf-8 -*-

import os

a = Analysis(
    ['src/db.py', 'src/driver.py', 'src/file_scraper.py', 'src/main.py', 
    'src/points.py','src/race.py', 'src/series.py', 'src/team.py', 'src/track.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/db/*.sql', 'db'),
        ('src/templates','templates'),
        ('src/static/styles', 'static/styles')
    ],
    hiddenimports=['flask', 'bs4', 'sqlite3', 'ctypes'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['config.ini'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NR2003 Stats Generator 1.1',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='options',
)
