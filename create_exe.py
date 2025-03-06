
import os
import subprocess
import sys
from build_exe import build_exe

def main():
    print("PockEmpire EXE Builder")
    print("======================")
    
    # Устанавливаем необходимые пакеты
    print("Установка необходимых пакетов...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "pillow"], check=True)
    
    # Добавляем путь к pyinstaller в PATH
    python_lib_path = subprocess.check_output([sys.executable, "-m", "site", "--user-base"], text=True).strip()
    bin_path = os.path.join(python_lib_path, "bin")
    os.environ["PATH"] = bin_path + os.pathsep + os.environ.get("PATH", "")
    
    # Фиксируем базу данных - создаем пустую базу, если её нет
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    # Создаем favicon.ico
    print("Генерация иконки приложения...")
    subprocess.run([sys.executable, "generate_icon.py"], check=True)
    
    # Запускаем сборку
    print("Запуск процесса сборки...")
    result = build_exe()
    
    if result:
        print("\nСборка успешно завершена!")
        print("Исполняемый файл находится в директории dist/PockEmpire/")
        print("Запустите PockEmpire.exe для старта приложения")
    else:
        print("\nОшибка при сборке. Смотрите лог выше для деталей.")

if __name__ == "__main__":
    main()
