import os
import markdown
import bleach
from bleach.sanitizer import Cleaner
import secrets
from flask import render_template, url_for, flash, redirect, request, abort, session, jsonify
from calllog import app, db, bcrypt, login_manager, mde
from calllog.forms import LoginForm, RegistrationForm, CallLogSummary
from calllog.models import User,CallPost
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import func

#Home Page
@app.route('/')
def home():
	page = request.args.get('page',1,type=int)
	callposts = CallPost.query.order_by(CallPost.date_posted.desc()).paginate(page=page,per_page=4)
	len_callpost = len(CallPost.query.all())
	return render_template('home.html',title='Home',len_callpost=len_callpost,callposts=callposts)

#Login Page
@app.route('/login',methods=['GET','POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password,form.password.data):
			login_user(user)
			next_page = request.args.get('next')
			return redirect(next_page) if next_page else redirect(url_for('home'))
		else:
			flash('Login Unsuccessful. Please check email or password','danger')
	return render_template('login.html',title='Login',form=form)

#Register Page
@app.route('/register',methods=['GET','POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))

	form = RegistrationForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user = User(username=form.username.data, email=form.email.data, password=hashed_password)
		db.session.add(user)
		db.session.commit()
		flash(f'Your Account has been created! You are now able to login','success')
		return redirect(url_for('login'))
	return render_template('register.html',title='Register',form=form)

#Add Call Log Summary
@app.route('/addcalllog/new',methods=['GET','POST'])
@login_required
def addcall():
	form = CallLogSummary()
	if form.validate_on_submit():

		session['content'] = request.form['summary']
		html = markdown.markdown(request.form['summary'],extensions=['nl2br'],safe_mode=True,output_format='html5')
		#Tags
		allowed_tags = [
		'a','abbr','acronym','b','blockquote','code',
		'em','i','li','ol','pre','strong','ul','img',
		'h1','h2','h3','p','br'
		]
		#Attributes
		allowed_attrs = {
		'*':['class'],
		'a':['href','rel'],
		'img':['src','alt']
		}
		#Sanitize HTML
		html_sanitized = bleach.clean(
			bleach.linkify(html),
			tags=allowed_tags,
			attributes=allowed_attrs
			)

		callpost = CallPost(title=form.title.data,client_name=form.client_name.data,content=html_sanitized,author=current_user,client_attendies=form.call_attendies.data)
		db.session.add(callpost)
		db.session.commit()
		flash('Call Summary Created !','success')
		return redirect(url_for('home'))

	return render_template('addcall.html',title='Add Call Summary',form=form,legend_title='Add Clientele Call Summary')

#Edit Call Post
@app.route('/callpost/<int:callpost_id>')
def edit_callpost(callpost_id):
	callpost = CallPost.query.get_or_404(callpost_id)
	return render_template('editcall.html',title=callpost.title,callpost=callpost)

#Update Call Post
@app.route('/callpost/<int:callpost_id>/update',methods=['GET','POST'])
@login_required
def update_callpost(callpost_id):
	callpost = CallPost.query.get_or_404(callpost_id)

	if callpost.author != current_user:
		abort(403)
	form = CallLogSummary()

	if form.validate_on_submit():
		callpost.title = form.title.data
		html = markdown.markdown(request.form['summary'],extensions=['nl2br'],safe_mode=True,output_format='html5')
		#Tags
		allowed_tags = [
		'a','abbr','acronym','b','blockquote','code',
		'em','i','li','ol','pre','strong','ul','img',
		'h1','h2','h3','p','br'
		]
		#Attributes
		allowed_attrs = {
		'*':['class'],
		'a':['href','rel'],
		'img':['src','alt']
		}
		#Sanitize HTML
		html_sanitized = bleach.clean(
			bleach.linkify(html),
			tags=allowed_tags,
			attributes=allowed_attrs
			)
		callpost.content = html_sanitized
		callpost.client_name = form.client_name.data

		db.session.commit()
		flash('Clientele Call Summary Updated !','success')
		return redirect(url_for('home'))
	elif request.method == 'GET':
		
		form.title.data = callpost.title
		form.client_name.data = callpost.client_name
		form.summary.data = callpost.content
		form.call_attendies.data = callpost.client_attendies

	return render_template('addcall.html',title='Update Call Summary',form=form,legend_title='Update Clientele Call Summary')

#Delete Call Post
@app.route('/delete_callpost/<int:callpost_id>/delete',methods=['POST'])
@login_required
def del_callpost(callpost_id):

	callpost = CallPost.query.get_or_404(callpost_id)

	if callpost.author != current_user:
		abort(403)
	db.session.delete(callpost)
	db.session.commit()

	flash('Call Summary has been deleted!','success')
	
	return redirect(url_for('home'))


#Search Client Post
@app.route('/search',methods=['GET','POST'])
def search():
	
	return render_template('search.html',title='Search')

#Check Search Result
@app.route('/search_client',methods=['POST','GET'])
def check_search():

	if request.method == "POST":
		page = request.args.get('page',1,type=int)
		count_search = db.session.query(CallPost).filter(func.lower(CallPost.client_name) == func.lower(request.form['searchclient'])).count()
		callposts = db.session.query(CallPost).filter(func.lower(CallPost.client_name) == func.lower(request.form['searchclient'])).paginate(page=page,per_page=4)

	return render_template('search_client.html',count_search=count_search,title='Search',search_text=request.form['searchclient'].upper(),callposts=callposts)


#Logout
@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('home'))