from flask import render_template, url_for, flash, redirect, request
from meetup import app, db, bcrypt
from meetup.forms import RegistrationForm, LoginForm
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

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

