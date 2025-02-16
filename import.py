
import pandas as pd  
import os 
from sqlalchemy import Column, Integer, String, create_engine , text ,MetaData,Table
from sqlalchemy.orm import scoped_session,sessionmaker

# read the file  
file_name = 'books.csv'
booksdataset = pd.read_csv(file_name)

# connecting to  database 
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
db = scoped_session(sessionmaker(bind=engine))


# making a table 
metadata = MetaData()
books = Table('books', metadata,
    Column('id', Integer, primary_key=True),
    Column('isbn', String(13), nullable=False),
    Column('title', String, nullable=False),
    Column('author', String, nullable=False),
    Column('year', Integer)
)
metadata.create_all(engine) 


# data into sql 
for index , row in booksdataset.iterro