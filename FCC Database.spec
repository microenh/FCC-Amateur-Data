# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['fcc.py'],
    pathex=[],
    binaries=[],
    datas=[('./FCC_Seal_1934_125.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FCC Database',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['FCC_Seal.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FCC Database',
)
app = BUNDLE(
    coll,
    name='FCC Database.app',
    icon='FCC_Seal.icns',
    version='0.1.0.0β',
    bundle_identifier=None,
    info_plist = {
	    'NSHumanReadableCopyright' : 'Copyright ©2023 Microcomputer Enhancement.\nAll rights reserved.'
    }
)
