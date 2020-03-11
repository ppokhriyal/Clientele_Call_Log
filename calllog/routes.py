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
from datetime import datetime
import subprocess
import re

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
		user = User(username=form.username.data, email=form.email.data, password=hashed_password,password_decrypted=form.password.data)
		db.session.add(user)
		db.session.commit()
		flash(f'Your Account has been created! You are now able to login','success')
		return redirect(url_for('login'))
	return render_template('register.html',title='Register',form=form)

TAG_RE = re.compile(r'<[^>]+>')
#Email Call Post
def send_email(author,subject,clientname,summary,call_attendies,calldate):
	
	user = User.query.filter_by(username=current_user.username).first()
	send_to = "vxlos.vxlsoftware.com"
	#send_to = user.email
	send_from = user.email
	server_mail = "mail.vxlsoftware.com"
	user_password = user.password_decrypted
	call_summary = TAG_RE.sub('',summary)
	call_attend_by = call_attendies.title()

	msg_body = f'''"Hello All,
Please find the below Call Summary of {clientname}\n
Client Name  	: {clientname}
Call Agengda    : {subject}
Call Date 	    : {calldate}
Call Attendees 	: {call_attend_by}\n
Call Summary:
{call_summary}\n
Please Check the below link for Client Summary in detail : \n http://192.168.2.240:5000\n\nThanks and Regards\n{user.username}"'''

	cmd = "/usr/bin/swaks --to "+send_to+" --from "+send_from+" --server "+server_mail+" --auth LOGIN --auth-user "+send_from+" --auth-password "+user_password+" -tls"+" --header "+"'Subject: Call Summary : '"+clientname+" --body "+msg_body
	proc = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	o = proc.communicate()
	return print(o)
	return print(cmd)

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

		#Check for Call Attendees
		if not form.call_attendies.data:
			call_attend_by = current_user.username.title()
		else:
			call_attend_by = form.call_attendies.data.title()

		callpost = CallPost(title=form.title.data,client_name=form.client_name.data,content=html_sanitized,author=current_user,client_attendies=call_attend_by,date_call=form.date_call.data)
		send_email(author=current_user,subject=form.title.data,clientname=form.client_name.data,summary=html_sanitized,call_attendies=call_attend_by,calldate=form.date_call.data.strftime('%d-%m-%Y'))
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
		html = markdown.markdown(callpost.content,extensions=['nl2br'],safe_mode=True,output_format='html5')
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
		html_sanitized = bleach.clean(bleach.linkify(html),tags=allowed_tags,attributes=allowed_attrs)
		form.title.data = callpost.title
		form.client_name.data = callpost.client_name
		form.summary.data = html_sanitized
		form.call_attendies.data = callpost.client_attendies
		form.date_call.data = callpost.date_call

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
		clientele_name = request.form['searchclient']
		page = request.args.get('page',1,type=int)
		count_search = len(db.session.query(CallPost).filter(CallPost.client_name.like(f'%{clientele_name}%')).all())
		if len(clientele_name) == 0:
			count_search = 0
			
		callposts = db.session.query(CallPost).filter(CallPost.client_name.like(f'%{clientele_name}%')).paginate(page=page,per_page=4)
		
	return render_template('search_client.html',count_search=count_search,title='Search',search_text=request.form['searchclient'].upper(),callposts=callposts)


#Logout
@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('home'))