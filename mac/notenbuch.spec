# -*- mode: python ; coding: utf-8 -*-
# Die Version wird von mac/make_build.py eingesetzt.
VERSION = '__VERSION__'

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('index.html', '.'),
    ],
    hiddenimports=['flask', 'jinja2', 'werkzeug', 'click', 'itsdangerous'],
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
    name='Notenbuch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Notenbuch',
)

app = BUNDLE(
    coll,
    name='Notenbuch.app',
    icon=None,
    bundle_identifier='at.drosg.notenbuch',
    info_plist={
        'CFBundleShortVersionString': VERSION,
        'CFBundleName': 'Notenbuch',
        'LSMinimumSystemVersion': '12.0',
        'NSHighResolutionCapable': True,
    },
)
