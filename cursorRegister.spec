# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    hiddenimports=['tkinter', 'PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'pandas', 'scipy', 'PyQt5', 'PyQt6', 
        'PySide2', 'PySide6', 'wx', 'notebook', 'sphinx', 'jupyter',
        'IPython', 'ipykernel', 'nbconvert', 'nbformat', 'test', 'tests',
        'unittest', 'distutils', 'pkg_resources', 'setuptools', 'email',
        '_pytest', 'pytest', 'doctest', 'pycparser', 'pdb'
    ],
    noarchive=False,
    optimize=2,  # 优化级别设为2
)

# 删除一些不必要的模块以减小文件大小
excluded_binaries = [
    'VCRUNTIME140.dll',
    'MSVCP140.dll',
    'ucrtbase.dll',
    'api-ms-win*.dll',
    'Qt*.dll',
    'PySide*.dll',
    'sip*.dll',
    'python*.dll',
    'libopenblas*.dll',
    'mkl_*.dll'
]

a.binaries = TOC([x for x in a.binaries if not any(pattern.lower() in x[0].lower() for pattern in excluded_binaries)])

# 移除不需要的数据文件，保留tk相关文件，并排除 .env 和 README.md 文件
a.datas = TOC([x for x in a.datas if not x[0].startswith(('numpy', 'matplotlib')) and x[0] not in ['.env', 'README.md']])

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='cursorRegister',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # 保持启用以减小体积
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, 
    disable_windowed_traceback=True,  # 保持启用以减小体积
    argv_emulation=True,  # 采用参考设置
    target_arch=None,  # 保持默认值，需要时可通过环境变量指定
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    uac_admin=False,
)
