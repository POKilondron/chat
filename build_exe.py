
import os
import sys
import subprocess
import webbrowser
import socket
import time
import threading

def build_exe():
    print("Начало сборки PockEmpire.exe...")
    
    # Создаем файл spec для PyInstaller
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('instance', 'instance')
    ],
    hiddenimports=['sqlalchemy', 'flask_sqlalchemy', 'flask_login', 'email_validator'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PockEmpire',
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
    icon='static/favicon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PockEmpire',
)
    """
    
    # Создаем favicon.ico для иконки приложения
    try:
        from PIL import Image
        img = Image.open('generated-icon.png')
        if not os.path.exists('static/favicon.ico'):
            img.save('static/favicon.ico')
    except Exception as e:
        print(f"Предупреждение: Не удалось создать иконку: {e}")
        pass
    
    # Создаем spec файл
    with open('pockempire.spec', 'w') as f:
        f.write(spec_content)
    
    # Создаем standalone.py - точку входа для приложения
    standalone_content = """from app import app
import webbrowser
import socket
import time
import threading

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def get_free_port(start=5000, end=5100):
    for port in range(start, end):
        if not is_port_in_use(port):
            return port
    return 5000  # Возвращаем 5000, если не нашли свободный порт

def open_browser(port):
    time.sleep(1.5)  # Ждем, пока сервер запустится
    webbrowser.open(f'http://localhost:{port}')

if __name__ == '__main__':
    # Найти свободный порт
    port = get_free_port()
    
    # Открыть браузер после запуска сервера
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    
    # Запустить сервер Flask
    app.run(host='0.0.0.0', port=port, debug=False)
"""
    
    with open('standalone.py', 'w') as f:
        f.write(standalone_content)
    
    # Изменяем spec файл, чтобы использовал standalone.py вместо main.py
    with open('pockempire.spec', 'r') as f:
        content = f.read()
    
    content = content.replace("['main.py']", "['standalone.py']")
    
    with open('pockempire.spec', 'w') as f:
        f.write(content)
    
    # Запускаем PyInstaller для сборки приложения
    try:
        subprocess.run([sys.executable, "-m", "pyinstaller", "pockempire.spec"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при запуске PyInstaller: {e}")
        return False
