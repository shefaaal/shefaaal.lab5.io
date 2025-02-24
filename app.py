import os
import flask
from flask import jsonify
from flask import Flask, session, redirect, request, flash, render_template
from flask_session import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import google.generativeai as genai 






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

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))



def get_google(isbn):
    link = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}'
    response = requests.get(link)

    if response.status_code == 200:
        data = response.json()
        if "items" in data:
            book_info = data["items"][0]["volumeInfo"]
            average_rating = book_info.get("averageRating", None)
            ratings_count = book_info.get("ratingsCount", None)
            description = book_info.get("description", "No description available.")
            return average_rating, ratings_count, description
    return None, None, "No description available."



def get_gemini_summary(description):
    if not description or description == "No description available.":
        return "No summary available."
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(f"Summarize this book description in less than 50 words: {description}")
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API error: {e}")
        return "Summary not available due to an API error."

@app.route('/book/<isbn>', methods=['GET', 'POST'])
def book_detail(isbn):
    #  database 
    book = db.execute(text("SELECT * FROM books WHERE isbn = :isbn"), {"isbn": isbn}).fetchone()

    
    if book:
        # google books
        google_data = get_google(isbn)

        
        book_data = {
            'isbn': book['isbn'],
            'title': book['title'],
            'author': book['author'],
            'year': book['year'],
            'average_rating': google_data[0] if google_data[0] else 'No rating available',
            'ratings_count': google_data[1] if google_data[1] else 'No ratings available',
            'description': google_data[2] if google_data[2] else 'No description available'
        }
    else:
        #  book is not found 
        book_data = {
            'isbn': isbn,
            'title': 'Book not found',
            'author': 'Unknown',
            'year': 'N/A',
            'average_rating': 'No rating available',
            'ratings_count': 'No ratings available',
            'description': 'No description available'
        }
        google_data = (None, None, "No description available")  
        flash("Book not found in the database", "error")

    
    print(f"Book data to render: {book_data}")

    
    if request.method == 'POST':
        if 'user_id' in session:
            review_text = request.form.get('review')
            rating = request.form.get('rating')
            user_id = session['user_id']

            #  user has already reviewed this book
            existing_review = db.execute(text("""
                SELECT * FROM reviews WHERE user_id = :user_id AND book_id = (SELECT id FROM books WHERE isbn = :isbn)
            """), {'user_id': user_id, 'isbn': isbn}).fetchone()

            if existing_review:
                flash("You have already reviewed this book.", "error")
            else:
                # review into the database
                db.execute(text("""
                    INSERT INTO reviews (user_id, book_id, review, rating)
                    VALUES (:user_id, (SELECT id FROM books WHERE isbn = :isbn), :review_text, :rating)
                """), {'user_id': user_id, 'isbn': isbn, 'review_text': review_text, 'rating': rating})
                db.commit()
                flash("Review submitted successfully!", "success")
        else:
            flash("You need to log in to submit a review.", "error")

    # reviews from the database for the given book
    reviews_query = text("""
        SELECT * FROM reviews WHERE book_id = (SELECT id FROM books WHERE isbn = :isbn)
    """)
    reviews = db.execute(reviews_query, {'isbn': isbn}).fetchall()

    return render_template(
        'book_page.html',
        book_data=book_data,
        google_data={'average_rating': book_data['average_rating'], 'ratings_count': book_data['ratings_count'], 'description': book_data['description']},
        reviews=reviews
    )

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




@app.route("/book/<int:book_id>/review", methods=["POST"])
def leave_review(book_id):
    
    if "user_id" not in session:
        flash("You need to log in first!")
        return redirect("/Login")

    
    review_text = request.form.get('review')
    rating = request.form.get('rating')  
    
   
    if not review_text:
        flash("Review cannot be empty!")
        return redirect(f"/book/{book_id}")
    
  
    if not rating:
        flash("Please select a rating!")
        return redirect(f"/book/{book_id}")

    
    user_id = session["user_id"]

    try:
        
        db.execute(text("""INSERT INTO reviews (book_id, user_id, review, rating) 
                           VALUES (:book_id, :user_id, :review_text, :rating)"""),
                   {"book_id": book_id, "user_id": user_id, "review_text": review_text, "rating": rating})
        db.commit()

        
        existing_review = db.execute(text("""
            SELECT * FROM reviews WHERE book_id = :book_id AND user_id = :user_id
        """), {"book_id": book_id, "user_id": user_id}).fetchone()

        
        if existing_review:
            db.execute(text("""
                DELETE FROM reviews WHERE book_id = :book_id AND user_id = :user_id AND review != :review_text
            """), {"book_id": book_id, "user_id": user_id, "review_text": review_text})
            db.commit()

        flash("Review added!")
    except Exception as e:
        db.rollback()
        flash(f"An error occurred while adding your review: {e}")
    
    return redirect(f"/book/{book_id}")



if __name__ == "__main__":
    app.run(debug=True)

