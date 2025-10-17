# -*- mode: python; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import (
        collect_dynamic_libs,
        collect_data_files,
        collect_submodules,
)

block_cipher = None

# Data files: (source, destination_folder)
datas = [
    ('vocab.txt', '.'),
    ('decoder_joint-model.onnx', '.'),
    ('encoder-model.onnx', '.'),
    ('parrator/resources/icon.png', 'resources'),
    ('parrator/resources/icon.ico', 'resources'),
    ('parrator/hotkey_manager.py', 'parrator'),
] + collect_data_files('onnx_asr')

# Binaries: dynamic libs from onnxruntime
binaries = collect_dynamic_libs('onnxruntime')

funasr_modules = []
modelscope_modules = []

try:
    import funasr  # noqa: F401

    funasr_modules = collect_submodules('funasr')
except Exception:
    pass

try:
    import modelscope  # noqa: F401

    modelscope_modules = collect_submodules('modelscope')
except Exception:
    pass

a = Analysis(
    ['parrator/__main__.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=(
        [
            'onnxruntime.capi._pybind_state',
            'pynput',
            'pynput.keyboard',
            'parrator.hotkey_manager',
            'parrator.audio_recorder',
            'parrator.config',
            'parrator.transcriber',
            'parrator.notifications',
            'parrator.startup',
            'parrator.tray_app',
        ]
        + funasr_modules
        + modelscope_modules
    ),
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
    [],
    exclude_binaries=True,
    name='Parrator',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    onefile=True,
    icon='parrator/resources/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='Parrator',
)

