from flask import Flask, render_template, redirect, request, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from sqlalchemy import desc
import random

from data import db_session
from data.users import User
from data.lesson import Lesson
from data.commenter import Commenter
from forms.login import LoginForm
from forms.addlesson import AddLesson
from forms.comment import Comment
from forms.changeprofile import ChangeProfile
from forms.reg_email import RegisterEmail
from forms.register import RegisterForm
from mailing.email_sender import send_email, delete

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


# Создание базы данных
def main():
    db_session.global_init("db/table.sqlite")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


# Показывает основную страницу
@app.route("/index/")
@app.route("/")
def index():
    return redirect('/index/all')


# Сортировка основной страницы
@app.route("/index/<key>")
@app.route("/<key>")
def index_key(key):
    font = 'font_width1'
    db_sess = db_session.create_session()
    if key == 'date':
        lessons = db_sess.query(Lesson).order_by(
            desc("created_date")
        ).all()
        data = {
            'date': font
        }
    elif key == 'comm':
        lessons = db_sess.query(Lesson).all()
        for lesson in lessons:
            lesson.count_comment = len(db_sess.query(Commenter).filter(
                Commenter.lesson_id == lesson.id
            ).all())
        data = {
            'comm': font
        }
        lessons = db_sess.query(Lesson).order_by(desc("count_comment")).all()
    else:
        lessons = db_sess.query(Lesson).all()
        data = {
            'all': font
        }
    db_sess.commit()
    return render_template("index.html", item=lessons, current_user=current_user, data=data)


# Вход на сайт
@app.route('/login', methods=['GET', 'POST'])
def login():
    db_sess = db_session.create_session()
    delete()
    form = LoginForm()
    if form.validate_on_submit():
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


# Регистрация на сайте
@app.route('/register', methods=['GET', 'POST'])
def reqister():
    global text_msg, email
    form = RegisterForm()
    delete()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        text_msg = random.randint(10000, 99999)
        email = form.email.data
        send_email(email, 'Потверждение почты', str(text_msg))
        user = User(
            name=form.name.data,
            email=form.email.data,
            checking=False
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/register_email')
    return render_template('register.html', title='Регистрация', form=form)


# Проверки email во время регистрации
@app.route('/register_email', methods=['GET', 'POST'])
def check_email():
    form_chek = RegisterEmail()
    if form_chek.validate_on_submit():
        db_sess = db_session.create_session()
        if not text_msg == form_chek.email_confirmation.data:
            for i in db_sess.query(User).filter(User.checking == 0):
                db_sess.delete(i)
                db_sess.commit()
            return redirect('/register')
        user = db_sess.query(User).filter(User.email == email).first()
        user.checking = True
        db_sess.commit()
        return redirect('/login')
    return render_template('register_email.html', form=form_chek, title='Регистрация')


# Выход с аккаунта
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# Показывает курс и создание и показывание коментариев
@app.route('/course/<int:id>', methods=['GET', 'POST'])
def course(id):
    if not current_user.is_authenticated:
        return redirect('/login')
    form = Comment()
    db_sess = db_session.create_session()
    href_video = db_sess.query(Lesson).filter(Lesson.id == id).first().video
    title_lesson = db_sess.query(Lesson).filter(Lesson.id == id).first().title
    if not (db_sess.query(Lesson).filter(Lesson.id == id
                                         ).first()):
        abort(404)
    current_user.last_lesson_attended = id
    db_sess.merge(current_user)
    db_sess.commit()
    if form.validate_on_submit():
        commenter = Commenter()
        commenter.comment = form.comment_zone.data
        commenter.lesson_id = id
        commenter.user_id = current_user.id
        db_sess.add(commenter)
        db_sess.commit()
        return redirect(f'/course/{id}')
    comments = db_sess.query(Commenter).order_by(desc("created_date"
                                                      )).filter(Commenter.lesson_id == id
                                                                )
    db_sess.commit()
    return render_template('course.html', form=form,
                           comments=comments,
                           href_video=href_video,
                           title_lesson=title_lesson)


# Добавление курса
@app.route('/add_course', methods=['GET', 'POST'])
@login_required
def add_curse():
    form_href = AddLesson()
    if form_href.validate_on_submit():
        db_sess = db_session.create_session()
        lesson = Lesson()
        try:
            create_href_for_youtube = form_href.video.data.split('watch?v=')
            create_href_for_youtube[1] = 'embed/' + create_href_for_youtube[1]
            if '&' in create_href_for_youtube[1]:
                create_href_for_youtube[1] = create_href_for_youtube[1].split('&')[0]
            lesson.video = ''.join(create_href_for_youtube)
        except IndexError:
            message = "Не верно указанна ссылка"
            return render_template('add_curse.html', title='Добавление ссылки на курс',
                                   form_href=form_href, message=message)
        name = form_href.file.data
        new_name = 'new_' + str(name).split("\'")[1]
        with open(f'static/svg/{new_name}', 'wb') as file:
            file.write(name.read())
        lesson.file = f'/static/svg/{new_name}'
        lesson.title = form_href.title.data
        lesson.user_id = current_user.id
        db_sess.add(lesson)
        db_sess.commit()
        return redirect('/')
    return render_template('add_curse.html', title='Добавление ссылки на курс',
                           form_href=form_href)


# Изменение курса
@app.route('/add_course/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_course(id):
    form_href = AddLesson()
    if request.method == "GET":
        db_sess = db_session.create_session()
        lesson = db_sess.query(Lesson).filter(Lesson.id == id
                                              ).first()
        if lesson:
            form_href.title.data = lesson.title
            form_href.video.data = lesson.video
            form_href.file.data = lesson.title
        else:
            abort(404)
    if form_href.validate_on_submit():
        db_sess = db_session.create_session()
        lesson = db_sess.query(Lesson).filter(Lesson.id == id
                                              ).first()
        if lesson:
            lesson.title = form_href.title.data
            name = form_href.file.data
            new_name = 'new_' + str(name).split("\'")[1]
            with open(f'static/svg/{new_name}', 'wb') as file:
                file.write(name.read())
            lesson.file = f'/static/svg/{new_name}'
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('add_curse.html',
                           title='Редактирование ссылки на курс',
                           form_href=form_href
                           )


# Удаление курса
@app.route('/course_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def course_delete(id):
    db_sess = db_session.create_session()
    lesson = db_sess.query(Lesson).filter(Lesson.id == id).first()
    comments = db_sess.query(Commenter).filter(Commenter.lesson_id == id).all()
    if lesson:
        db_sess.delete(lesson)
        for comment in comments:
            db_sess.delete(comment)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


# Изменение профиля
@app.route('/change', methods=['GET', 'POST'])
def change():
    form = ChangeProfile()
    if request.method == "GET":
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id
                                          ).first()
        if user:
            form.name.data = user.name
            form.email.data = user.email
            form.about.data = user.about
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data,
                                      form.email.data != current_user.email).first():
            return render_template('change.html', title='Профиль',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = db_sess.query(User).filter(User.id == current_user.id
                                          ).first()
        user.name = form.name.data
        user.email = form.email.data
        user.about = form.about.data
        db_sess.commit()
        return redirect('/')
    return render_template('change.html', title='Профиль', form=form)


if __name__ == '__main__':
    main()
    app.run(port=8080, host='127.0.0.1')
