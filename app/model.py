from app import db
from datetime import datetime

checkouts = db.Table('checkouts',
                     db.Column('student_id', db.Integer, db.ForeignKey('student.id'), primary_key=True),
                     db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
                     db.Column('checkout_date', db.DateTime, default=datetime.utcnow)
                     )


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    # Show a many to many
    books = db.relationship('Book', secondary=checkouts, lazy='subquery',
                            backref=db.backref('students', lazy=True))


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100))
