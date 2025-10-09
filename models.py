from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import hashlib

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    password_sha1 = db.Column(db.String(40))  # SHA1 хеш для работы с iiko
    email = db.Column(db.String(120), unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Связь с филиалами
    branches = db.relationship('UserBranch', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Устанавливает хеш пароля и SHA1 хеш"""
        self.password_hash = generate_password_hash(password)
        # Сохраняем SHA1 хеш для работы с iiko API
        self.password_sha1 = hashlib.sha1(password.encode()).hexdigest()
    
    def check_password(self, password):
        """Проверяет пароль"""
        return check_password_hash(self.password_hash, password)
    
    def get_sha1_password(self):
        """Возвращает SHA1 хеш пароля для работы с iiko API"""
        return self.password_sha1
    
    def __repr__(self):
        return f'<User {self.username}>'

class UserBranch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    branch_id = db.Column(db.String(100), nullable=False)
    branch_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserBranch {self.user_id}:{self.branch_name}>'

