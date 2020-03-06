from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from calllog import db, login_manager, app
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
        return User.query.get(int(user_id))


class User(db.Model,UserMixin):
	id = db.Column(db.Integer,primary_key=True)
	username = db.Column(db.String(20),unique=True,nullable=False)
	email = db.Column(db.String(120),unique=True,nullable=False)
	password = db.Column(db.String(60),nullable=False)
	password_decrypted = db.Column(db.String(60),nullable=False)
	callposts = db.relationship('CallPost',backref='author',lazy=True,cascade='all,delete-orphan')

	def __repr__(self):
		return f"User('{self.username}','{self.password}')"

class CallPost(db.Model):
	id = db.Column(db.Integer,primary_key=True)
	title = db.Column(db.String(100),nullable=False)
	date_posted = db.Column(db.DateTime(),nullable=False,default=datetime.utcnow)
	date_call = db.Column(db.DateTime(),nullable=False,default=datetime.utcnow)
	client_name = db.Column(db.String(100),nullable=False)
	client_attendies = db.Column(db.String(500))
	content = db.Column(db.Text,nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

	def __repr__(self):

		return f"CallPost('{self.title}','{self.date_posted}','{self.client_name}','{self.client_attendies}')"
