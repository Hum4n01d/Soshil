from flask_wtf import Form
from wtforms import StringField, PasswordField, TextAreaField, BooleanField
from wtforms.validators import (DataRequired, Regexp, ValidationError, Email, Length, EqualTo)

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
    
class LoginForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    
class PostForm(Form):
    title = StringField('Post title', validators=[DataRequired()])
    content = TextAreaField("What's on your mind?", id='content', validators=[DataRequired()])

class CommentForm(Form):
    content = TextAreaField("Leave a comment", id="comment_editor", validators=[
        DataRequired(),
        Length(max=250)
    ])