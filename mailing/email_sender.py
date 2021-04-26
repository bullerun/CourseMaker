import smtplib
import mimetypes
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from data import db_session
from data.users import User


def send_email(email, subject, text):
    addr_from = os.getenv("FROM")
    password = os.getenv("PASSWORD")
    msg = MIMEMultipart()
    msg['From'] = addr_from
    msg['To'] = email
    msg['Subject'] = subject
    body = 'Код подтверждения регистрации  -  ' + str(text)
    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP_SSL(os.getenv('HOST'), os.getenv('PORT'))
    server.login(addr_from, password)
    server.send_message(msg)
    server.quit()
    return True


def delete():
    db_sess = db_session.create_session()
    for i in db_sess.query(User).filter(User.checking == 0):
        db_sess.delete(i)
    db_sess.commit()
