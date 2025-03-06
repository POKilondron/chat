
import os
import sys
import socket
import webbrowser
import threading
import time
from app import app

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
