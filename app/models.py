from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from datetime import datetime
import secrets
import string

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(12), unique=True, nullable=False, index=True)  # Random 10-12 char ID
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # student, teacher, admin
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True) # For students
    is_active = db.Column(db.Boolean, default=True)
    is_password_temporary = db.Column(db.Boolean, default=False)  # Temporary password flag
    profile_pic = db.Column(db.String(255), nullable=True, default='default.jpg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.user_id:
            self.user_id = self.generate_user_id()
    
    @staticmethod
    def generate_user_id():
        """Generate a random 10-12 character user ID"""
        length = secrets.choice([10, 11, 12])
        chars = string.ascii_letters + string.digits
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = bcrypt.generate_password_hash(password.encode('utf-8')).decode('utf-8')
    
    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return bcrypt.check_password_hash(self.password_hash, password.encode('utf-8'))
    
    def get_full_name(self):
        """Return the full name of the user"""
        return f"{self.firstname} {self.lastname}"

    def get_id(self):
        """Use the random user_id in session handling"""
        return str(self.user_id)
    
    def __repr__(self):
        return f'<User {self.user_id}>'


class ClassGroup(db.Model):
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    
    students = db.relationship('User', backref='class_group', lazy=True)
    schedules = db.relationship('ScheduleEvent', backref='class_group', lazy=True)

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    prof_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    prof = db.relationship('User', backref='courses_taught')
    schedules = db.relationship('ScheduleEvent', backref='course', lazy=True)
    grades = db.relationship('Grade', backref='course', lazy=True)

class ScheduleEvent(db.Model):
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    room = db.Column(db.String(50))
    event_type = db.Column(db.String(50)) # e.g. "CM", "TD", "Exam"

class Grade(db.Model):
    __tablename__ = 'grades'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    value = db.Column(db.Float, nullable=False)
    coefficient = db.Column(db.Float, default=1.0)
    exam_name = db.Column(db.String(100)) # e.g. "Partiel 1"
    
    student = db.relationship('User', backref='grades')

class Absence(db.Model):
    __tablename__ = 'absences'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False)
    is_justified = db.Column(db.Boolean, default=False)
    
    student = db.relationship('User', backref='absences')
    schedule = db.relationship('ScheduleEvent', backref='absences')

class PasswordReset(db.Model):
    __tablename__ = 'password_resets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref='password_resets')
    
    def is_valid(self):
        """Check if the reset token is still valid"""
        return not self.used and datetime.utcnow() < self.expires_at
    
    def __repr__(self):
        return f'<PasswordReset {self.email}>'
