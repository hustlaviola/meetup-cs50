import os
from PIL import Image
import secrets
from flask import url_for, current_app
from meetup import mail
from flask_mail import Message


def save_img(form_img):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_img.filename)
    img_fn = random_hex + f_ext
    img_path = os.path.join(current_app.root_path, 'static/profile-imgs', img_fn)
    size = (125, 125)
    image = Image.open(form_img)
    image.thumbnail(size)
    image.save(img_path)
    return img_fn


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset', sender='noreply@fiosa.com',
                  recipients=[user.email])
    msg.body = f'''Visit the following link to reset your password:
{url_for('users.reset_password', token=token, _external=True)}

If you did not make this request, ignore this email and you are good.
'''
    mail.send(msg)
