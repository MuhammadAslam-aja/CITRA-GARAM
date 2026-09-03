from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from app import login_manager
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'tb_user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)  # Ensure username is unique
    password = db.Column(db.String(255), nullable=False)
    plain_password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Hash the password and store it."""
        self.password = generate_password_hash(password)  # Store hashed password

    def checkPassword(self, password):
        return check_password_hash(self.password, password)

    def is_authenticated(self):
        return True  # Return True if the user is authenticated

    def is_active(self):
        return True  # Return True if the user is active

    def is_anonymous(self):
        return False  # Return False if the user is not anonymous

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))