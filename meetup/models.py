from datetime import datetime
from meetup import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
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
