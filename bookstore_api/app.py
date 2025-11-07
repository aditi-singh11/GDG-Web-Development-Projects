from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./books.db")

# Database setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

# SQLAlchemy model
class BookDB(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    genre = Column(String)
    price = Column(Float)

Base.metadata.create_all(bind=engine)

# Pydantic models
class BookCreate(BaseModel):
    title: str
    author: str
    genre: str
    price: float

class Book(BookCreate):
    id: int

# POST endpoint
@app.post("/books", response_model=Book)
def add_book(book: BookCreate):
    db = SessionLocal()
    new_book = BookDB(**book.dict())
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    db.close()
    return new_book

# GET endpoint with pagination
@app.get("/books", response_model=List[Book])
def get_books(skip: int = 0, limit: int = 10):
    db = SessionLocal()
    books = db.query(BookDB).offset(skip).limit(limit).all()
    db.close()
    return books

# GET by ID
@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int):
    db = SessionLocal()
    book = db.query(BookDB).filter(BookDB.id == book_id).first()
    db.close()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

# PUT endpoint
@app.put("/books/{book_id}", response_model=Book)
def update_book(book_id: int, updated_book: BookCreate):
    db = SessionLocal()
    book = db.query(BookDB).filter(BookDB.id == book_id).first()
    if not book:
        db.close()
        raise HTTPException(status_code=404, detail="Book not found")
    for key, value in updated_book.dict().items():
        setattr(book, key, value)
    db.commit()
    db.refresh(book)
    db.close()
    return book
# DELETE endpoint
@app.delete("/books/{book_id}")
def delete_book(book_id: int):
    db = SessionLocal()
    book = db.query(BookDB).filter(BookDB.id == book_id).first()
    if not book:
        db.close()
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
    db.close()
    return {"message": "Book deleted successfully"}