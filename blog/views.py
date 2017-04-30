from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user
from werkzeug.security import check_password_hash

from . import app
from .database import session, Entry, User

PAGINATE_BY = 10

@app.route("/")
@app.route("/?limit=<int:limit>")
@app.route("/page/<int:page>")
@app.route("/page/<int:page>/?limit=<int:limit>")
def entries(page=1):
	# Zero-indexed page
	page_index = page - 1
	
	count = session.query(Entry).count()
	
	start = page_index * PAGINATE_BY
	end = start + PAGINATE_BY
	
	total_pages = (count - 1) // PAGINATE_BY + 1
	has_next = page_index < total_pages - 1
	has_prev = page_index > 0
	
	entries = session.query(Entry)
	entries = entries.order_by(Entry.datetime.desc())
	entries = entries[start:end]
	#TODO: clip posts so that they don't fill the screen
	
	return render_template("entries.html",
		entries=entries,
		has_next=has_next,
		has_prev=has_prev,
		page=page,
		total_pages=total_pages
	)

@app.route("/entry/add", methods=["GET"])
def add_entry_get():
	return render_template("add_entry.html")

@app.route("/entry/add", methods=["POST"])
def add_entry_post():
	entry = Entry(
		title=request.form["title"],
		content=request.form["content"],
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
def edit_entry_get(id):
	entry = session.query(Entry).get(id)
	return render_template("edit_entry.html",
		entry=entry
	)

@app.route("/entry/<int:id>/edit", methods=["POST"])
def edit_entry_post(id):
	entry = session.query(Entry).get(id)
	entry.title=request.form["title"]
	entry.content=request.form["content"]
	session.commit()
	#TODO: redirect to same post
	return redirect(url_for("entries"))

@app.route("/entry/<int:id>/delete", methods=["GET"])
def remove_entry_get(id):
	entry = session.query(Entry).get(id)
	return render_template("delete.html",
		entry=entry
	)
	
@app.route("/entry/<int:id>/delete", methods=["POST"])
def remove_entry_delete(id):
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
