from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


class ChangeProfile(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    name = StringField('Логин', validators=[DataRequired()])
    about = TextAreaField('Расскажите о себе')
    submit = SubmitField('Изменить профиль')
