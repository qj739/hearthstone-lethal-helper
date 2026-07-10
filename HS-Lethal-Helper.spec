# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — HS 斩杀助手

from pathlib import Path

ROOT = Path(SPECPATH)

a = Analysis(
    [str(ROOT / 'hdt_tracker.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'json'), 'json'),
        (str(ROOT / 'log.config'), '.'),
    ],
    hiddenimports=[
        'overlay_win',
        'overlay_settings_ui',
        'hdt_python.app_paths',
        'hdt_python.overlay_settings',
        'hdt_python.log_watcher',
        'hdt_python.power_parser',
        'hdt_python.lethal_checker',
        'hdt_python.board_damage',
        'hdt_python.spell_board',
        'hdt_python.spell_p0_concoction',
        'hdt_python.spell_p0_remove',
        'hdt_python.spell_p1_direct',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='HS-Lethal-Helper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / 'assets' / 'hs_lethal_helper.ico'),
)
