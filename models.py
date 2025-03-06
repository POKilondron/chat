from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationships
    messages = db.relationship('Message', backref='author', lazy='dynamic')
    rooms = db.relationship('ChatRoom', secondary='room_members', backref='members')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_administrator(self):
        return self.is_admin

class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    messages = db.relationship('Message', backref='room', lazy='dynamic')
    created_by = db.relationship('User', foreign_keys=[created_by_id])

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(1024))
    image_url = db.Column(db.String(512))  # For storing image URLs
    message_type = db.Column(db.String(10), default='text')  # 'text' or 'image'
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)

# Association table for room members
room_members = db.Table('room_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('room_id', db.Integer, db.ForeignKey('chat_room.id'), primary_key=True)
)