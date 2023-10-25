from flask import render_template,request, redirect, url_for, flash
from app import app, db
from app.model import Student, Book, checkouts
from datetime import datetime



@app.route('/')
def library():
    # Fetch all students, books, and checkouts
    students = Student.query.all()
    books = Book.query.all()
    checkouts_data = db.session.query(checkouts).all()

    return render_template('index.html', students=students, books=books, checkouts=checkouts_data)

@app.route('/add_student', methods=['POST'])
def add_student():
    # Get the form data
    student_id = request.form.get('student_id')
    name = request.form.get('name')
    email = request.form.get('email')

    # Check if the ID already exists
    existing_student = Student.query.get(student_id)
    if existing_student:
        flash('A student with this ID already exists. Please enter a different ID.', 'error')
        return redirect(url_for('library'))

    # Create a new student with the specified ID
    new_student = Student(id=student_id, name=name, email=email)

    # Add the new student to the session and commit to the database
    try:
        db.session.add(new_student)
        db.session.commit()
        # Redirect to the home page after successful addition
        return redirect(url_for('library'))
    except Exception as e:
        # Rollback the session in case of an error and show the error message
        db.session.rollback()
        flash(f"An error occurred: {e}", 'error')
        return redirect(url_for('library'))


@app.route('/seed-db')
def seed_db():
    # Check and create Students if they don't exist
    if not Student.query.get(1000):
        student1 = Student(id=1000, name="John Wick", email="jwick@aol.com")
        db.session.add(student1)

    if not Student.query.get(1001):
        student2 = Student(id=1001, name="Hank Hill", email="hhill@gmail.com")
        db.session.add(student2)

    if not Student.query.get(1002):
        student3 = Student(id=1002, name="Penny Smith", email="psmith@hotmail.com")
        db.session.add(student3)

    # Check and create Books if they don't exist
    if not Book.query.get(125):
        book1 = Book(id=125, title="Ham and Eggs A SCRUM Love Story", author="Jeff Hams")
        db.session.add(book1)

    if not Book.query.get(605):
        book2 = Book(id=605, title="Frankenstein", author="Mary Shelly")
        db.session.add(book2)

    if not Book.query.get(620):
        book3 = Book(id=620, title="Dracula", author="Bram Stoker")
        db.session.add(book3)

    if not Book.query.get(652):
        book4 = Book(id=652, title="Call of Cthulhu", author="H.P. Lovecraft")
        db.session.add(book4)

    if not Book.query.get(998):
        book5 = Book(id=998, title="IT", author="Stephen King")
        db.session.add(book5)

    db.session.commit()  # Commit changes up to this point


    return redirect(url_for('library'))  # Assuming 'index' is a route that displays your main page

@app.route('/seed_checkouts')
def seed_checkouts():
    # Fetch students and books from the database
    student1 = Student.query.get(1000)  # Assuming the ID of the first student is 1
    student2 = Student.query.get(1001)  # Assuming the ID of the second student is 2
    book1 = Book.query.get(125)  # Assuming the ID of the first book is 1
    book2 = Book.query.get(620)  # Assuming the ID of the second book is 2

    # Check if the entities exist
    if not (student1 and student2 and book1 and book2):
        return "Error: Some entities do not exist", 400


    if book1 not in student1.books:
        student1.books.append(book1)
    if book2 not in student2.books:
        student2.books.append(book2)

    # Commit the changes to the database
    try:
        db.session.commit()
        return redirect(url_for('library'))
    except Exception as e:
        return f"An error occurred: {e}", 500