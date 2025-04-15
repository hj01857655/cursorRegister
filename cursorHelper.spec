import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 获取所有可能的依赖项
tab_imports = collect_submodules('tab')
drissionpage_imports = collect_submodules('DrissionPage')
loguru_imports = collect_submodules('loguru')
qt_imports = collect_submodules('PyQt5')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('.env.example', '.'),  # 添加环境变量示例文件
        ('turnstilePatch', 'turnstilePatch'),  # 包含turnstilePatch目录
    ],
    hiddenimports=[
        'tkinter', 
        'tkinter.ttk',
        'PIL._tkinter_finder',
        'loguru',
        'dotenv',
        'drissionpage',
        'PyQt5',
        'PyQt5.QtWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'playwright',
        'email',
        'email.mime',
        'email.mime.text',
        'email.mime.multipart',
        'ca_certificates',
        'requests',
        'urllib3',
        'json',
        'faker',
        'csv',
        'utils',
        'registerAc',
        'cursor',
        'uuid',
        'base64',
        'webbrowser',
        'datetime',
        'random',
        'string',
        're',
        'ssl',
        'zipfile',
        'tabulate',
    ] + tab_imports + drissionpage_imports + loguru_imports + qt_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'pandas', 'scipy', 
        'wx', 'notebook', 'sphinx', 'jupyter',
        'IPython', 'ipykernel', 'nbconvert', 'nbformat', 'test', 'tests',
        'unittest', 'distutils', 'pkg_resources',
        '_pytest', 'pytest', 'doctest', 'pycparser', 'pdb'
    ],
    noarchive=False,
    optimize=2,
)

# 减少不必要的排除，确保Qt组件被正确包含
excluded_binaries = [
    'api-ms-win-core*.dll',
    'api-ms-win-crt*.dll',
    'libopenblas*.dll',
    'mkl_*.dll'
]

# 使用更温和的过滤方式
a.binaries = TOC([x for x in a.binaries if not any(
    pattern.lower() in x[0].lower() and '*' in pattern 
    for pattern in excluded_binaries
)])

# 过滤数据文件，但保留必要文件
a.datas = TOC([
    x for x in a.datas 
    if not x[0].startswith(('numpy', 'matplotlib')) 
    and not x[0] in ['.env']  # 只排除.env，保留其他所有数据文件
])

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='cursorHelper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    requestedExecutionLevel='requireAdministrator',  # 明确要求管理员权限
    uac_admin=True,  # 请求管理员权限
)

