# models/student.py

from werkzeug.security import generate_password_hash, check_password_hash

class Student:
    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password_hash = generate_password_hash(password)

    def to_dict(self):
        return {
            "name": self.name,
            "email": self.email,
            "password": self.password_hash
        }

    @staticmethod
    def check_password(stored_password_hash, entered_password):
        return check_password_hash(stored_password_hash, entered_password)
