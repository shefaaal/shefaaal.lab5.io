
import pandas as pd  
import os 
from sqlalchemy import create_engine , text 
from sqlalchemy.orm import scoped_session,sessionmaker
file_name = pd.read_csv('books.csv')
booksdataset = pd.DataFrame(file_name)

# connecting to  database 
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
db = scoped_session(sessionmaker(bind=engine))


# data into sql 
for index , row in booksdataset.iterrows():
    db.execute({"isbn" :row["isbn"],
                "title" : row["title"],
                "author": row['author'],
                "year": row["year"]})
    db.commit()
    print("done importing")
    