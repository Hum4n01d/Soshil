from datetime import datetime
from peewee import *

from flask_login import UserMixin
from flask_bcrypt import generate_password_hash, check_password_hash

DATABASE = SqliteDatabase('soshil.db')

class User(UserMixin, Model):
    username = CharField()
    low_username = CharField(unique=True)
    email = CharField(unique=True)
    password = CharField(max_length=100)
    joined_date = DateTimeField(default=datetime.now)
    is_admin = BooleanField(default=False)
    github_user = BooleanField(default=False)
  
    class Meta:
        database = DATABASE
    
    @classmethod
    def create_user(cls, username, email, password, admin=False, github_user=False, low_username=low_username):
        if github_user:
            cls.create(
                username=username,
                email=email,
                password='',
                is_admin=admin,
                github_user=github_user,
                low_username=low_username
            )
        else:
            try:
                cls.create(
                    username=username,
                    low_username=username,
                    email=email,
                    password=generate_password_hash(password),
                    is_admin=admin
                )
            except IntegrityError:
                raise ValueError('User already exists')
    
def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User], safe=True)
    DATABASE.close()