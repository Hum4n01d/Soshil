from flask_wtf import Form, RecaptchaField
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import (DataRequired, Regexp, ValidationError, Email, Length, EqualTo, Optional, URL, AnyOf)

from models import User

def name_exists(form, field):
    if User.select().where(User.username == field.data).exists():
        raise ValidationError('That username already exists.')

def email_exists(form, field):
    if User.select().where(User.email == field.data).exists():
        raise ValidationError('That email is already registered.')

class RegisterForm(Form):
    username = StringField(
        'Username',
        validators=[
            DataRequired(),
            Length(max=15, message='Usernames must be 15 characters or less'),
            Regexp(
                r'^[a-zA-Z0-9_​]+$',
                message=('Username can only contain letters, numbers, and underscores')
            ),
            name_exists
        ])
    email = StringField(
        'Email (gravatar will be used)',
        validators=[
            DataRequired(),
            Email(),
            email_exists
        ])
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=6),
            EqualTo('password2', message='Passwords must match')
        ])
    password2 = PasswordField(
        'Confirm Password',
        validators=[DataRequired()]
    )
    recaptcha = RecaptchaField()
    
class LoginForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    
class PostForm(Form):
    title = StringField('Post title', validators=[
        DataRequired(),
        Length(max=100)
    ])
    content = TextAreaField("What's on your mind?", id='editor', validators=[
        DataRequired(),
        Length(max=10000, message='Posts must be within 10000 characters')
    ])

class CommentForm(Form):
    content = TextAreaField("Leave a comment", id="editor", validators=[
        DataRequired(),
        Length(max=250)
    ])

class AccountForm(Form):
    avatar_url = StringField(validators=[
        Optional(),
        URL()
    ])
    email = StringField(validators=[
        Optional(),
        Email(),
        email_exists
    ])

class DeleteForm(Form):
    username = StringField(validators=[
        DataRequired()
    ])