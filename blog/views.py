from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, current_user, logout_user
from werkzeug.security import check_password_hash

from . import app
from .database import session, Entry, User

PAGINATE_BY = 10

@app.route("/")
@app.route("/page/<int:page>")
def entries(page=1):
	# Zero-indexed page
	page_index = page - 1
	
	try:
		limit = int(request.args.get("limit", PAGINATE_BY))
	except ValueError:
		limit = PAGINATE_BY
	if limit < 1 or limit > 100:
		limit = PAGINATE_BY
	
	count = session.query(Entry).count()
	
	start = page_index * limit
	end = start + limit
	
	total_pages = (count - 1) // limit + 1
	has_next = page_index < total_pages - 1
	has_prev = page_index > 0
	has_paginator = True
	
	entries = session.query(Entry)
	entries = entries.order_by(Entry.datetime.desc())
	entries = entries[start:end]
	#TODO: clip posts so that they don't fill the screen
	
	return render_template("entries.html",
		entries=entries,
		has_next=has_next,
		has_paginator=has_paginator,
		has_prev=has_prev,
		page=page,
		total_pages=total_pages,
		limit=limit,
		current_user=current_user,
	)

@app.route("/entry/add", methods=["GET"])
@login_required
def add_entry_get():
	return render_template("add_entry.html")

@app.route("/entry/add", methods=["POST"])
@login_required
def add_entry_post():
	entry = Entry(
		title=request.form["title"],
		content=request.form["content"],
		author=current_user,
	)
	session.add(entry)
	session.commit()
	return redirect(url_for("entries"))

@app.route("/entry/<int:id>")
def single_post(id=1):
	#TODO: default to latest post instead of first one
	entries = session.query(Entry).get(id)
	#TODO: link next and previous posts a la wz2100.net
	return render_template("entries.html",
		entries=[entries]
	)

@app.route("/entry/<int:id>/edit", methods=["GET"])
@login_required
def edit_entry_get(id):
	entry = session.query(Entry).get(id)
	if entry.author_id != current_user.id:
		flash("You can only edit your own posts", "danger")
		return redirect(request.referrer or url_for("entries"))
	return render_template("edit_entry.html",
		entry=entry
	)

@app.route("/entry/<int:id>/edit", methods=["POST"])
@login_required
def edit_entry_post(id):
	entry = session.query(Entry).get(id)
	if entry.author_id != current_user.id:
		flash("You can only edit your own posts", "danger")
		return redirect(url_for("entries"))
	entry.title=request.form["title"]
	entry.content=request.form["content"]
	session.commit()
	#TODO: redirect to same post
	return redirect(url_for("entries"))

@app.route("/entry/<int:id>/delete", methods=["GET"])
@login_required
def remove_entry_get(id):
	#TODO: lock down by user or admin
	entry = session.query(Entry).get(id)
	if entry.author_id != current_user.id:
		flash("You can only delete your own posts", "danger")
		return redirect(request.referrer or url_for("entries"))
	return render_template("delete.html",
		entry=entry
	)
	
@app.route("/entry/<int:id>/delete", methods=["POST"])
@login_required
def remove_entry_delete(id):
	entry = session.query(Entry).get(id)
	if entry.author_id != current_user.id:
		flash("You can only delete your own posts", "danger")
		return redirect(url_for("entries"))
	print("Starting deletion")
	session.query(Entry).filter(Entry.id==id).delete()
	session.commit()
	return redirect(url_for("entries"))

@app.route("/login", methods=["GET"])
def login_get():
	return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_post():
	email = request.form["email"]
	password = request.form["password"]
	user = session.query(User).filter_by(email=email).first()
	if not user or not check_password_hash(user.password, password):
		flash("Incorrect username or password", "danger")
		return redirect(url_for("login_get"))
	
	login_user(user) #TODO: Create cookie warning to comply with EU regs
	return redirect(request.args.get('next') or url_for("entries"))

@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for("entries"))
