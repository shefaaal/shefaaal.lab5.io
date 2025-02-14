import os
import flask
from flask import Flask, session , redirect ,Request ,flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash , check_password_hash
import query 

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
    return "Project 1: TODO , this is my books datat base"


@app.route("/Register" , methods = ["GET","POST"])
def regiestraion():
    if Request.access_control_request_method == 'POST':
        username = Request.form['username']
        password = Request.form['password']
        hash_pass = generate_password_hash(password)

    return("register.html")


@app.route("/Login" , methods =["GET","POST"])
def login():
     if Request.access_control_request_method == 'POST':
        username = Request.form['username']
        password = Request.form['password']
        hash_pass = generate_password_hash(password)

        return("login.html")
     

@app.route("/logout", methods = ["GET","POST"])
def logout():
    if Request.access_control_request_method == 'POST':
        username = Request.form['username']
        password = Request.form['password']
        hash_pass = generate_password_hash(password)

        return("logout.html")
     

@app.route("/book" , methods = ["GET"])
def book():
    name = Request.form.get("name")
    try: 
        flight_id = int(Request.form.get("flight"_id))
    except ValueError :
        return("this is Invalid")
    
    flight = flight.query.get(flight_id)

