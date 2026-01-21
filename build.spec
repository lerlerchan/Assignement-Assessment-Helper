# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Teacher Grading Assistant
Build command: pyinstaller build.spec
"""

import sys
from pathlib import Path

block_cipher = None

# Application root directory
ROOT_DIR = Path(SPECPATH)

# Collect all data files
datas = [
    (str(ROOT_DIR / 'templates'), 'templates'),
    (str(ROOT_DIR / 'static'), 'static'),
]

# Hidden imports for dynamic imports
hiddenimports = [
    # Flask and dependencies
    'flask',
    'werkzeug',
    'jinja2',
    'markupsafe',
    'itsdangerous',
    'click',

    # PDF processing
    'pdfplumber',
    'PyPDF2',
    'PIL',
    'PIL.Image',

    # AI providers
    'openai',
    'anthropic',
    'google.generativeai',
    'aiohttp',

    # Excel export
    'openpyxl',
    'openpyxl.styles',
    'openpyxl.utils',

    # Security
    'cryptography',
    'cryptography.fernet',
    'cryptography.hazmat.primitives',
    'cryptography.hazmat.primitives.hashes',
    'cryptography.hazmat.primitives.kdf.pbkdf2',

    # Standard library
    'asyncio',
    'json',
    'uuid',
    'threading',
    'datetime',
    're',

    # Application modules
    'models',
    'models.student',
    'models.rubric',
    'models.grade_result',
    'providers',
    'providers.base_provider',
    'providers.openai_provider',
    'providers.anthropic_provider',
    'providers.gemini_provider',
    'providers.ollama_provider',
    'providers.lmstudio_provider',
    'providers.generic_provider',
    'services',
    'services.pdf_service',
    'services.ai_service',
    'services.grading_service',
    'services.export_service',
    'utils',
    'utils.config_manager',
    'utils.file_manager',
]

a = Analysis(
    ['app.py'],
    pathex=[str(ROOT_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'cv2',
        'tensorflow',
        'torch',
    ],
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
    name='TeacherGradingAssistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one: icon='icon.ico'
)
