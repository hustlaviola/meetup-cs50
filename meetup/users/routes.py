from flask import render_template, url_for, flash, redirect, request, abort, Blueprint
from meetup import db, bcrypt
from meetup.users.forms import (RegistrationForm, LoginForm,
                                UpdateProfileForm, RequestResetForm, ResetPaswordForm)
from meetup.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from meetup.users.utils import save_img, send_reset_email


users = Blueprint('users', __name__)


@users.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data, password=hashed)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created successfully', 'success')
        return redirect(url_for('users.login'))
    return render_template('register.html', form=form)


@users.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash(f'Invalid username/password', 'danger')
    return render_template('login.html', form=form)


@users.route('/profile', methods=['GET', 'POST'])
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
        return redirect(url_for('users.profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    img = url_for('static', filename='profile-imgs/' + current_user.image_file)
    return render_template('profile.html', img=img, form=form)


@users.route('/users/<string:username>')
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(owner=user).order_by(
        Post.posted_at.desc()).paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)


@users.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('A reset link has been sent to your email', 'info')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', form=form)


@users.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('The link has expired or invalid', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPaswordForm()
    if form.validate_on_submit():
        hashed = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user.password = hashed
        db.session.commit()
        flash(f'Password updated successfully', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset.html', form=form)


@users.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))
