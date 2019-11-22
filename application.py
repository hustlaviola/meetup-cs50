from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect
from forms import RegistrationForm, LoginForm
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SECRET_KEY'] = '2417f062814e6d7c0b2108c9abc24109'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meetup.db'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='no-img.png')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='owner', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.posted_at}', '{self.owner_id}')"



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

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.route('/')
def index():
    return render_template('index.html', posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account created for { form.username.data }', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash(f'Account created for { form.username.data }', 'success')
        return redirect(url_for('login'))
    return render_template('login.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
