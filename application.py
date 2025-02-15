import os
import flask
from flask import Flask, session, redirect, request, flash, render_template
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    return "Shafa Books Database"

@app.route("/Register", methods=["GET", "POST"])
def registration():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hash_pass = generate_password_hash(password)
        
        # Check if the user already exists
        existing_user = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()
        if existing_user:
            flash("Username already exists. Please choose another one.")
            return redirect("/Register")
        
        # Insert new user into the database
        db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", 
                   {"username": username, "password": hash_pass})
        db.commit()

        flash("Registration successful! Please log in.")
        return redirect("/Login")

    # Render the registration page if GET request
    return render_template("register.html")

@app.route("/Login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Fe