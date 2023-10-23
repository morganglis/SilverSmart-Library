from app import app, db
from app.model import Student, Book
import datetime

with app.app_context():  #
    # Create some students
    student1 = Student(id=1000,name="John Wick", email="jwick@aol.com")
    student2 = Student(id=1001,name="Hank Hill", email="hhill@gmail.com")
    student3 = Student(id=1002,name="Penny Smith", email="psmith@hotmail.com")

    # Create some books
    book1 = Book(id=125,title="Ham and Eggs A SCRUM Love Story", author="Jeff Hams")
    book2 = Book(id=605,title="Frankenstein", author="Mary Shelly")
    book3 = Book(id=620,title="Dracula ", author="Bram Stoker")
    book4 = Book(id=652,title="Call of Cthulhu", author="H.P. Lovecraft")
    book5 = Book(id=998,title="IT", author="Stephen King")

    # Add the new objects to the session
    db.session.add(student1)
    db.session.add(student2)
    db.session.add(student3)
    db.session.add(book1)
    db.session.add(book2)
    db.session.add(book3)
    db.session.add(book4)
    db.session.add(book5)

    # Commit the session to save the objects
    db.session.commit()

    print("Database seeded!")
