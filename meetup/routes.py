import os
from PIL import Image
import secrets
from flask import render_template, url_for, flash, redirect, request
from meetup import app, db, bcrypt
from meetup.forms import RegistrationForm, LoginForm, UpdateProfileForm
from meetup.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required

posts = [
    {
        "message": "My post is big, need your comments",
        "time": "06:30am"
    },
    {
        "message": "My post is not small, lets see whatsup",
        "time": "04:30am"
    },
    {
        "message": "My post is very small, need your likes",
        "time": "07:30am"
    }
]

@app.route('/')
def index():
    return render_template('index.html', posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created successfully', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash(f'Invalid username/password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
    
@app.route('/about')
def about():
    return render_template('about.html')

def save_img(form_img):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_img.filename)
    img_fn = random_hex + f_ext
    img_path = os.path.join(app.root_path, 'static/profile-imgs', img_fn)
    size = (125, 125)
    image = Image.open(form_img)
    image.thumbnail(size)
    image.save(img_path)
    return img_fn

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        if form.image.data:
            img_file = save_img(form.image.data)
            current_user.image_file = img_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    img = url_for('static', filename='profile-imgs/' + current_user.image_file)
    return render_template('profile.html', img=img, form=form)

@app.route('/posts')
@login_required
def post():
    return render_template('post.html')
