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



@app.route('/checkout')
def checkout():
    return render_template('library_checkout.html')

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
        return "Checkouts successfully added", 200
    except Exception as e:
        return f"An error occurred: {e}", 500
