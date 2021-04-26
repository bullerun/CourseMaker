from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class AddLesson(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    file = FileField("Содержание", validators=[DataRequired()])
    video = StringField("Ссылка на видео", validators=[DataRequired()])
    submit = SubmitField('Применить')
