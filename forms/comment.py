from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class Comment(FlaskForm):
    comment_zone = StringField(validators=[DataRequired()])
    submit = SubmitField('Отправить')
