import pandas as pd
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.orm import scoped_session, sessionmaker

# File and database connection setup
file_name = 'books.csv'
booksdataset = pd.read_csv(file_name)
DATABASE_URL = "postgresql://shafa:301156@localhost/shafabooks"
engine = create_engine(DATABASE_URL)
db = scoped_session(sessionmaker(bind=engine))

# Define metadata and tables
metadata = MetaData()
books = Table('books', metadata,
    Column('id', Integer, primary_key=True),
    Column('isbn', String(13), nullable=False, unique=True),
    Column('title', String, nullable=False),
    Column('author', String, nullable=False),
    Column('year', Integer)
)

reviews = Table('reviews', metadata,
    Column('id', Integer, primary_key=True),
    Column('book_id', Integer, nullable=False),
    Column('user_id', Integer, nullable=False),
    Column('review', String, nullable=False),
    UniqueConstraint('book_id', 'user_id', name='unique_review')
)

metadata.create_all(engine)

# Insert books data into the database
for index, row in booksdataset.iterrows():
    # Prepare the book data
    isbn = row['isbn']
    title = row['title']
    author = row['author']
    year = row['year']

    # Check if the book already exists based on the ISBN
    existing_book = db.execute(text("SELECT * FROM books WHERE isbn = :isbn"), {"isbn": isbn}).fetchone()

    if existing_book:
        print(f"Book with ISBN {isbn} already exists.")
    else:
        # Insert the new book into the database
        db.execute(text("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)"),
                   {"isbn": isbn, "title": title, "author": author, "year": year})
        print(f"Inserted book: {title} (ISBN: {isbn})")

# Commit the transaction
db.commit()
print("Done importing")
