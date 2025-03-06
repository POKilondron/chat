from app import app
import os
import logging

# Настройка логирования для скрытия конфиденциальной информации
logger = logging.getLogger('werkzeug')
logger.setLevel(logging.ERROR)

if __name__ == "__main__":
    # Отключаем вывод отладочной информации, которая может содержать конфиденциальные данные
    os.environ['FLASK_DEBUG'] = '0'
    app.run(host="0.0.0.0", port=5000, debug=False)