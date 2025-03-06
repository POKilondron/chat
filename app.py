import os
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import logging
from utils import admin_required
import secrets
import string
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import uuid

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app and extensions
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")
# Если используется Neon PostgreSQL, изменим URL для использования connection pooling
database_url = os.environ.get("DATABASE_URL")
if database_url and '.us-east-2' in database_url:
    database_url = database_url.replace('.us-east-2', '-pooler.us-east-2')

# Если DATABASE_URL не установлен, используем SQLite как резервный вариант
if not database_url:
    database_url = 'sqlite:///instance/chat.db'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,  # Проверка соединения перед запросом
    'pool_recycle': 300,    # Переподключение каждые 5 минут
    'pool_timeout': 30,     # Таймаут для получения соединения из пула
    'max_overflow': 10      # Максимальное количество дополнительных соединений
}
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Create subdirectories for different file types
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'images'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'documents'), exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import models after db initialization
from models import User, ChatRoom, Message
from forms import LoginForm, RegisterForm, ChatRoomForm

# Create tables and first admin
with app.app_context():
    # Создаем таблицы, если они не существуют
    db.create_all()

    # Create admin user if doesn't exist
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # Generate a secure password
        password_length = 16
        alphabet = string.ascii_letters + string.digits + string.punctuation
        secure_password = ''.join(secrets.choice(alphabet) for i in range(password_length))

        admin = User(username='admin', is_admin=True)
        admin.set_password(secure_password)
        db.session.add(admin)
        db.session.commit()
        logging.info(f"Admin user created with password: {secure_password}")
        print(f"\n\nIMPORTANT! New admin password: {secure_password}\n\n")
    else:
        # Admin password remains unchanged for existing admin
        db.session.commit()
        print("\n\nAdmin account is already configured.\n\n")

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('rooms'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('rooms'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('rooms'))

    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('This username is already taken')
            return render_template('register.html', form=form)

        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rooms')
@login_required
def rooms():
    rooms = ChatRoom.query.all()
    form = ChatRoomForm()
    return render_template('rooms.html', rooms=rooms, form=form)

@app.route('/rooms/create', methods=['POST'])
@login_required
def create_room():
    form = ChatRoomForm()
    if form.validate_on_submit():
        room = ChatRoom(
            name=form.name.data,
            description=form.description.data,
            created_by_id=current_user.id
        )
        room.members.append(current_user)
        db.session.add(room)
        db.session.commit()
        flash('Room created successfully!')
        return redirect(url_for('rooms'))

    flash('Error creating room')
    return redirect(url_for('rooms'))

@app.route('/chat/<int:room_id>')
@login_required
def chat(room_id):
    room = ChatRoom.query.get_or_404(room_id)
    if current_user not in room.members:
        room.members.append(current_user)
        db.session.commit()
    return render_template('chat.html', room=room)

@app.route('/rooms/delete/<int:room_id>', methods=['POST'])
@login_required
def delete_room(room_id):
    room = ChatRoom.query.get_or_404(room_id)

    # Check if user is the creator of the room or an admin
    if room.created_by_id == current_user.id or current_user.is_admin:
        # Delete all messages in the room first
        Message.query.filter_by(room_id=room_id).delete()
        # Remove all members from the room
        room.members = []
        # Delete the room
        db.session.delete(room)
        db.session.commit()
        flash('Room deleted successfully!')
    else:
        flash('You do not have permission to delete this room.')

    return redirect(url_for('rooms'))

def allowed_file(filename):
    # Allow more file types
    allowed_extensions = {
        'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp',  # Images
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt',  # Documents
        'zip', 'rar', '7z',  # Archives
        'mp3', 'wav', 'ogg',  # Audio
        'mp4', 'avi', 'mov', 'webm'  # Video
    }
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/api/messages/<int:room_id>', methods=['GET'])
@login_required
def get_messages(room_id):
    try:
        messages = Message.query.filter_by(room_id=room_id).order_by(Message.timestamp).all()
        return jsonify([{
            'id': msg.id,
            'text': msg.text,
            'image_url': msg.image_url,
            'message_type': msg.message_type,
            'timestamp': msg.timestamp.strftime('%H:%M:%S'),
            'sender': msg.author.username
        } for msg in messages])
    except Exception as e:
        app.logger.error(f"Error fetching messages: {str(e)}")
        return jsonify({'error': 'Ошибка загрузки сообщений. Пожалуйста, попробуйте позже.'}), 500

@app.route('/api/messages/<int:room_id>', methods=['POST'])
@login_required
def post_message(room_id):
    try:
        room = ChatRoom.query.get_or_404(room_id)
        if current_user not in room.members:
            return jsonify({'error': 'You are not a member of this room'}), 403

        message_text = request.form.get('message', '').strip()
        file = request.files.get('image')  # File input name is still 'image' for backward compatibility

        if not message_text and not file:
            return jsonify({'error': 'Message or file is required'}), 400

        new_message = Message(
            user_id=current_user.id,
            room_id=room_id
        )

        if file and file.filename:
            if allowed_file(file.filename):
                # Generate unique filename to avoid collisions
                original_filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{original_filename}"

                # Determine file type and destination folder
                file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''

                if file_ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp']:
                    subfolder = 'images'
                    new_message.message_type = 'image'
                else:
                    subfolder = 'documents'
                    new_message.message_type = 'file'

                # Save file to appropriate subfolder
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], subfolder, unique_filename)
                file.save(file_path)

                # Create relative URL
                new_message.image_url = url_for('static', filename=f'uploads/{subfolder}/{unique_filename}')
                new_message.text = original_filename  # Save original filename as text
            else:
                return jsonify({'error': 'File type not allowed'}), 400
        else:
            new_message.message_type = 'text'
            new_message.text = message_text

        db.session.add(new_message)
        db.session.commit()

        return jsonify({
            'id': new_message.id,
            'text': new_message.text,
            'image_url': new_message.image_url,
            'message_type': new_message.message_type,
            'timestamp': new_message.timestamp.strftime('%H:%M:%S'),
            'sender': current_user.username
        })
    except Exception as e:
        app.logger.error(f"Error posting message: {str(e)}")
        return jsonify({'error': 'An error occurred while sending your message'}), 500

# We don't need SSE anymore as we're using polling
# This section is intentionally removed to avoid the SSE errors

@app.route('/api/users/status/<int:room_id>')
@login_required
def get_user_statuses(room_id):
    """Get online status of users in a room"""
    room = ChatRoom.query.get_or_404(room_id)

    # In a real app, you would track active users
    # For this example, we'll just return all members as active
    return jsonify([{
        'user_id': user.id,
        'username': user.username,
        'status': 'online'
    } for user in room.members])


@app.route('/start')
def start():
    """Start page for launching the application"""
    return render_template('start.html')

@app.route('/api/health-check')
def health_check():
    """Health check endpoint to verify the application is running"""
    return jsonify({"status": "ok", "message": "Application is running"}), 200

@app.route('/install')
def install():
    """Page with application installation instructions"""
    return render_template('install.html')

@app.route('/download-app')
def download_app():
    """Создание и отправка ZIP-архива с приложением"""
    try:
        import io
        import zipfile

        # Создаем ZIP-архив в памяти
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Список файлов, которые нужно добавить в архив
            files_to_include = [
                'app.py', 'models.py', 'forms.py', 'utils.py',
                'pyproject.toml', 'README.md', 'requirements.txt'
            ]

            # Добавляем основные файлы
            for file_name in files_to_include:
                if os.path.exists(file_name):
                    zf.write(file_name)

            # Добавляем шаблоны
            for root, dirs, files in os.walk('templates'):
                for file in files:
                    zf.write(os.path.join(root, file))

            # Добавляем статические файлы
            for root, dirs, files in os.walk('static'):
                for file in files:
                    zf.write(os.path.join(root, file))

            # Создаем requirements.txt, если его нет
            if not os.path.exists('requirements.txt'):
                with open('requirements.txt', 'w') as req_file:
                    req_file.write("""flask==3.1.0
flask-sqlalchemy==3.1.1
flask-login==0.6.3
flask-wtf==1.2.2
email-validator==2.2.0
gunicorn==23.0.0
psycopg2-binary==2.9.10
wtforms==3.2.1
werkzeug==3.1.3
""")
                zf.write('requirements.txt')

            # Создаем README.md
            if not os.path.exists('README.md'):
                with open('README.md', 'w') as readme_file:
                    readme_file.write("""# Pock Empire

Платформа для общения и обмена сообщениями.

## Установка

1. Установите Python 3.8 или выше
2. Установите зависимости: `pip install -r requirements.txt`
3. Запустите приложение: `python main.py`
4. Откройте в браузере: http://localhost:5000

## Данные для входа

- **Администратор**: admin / Adm1n@2025#Secure!Pass

## Возможности

- Создание и удаление комнат для общения
- Обмен текстовыми сообщениями и файлами
- Администрирование пользователей
""")
                zf.write('README.md')

        # Перемещаем указатель в начало файла
        memory_file.seek(0)

        # Отправляем файл пользователю
        return Response(
            memory_file,
            mimetype='application/zip',
            headers={'Content-Disposition': 'attachment;filename=pock_empire.zip'}
        )
    except Exception as e:
        app.logger.error(f"Ошибка при создании архива приложения: {str(e)}")
        flash('Произошла ошибка при создании архива приложения. Попробуйте позже.')
        return redirect(url_for('index'))

from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)