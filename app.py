import os
import flask
from flask import Flask, session, redirect, request, flash, render_template
from flask_session import Session
from sqlalchemy import create_engine, text
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
    return render_template("index.html")

@app.route("/Register", methods=["GET", "POST"])
def registration():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hash_pass = generate_password_hash(password)
        

        existing_user = db.execute(text("SELECT * FROM users WHERE username = :username"), {"username": username}).fetchone()
        if existing_user:
            flash("Username already exists. Please choose another one.")
            return redirect("/Register")
        
        db.execute(text("INSERT INTO users (username, password) VALUES (:username, :password)"), 
                   {"username": username, "password": hash_pass})
        db.commit()

        flash("Registration successful! Please log in.")
        return redirect("/Login")


    return render_template("register.html")

@app.route("/Login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = db.execute(text("SELECT * FROM users WHERE username = :username"), {"username": username}).mappings().fetchone()
        
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            flash("Login successful!")
            return redirect("/")
        
        flash("Invalid username or password")
        return redirect("/Login")
    
    
    return render_template("login.html")

@app.route("/logout", methods=["POST"])
def logout():
        session.pop("user_id", None)  
        flash("Logged out!")
        return redirect("/")



@app.route("/search", methods=["GET", "POST"])
def search():
    if "user_id" not in session:
        flash("You need to log in first!")
        return redirect("/Login")
    
    if request.method == 'POST':
        search_term = request.form['search_term']
        search_results = db.execute(text("""
            SELECT * FROM books
            WHERE isbn LIKE :search_term OR title LIKE :search_term OR author LIKE :search_term
            """), {"search_term": "%" + search_term + "%"}).fetchall()
        
        if search_results:
            return render_template("search.html", books=search_results, search_term=search_term)
        else:
            flash(f"No results found for '{search_term}'")
            return render_template("search.html", search_term=search_term)
    
    return render_template("search.html")



@app.route("/book/<int:book_id>")
def book_page(book_id):
    book = db.execute(text("SELECT * FROM books WHERE id = :id"), {"id": book_id}).fetchone()
    reviews = db.execute(text("SELECT * FROM reviews WHERE book_id = :book_id"), {"book_id": book_id}).fetchall()
    
    # Debugging output
    print("Book:", book)
    print("Reviews:", reviews)
    
    if book:
        return render_template("book_page.html", book=book, reviews=reviews)
    else:
        flash("Book not found.")
        return redirect("/search")

@app.route("/book/<int:book_id>/review", methods=["POST"])
def leave_review(book_id):
    if "user_id" not in session:
        flash("You need to log in first!")
        return redirect("/Login")
    
    review_text = request.form.get('review_text')
    
    if review_text:
        db.execute(text("""
            INSERT INTO reviews (book_id, user_id, text) 
            VALUES (:book_id, :user_id, :review_text)
        """), {"book_id": book_id, "user_id": session["user_id"], "review_text": review_text})
        db.commit()
        
        flash("Review added successfully!")
        return redirect(f"/book/{book_id}")
    
    flash("Review cannot be empty!")
    return redirect(f"/book/{book_id}")

if __name__ == "__main__":
    app.run(debug=True)

