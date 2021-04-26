from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField

from wtforms.validators import DataRequired


class RegisterEmail(FlaskForm):
    email_confirmation = IntegerField('Потверждение почты', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')