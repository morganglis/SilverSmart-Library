from flask import render_template, request, redirect, url_for, flash, session
from app import app, db
from app.model import Patron, ItemType, Item, Checkout, Author, ItemAuthors  # import the tables you need to access
from datetime import datetime, timedelta
from decimal import Decimal


@app.route('/seed_db', methods=['POST'])
def seed_db_route():
    seed_database()
    # Flash a success message
    flash('Database seeded successfully!', 'success')
    # Redirect to the 'library' route after seeding the database
    return redirect(url_for('library'))


@app.route('/database-summary')
# This is just a quick query to show the contents of the database and display it.
# This is not part of the project. Just to help with debugging.
def database_summary():
    patrons = Patron.query.all()
    item_types = ItemType.query.all()
    items = Item.query.all()
    authors = Author.query.all()
    checkouts = Checkout.query.all()

    return render_template('database_summary.html', patrons=patrons, item_types=item_types, items=items,
                           authors=authors, checkouts=checkouts)


@app.route('/add_patron')
def add_patron():
    # Display a form to add a new patron
    return render_template('add_patron.html')


@app.route('/create_patron', methods=['POST'])
def create_patron():
    # Get data from form submission to create a new Patron
    patronID = request.form['patronID']
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    email = request.form['email']
    phoneNum = request.form['phoneNum']
    # Create a new Patron instance
    new_patron = Patron(patronID=patronID, firstName=firstName, lastName=lastName, email=email, phoneNum=phoneNum,
                        acctBalance=0.00,
                        itemsRented=0)
    db.session.add(new_patron)
    db.session.commit()

    flash('New patron added successfully!')
    return redirect(url_for('checkout'))


@app.route('/')
def library():
    # This is how we to the index page.
    return render_template('index.html')


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'checkout_items' not in session:
        session['checkout_items'] = []

    patron = None
    is_expired = False

    if request.method == 'POST':
        patron_id = request.form.get('patronID')
        patron = Patron.query.get(patron_id)

        if not patron:
            flash('No patron found with this ID.', 'error')
            return redirect(url_for('checkout'))

        # Calculate if the patron's ID is expired
        is_expired = datetime.utcnow() > (patron.date_created + timedelta(days=2 * 365))

        # Renew Patron ID
        if 'renew' in request.form:
            patron.date_created = datetime.utcnow()
            db.session.commit()
            flash('Patron ID has been renewed.', 'success')
            is_expired = False  # Update the expiration status after renewal

        # If the card is expired and not being renewed, inform the user and prevent further actions
        if is_expired:
            flash('Your card has expired. Please renew your card.', 'error')
            return redirect(url_for('checkout'))

        # Check if the patron has already checked out the maximum number of items
        if patron.itemsRented >= 20:
            flash('You have reached the maximum number of items allowed to be checked out.', 'error')
            return redirect(url_for('checkout'))

        # Handle Payment
        elif 'payment' in request.form:
            payment_amount = request.form['payment']
            try:
                payment = Decimal(payment_amount)
                if payment > 0 and payment <= patron.acctBalance:
                    patron.acctBalance -= payment
                    db.session.commit()
                    flash(f'Payment of ${payment:.2f} received. New balance: ${patron.acctBalance:.2f}', 'success')
                else:
                    flash('Invalid payment amount.', 'error')
            except ValueError:
                flash('Invalid payment amount entered.', 'error')

        # Add Item to Checkout List
        elif 'add_item' in request.form:
            item_id = request.form.get('itemId')
            item = Item.query.get(item_id)
            if item and not item.isCheckedOut and patron.itemsRented < 20:
                session['checkout_items'].append(item_id)
                item.isCheckedOut = True  # Mark the item as checked out
                patron.itemsRented += 1  # Increment the number of items rented by the patron
                db.session.commit()  # Commit the change to the database
                flash(f'Item {item_id} added to checkout list.', 'success')
            elif item and item.isCheckedOut:
                flash(f'Item {item_id} is already checked out.', 'error')
            elif patron.itemsRented >= 20:
                flash('You cannot check out more than 20 items.', 'error')
            else:
                flash(f'Item {item_id} not found.', 'error')

        # Confirm Checkout
        elif 'confirm_checkout' in request.form:
            checkout_items = session.get('checkout_items', [])
            if checkout_items:
                due_dates = []
                # Process each item and create Checkout records
                for item_id in checkout_items:
                    item = Item.query.get(item_id)
                    if item:
                        due_date = datetime.utcnow() + timedelta(days=item.item_type.rentDuration)
                        new_checkout = Checkout(patronID=patron.patronID, itemID=item.itemID, dueDate=due_date)
                        db.session.add(new_checkout)
                        due_dates.append(due_date.strftime('%Y-%m-%d'))
                db.session.commit()
                flash('Items checked out successfully.', 'success')

                # Clear the session checkout_items after successful checkout
                session.pop('checkout_items', None)

                # Generate receipt data
                receipt_data = []
                for item_id, due_date_str in zip(checkout_items, due_dates):
                    item = Item.query.get(item_id)
                    if item:
                        receipt_data.append({
                            'item_title': item.itemTitle,
                            'due_date': due_date_str
                        })

                # Redirect to the receipt page with the necessary data
                return render_template('receipt.html', patron=patron, receipt_data=receipt_data)
            else:
                flash('No items to checkout.', 'error')

    # For GET requests or any other redirection
    items = {item.itemID: item for item in Item.query.all()}
    return render_template('library_checkout.html', patron=patron, is_expired=is_expired,
                           checkout_items=session.get('checkout_items', []),
                           items=items)

def seed_database():
    # Clears out existing data and then seeds the database with data in this

    db.session.query(Checkout).delete()
    db.session.query(ItemAuthors).delete()
    db.session.query(Author).delete()
    db.session.query(Item).delete()
    db.session.query(ItemType).delete()
    db.session.query(Patron).delete()

    # Add authors
    authors = [
        Author(authorID=1, firstName='F. Scott', lastName='Fitzgerald'),
        Author(authorID=2, firstName='George', lastName='Orwell'),

    ]

    # Add item types
    item_types = [
        ItemType(typeID=1, typeName='Book', rentDuration=14),
        ItemType(typeID=2, typeName='DVD', rentDuration=7),

    ]

    # Add items
    items = [
        Item(itemID=1, itemTitle='The Great Gatsby', publishDate=datetime(1925, 4, 10), itemBranch='Main', typeID=1),
        Item(itemID=2, itemTitle='1984', publishDate=datetime(1949, 6, 8), itemBranch='Downtown', typeID=1),

    ]

    # Add ItemAuthors associations
    item_authors = [
        ItemAuthors(authorID=1, itemID=1),
        ItemAuthors(authorID=2, itemID=2),

    ]

    # Add patrons
    patrons = [
        Patron(patronID=1, firstName='John', lastName='Doe', email='john.doe@example.com', phoneNum='1234567890',
               acctBalance=15.75, itemsRented=2, date_created=datetime(2023, 10, 1)),
        Patron(patronID=2, firstName='Jane', lastName='Smith', email='jane.smith@example.com', phoneNum='0987654321',
               acctBalance=0.00, itemsRented=5, date_created=datetime(2023, 10, 1)),
        Patron(patronID=3, firstName='Jim', lastName='Johns', email='jim.johns@aol.com', phoneNum='9192012654',
               acctBalance=0.00, itemsRented=5, date_created=datetime(2020, 10, 1)),
        Patron(patronID=4, firstName='Don', lastName='Johnson', email='d.johnson@yahoo.com', phoneNum='9192022654',
               acctBalance=0.00, itemsRented=21, date_created=datetime(2023, 10, 1)),
    ]

    # Add all to session
    db.session.add_all(authors + item_types + items + patrons + item_authors)

    # Commit the session
    db.session.commit()

    print("Database seeded successfully!")

