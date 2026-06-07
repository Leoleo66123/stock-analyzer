# -*- mode: python -*-
a = Analysis(['run.py'], pathex=[], binaries=[], datas=[],
    hiddenimports=['socket','logging','subprocess','webbrowser','urllib.request'],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['tkinter','matplotlib'],
    win_no_prefer_redirects=False, win_private_assemblies=False,
    cipher=None, noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name='StockAnalyzer', debug=False, strip=False, upx=True,
    console=False, disable_windowed_traceback=True,
    target_arch='x86_64', icon=None,
)