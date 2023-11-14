from flask import render_template, request, redirect, url_for, flash, session
from app import app, db
from app.model import Patron, ItemType, Item, Checkout, Author, ItemAuthors, Branch, ItemBranch, Checkin
from datetime import datetime, timedelta
from decimal import Decimal

from flask_toastr import Toastr
toastr = Toastr(app)

app.config['TOASTR_POSITION_CLASS'] = 'toast-top-center'

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


@app.route('/about')
def about():
    return render_template('about.html')

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

@app.route('/database-overview')
def database_overview():
    patrons = Patron.query.all()
    itemTypes = ItemType.query.all()
    items = Item.query.all()
    checkouts = Checkout.query.all()
    authors = Author.query.all()
    itemAuthors = ItemAuthors.query.all()
    branches = Branch.query.all()
    itemBranches = ItemBranch.query.all()
    checkins = Checkin.query.all()

    return render_template('database_overview.html', patrons=patrons,
                           itemTypes=itemTypes, items=items,
                           checkouts=checkouts, authors=authors,
                           itemAuthors=itemAuthors, branches=branches,
                           itemBranches=itemBranches, checkins=checkins)



@app.route('/')
def library():
    # This is how we to the index page.
    return render_template('index.html')


@app.route('/privacy')
def privacy():
    return render_template('privacy_policy.html')


@app.route('/terms_use')
def terms_use():
    return render_template('terms_of_use.html')


@app.route('/accessibility')
def accessibility():
    return render_template('accessibility.html')


@app.route('/terms_pay')
def terms_pay():
    return render_template('terms_of_payment.html')


@app.route('/volunteer')
def volunteer():
    return render_template('volunteer.html')


@app.route('/donate')
def donate():
    return render_template('donate.html')


@app.route('/checkin', methods=['GET', 'POST'])
def checkin():
    if request.method == 'POST':
        item_id = request.form.get('itemID')
        is_damaged = request.form.get('isDamaged') == 'yes'

        item = Item.query.get(item_id)
        checkout = Checkout.query.filter_by(itemID=item_id).first()

        if not item.isCheckedOut:
            flash("Book is not checked out.", 'error')
            return redirect(url_for('checkin'))

        patron = Patron.query.get(checkout.patronID)
        due_date = checkout.dueDate
        today = datetime.now().date()

        if item:
            if is_damaged:
                item.itemCondition = "Damaged"
                item.isAvailable = False
                item.isCheckedOut = False
                patron.itemsRented -= 1  # decrement the number of items rented by the patron
                flash(f'Place {item_id} in damaged bin.', 'warning')
            elif item.itemBranch != 'Main':
                item.isCheckedOut = False # item is checked in
                item.isAvailable = False # item is not available because it is in transit
                item.inTransit = True  # Show that the item is in cart for transit
                patron.itemsRented -= 1  # decrement the number of items rented by the patron
                flash(f'Item {item_id} should be placed in {item.itemBranch} cart.', 'info')
            else:
                item.isCheckedOut = False
                item.isAvailable = True
                item.isSecure = True
                patron.itemsRented -= 1  # decrement the number of items rented by the patron
                flash(f'Chip detection service has been turned ON for Item {item_id}', 'info')

            fee = calculate_fees(due_date, today)
            patron.acctBalance += fee

            if fee > 0:
                flash(f'Late return fee of ${fee:.2f} added to account.', 'warning')


            # Create a new Checkin record
            new_checkin = Checkin(patronID=patron.patronID, itemID=item_id, returnDate=today)
            db.session.add(new_checkin)

            # Optional: Delete the checkout record
            # db.session.delete(checkout)

            db.session.commit()  # Commit the changes to the database

            flash(f'Item {item_id} checked in successfully.', 'success')
        else:
            flash("Item not found.", 'error')

    return render_template('library_checkin.html')


def calculate_fees(due_date, return_date):
    if return_date > due_date:
        days_past_due = (return_date - due_date).days
        return Decimal(days_past_due) * Decimal('1.00')
    return Decimal('0.00')

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'checkout_items' not in session:
        session['checkout_items'] = []

    patron = None
    is_expired = False
    checkouts = Checkout.query.all()
    authors = Author.query.all()
    items_information = Item.query.all()


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

        if is_expired:
            # Pass the is_expired to the template to show the renewal button
            return render_template('library_checkout.html', patron=patron, is_expired=is_expired)

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
            if item and not item.isCheckedOut and item.isAvailable and patron.itemsRented < 20:
                session['checkout_items'].append(item_id)
                item.isCheckedOut = True  # Mark the item as checked out
                patron.itemsRented += 1  # Increment the number of items rented by the patron
                db.session.commit()  # Commit the change to the database
                flash(f'Item {item_id} added to checkout list.', 'success')
            elif item and item.isCheckedOut:
                flash(f'Item {item_id} is already checked out.', 'error')
            elif item and not item.isAvailable:
                flash(f'Item {item_id} is in transit to other branch.', 'error')
            elif patron.itemsRented >= 20:
                flash('You cannot check out more than 20 items.', 'error')
            else:
                flash(f'Item {item_id} not found.', 'error')


        if 'remove_item' in request.form:
            item_id_to_remove = request.form.get('itemIDToRemove')
            if item_id_to_remove in session.get('checkout_items', []):
                session['checkout_items'].remove(item_id_to_remove)
                item = Item.query.get(item_id_to_remove)
                if item:
                    item.isCheckedOut = False
                    patron.itemsRented -= 1
                    db.session.commit()
                    flash(f'Item {item_id_to_remove} removed from checkout list.', 'success')
                else:
                    flash(f'Item {item_id_to_remove} not found.', 'error')
            else:
                flash(f'Item {item_id_to_remove} is not in the checkout list.', 'error')

        if 'cancel_checkout' in request.form:
            # Clear the session checkout_items
            checkout_items = session.get('checkout_items', [])

            for item_id in checkout_items:
                item = Item.query.get(item_id)
                if item:
                    item.isCheckedOut = False  # Reset the 'isCheckedOut' attribute for checked-out items
                    db.session.commit()  # Commit the change to the database

            session.pop('checkout_items', None)
            flash('Checkout canceled successfully.', 'info')
            return redirect(url_for('checkout'))


        # Confirm Checkout
        elif 'confirm_checkout' in request.form:
            checkout_items = session.get('checkout_items', [])
            due_dates = []  # Initialize due_dates list
            if checkout_items:
                # Process each item and create Checkout records
                for item_id in checkout_items:
                    item = Item.query.get(item_id)
                    if item:
                        due_date = datetime.utcnow() + timedelta(days=item.item_type.rentDuration)
                        new_checkout = Checkout(patronID=patron.patronID, itemID=item.itemID, dueDate=due_date)
                        item.isSecure = False
                        db.session.add(new_checkout)
                        due_dates.append(due_date.strftime('%Y-%m-%d'))
                db.session.commit()
                flash('Items checked out successfully.', 'success')

                # Generate receipt data
                receipt_data = []
                for item_id, due_date_str in zip(checkout_items, due_dates):
                    item = Item.query.get(item_id)
                    if item:
                        receipt_data.append({
                            'item_title': item.itemTitle,
                            'due_date': due_date_str
                        })

                # Clear the session checkout_items after a successful checkout
                session.pop('checkout_items', None)

                # Redirect to the receipt page with the necessary data
                flash(f'Chip detection service has been turned OFF for Item {item_id}', 'info')
                return render_template('receipt.html', patron=patron, receipt_data=receipt_data)
            else:
                flash('No items to checkout.', 'error')
                return redirect(url_for('checkout'))

    # For GET requests or any other redirection
    items = {item.itemID: item for item in Item.query.all()}

    item_id = request.form.get('itemId', None)
    return render_template('library_checkout.html', patron=patron, is_expired=is_expired,
                           checkout_items=session.get('checkout_items', []),
                           items=items, item_id=item_id, checkouts=checkouts, authors = authors, items_information = items_information)

def seed_database():
    # Clears out existing data and then seeds the database with data in this

    # db.session.query(Checkout).delete()
    # db.session.query(Item).delete()
    # db.session.query(ItemType).delete()
    # db.session.query(Patron).delete()
    # db.session.query(ItemAuthors).delete()
    # db.session.query(Author).delete()

    db.session.query(ItemAuthors).delete()
    db.session.query(Checkout).delete()
    db.session.query(Item).delete()
    db.session.query(ItemType).delete()
    db.session.query(Patron).delete()
    db.session.query(Author).delete()

    # Add authors
    authors = [
        Author(authorID=1, firstName='F. Scott', lastName='Fitzgerald'),
        Author(authorID=2, firstName='George', lastName='Orwell'),
        Author(authorID=3, firstName='Mary', lastName='Shelley'),
        Author(authorID=4, firstName='Bram', lastName='Stoker'),
        Author(authorID=5, firstName='H.P.', lastName='Lovecraft'),
        Author(authorID=6, firstName='Stephen', lastName='King'),
        Author(authorID=7, firstName='Jeff', lastName='Hams'),
        Author(authorID=8, firstName='J.K.', lastName='Rowling'),
        Author(authorID=9, firstName='J.R.R.', lastName='Tolkien'),
        Author(authorID=10, firstName='J.D.', lastName='Salinger'),
        Author(authorID=11, firstName='Mark', lastName='Twain'),
        Author(authorID=12, firstName='William', lastName='Shakespeare'),
        Author(authorID=13, firstName='Charles', lastName='Dickens'),
        Author(authorID=14, firstName='Jules', lastName='Verne'),
        Author(authorID=15, firstName='Agatha', lastName='Christie'),
    ]

    db.session.add_all(authors)
    db.session.commit()

    # Add item types
    item_types = [
        ItemType(typeID=1, typeName='Book', rentDuration=14),
        ItemType(typeID=2, typeName='Magazine', rentDuration=2),
        ItemType(typeID=3, typeName='Classic Movie', rentDuration=7),
        ItemType(typeID=4, typeName='New Release', rentDuration=3),
        ItemType(typeID=5, typeName='Reference', rentDuration=5),
    ]

    db.session.add_all(item_types)
    db.session.commit()

    # Add items
    items = [
        Item(itemID=1, itemTitle='The Great Gatsby', publishDate=datetime(1925, 4, 10), itemBranch='Main', typeID=1),
        Item(itemID=2, itemTitle='1984', publishDate=datetime(1949, 6, 8), itemBranch='Downtown', typeID=1),
        Item(itemID=3, itemTitle='Frankenstein', publishDate=datetime(1945, 8, 17), itemBranch='Main', typeID=1),
        Item(itemID=4, itemTitle='Dracula', publishDate=datetime(1897, 5, 26), itemBranch='Downtown', typeID=1),
        Item(itemID=5, itemTitle='Call of Cthulhu', publishDate=datetime(1928, 5, 1), itemBranch='Main', typeID=1),
        Item(itemID=6, itemTitle='IT', publishDate=datetime(1986, 9, 15), itemBranch='Downtown', typeID=1),
        Item(itemID=7, itemTitle='Ham and Eggs A SCRUM Love Story', publishDate=datetime(2020, 9, 1), itemBranch='Main', typeID=1),
        Item(itemID=8, itemTitle='Harry Potter and the Sorcerer\'s Stone', publishDate=datetime(1997, 6, 26), itemBranch='Downtown', typeID=1),
        Item(itemID=9, itemTitle='The Hobbit', publishDate=datetime(1937, 9, 21), itemBranch='Main', typeID=1),
        Item(itemID=10, itemTitle='The Catcher in the Rye', publishDate=datetime(1951, 7, 16), itemBranch='Downtown', typeID=1),
        Item(itemID=11, itemTitle='The Adventures of Tom Sawyer', publishDate=datetime(1876, 12, 1), itemBranch='Main', typeID=1),
        Item(itemID=12, itemTitle='Romeo and Juliet', publishDate=datetime(1597, 1, 1), itemBranch='Downtown', typeID=1),
        Item(itemID=13, itemTitle='A Tale of Two Cities', publishDate=datetime(1859, 4, 30), itemBranch='Main', typeID=1),
        Item(itemID=14, itemTitle='Twenty Thousand Leagues Under the Sea', publishDate=datetime(1870, 1, 1), itemBranch='Downtown', typeID=1),
        Item(itemID=15, itemTitle='Murder on the Orient Express', publishDate=datetime(1934, 2, 28), itemBranch='Main', typeID=1),
    ]

    db.session.add_all(items)
    db.session.commit()

    # Add ItemAuthors associations
    item_authors = [
        ItemAuthors(authorID=1, itemID=1),
        ItemAuthors(authorID=2, itemID=2),
        ItemAuthors(authorID=3, itemID=3),
        ItemAuthors(authorID=4, itemID=4),
        ItemAuthors(authorID=5, itemID=5),
        ItemAuthors(authorID=6, itemID=6),
        ItemAuthors(authorID=7, itemID=7),
        ItemAuthors(authorID=8, itemID=8),
        ItemAuthors(authorID=9, itemID=9),
        ItemAuthors(authorID=10, itemID=10),
        ItemAuthors(authorID=11, itemID=11),
        ItemAuthors(authorID=12, itemID=12),
        ItemAuthors(authorID=13, itemID=13),
        ItemAuthors(authorID=14, itemID=14),
        ItemAuthors(authorID=15, itemID=15),
    ]

    db.session.add_all(item_authors)
    db.session.commit()

    # Add patrons
    patrons = [
        Patron(patronID=1, firstName='John', lastName='Doe', email='john.doe@example.com', phoneNum='1234567890',
               acctBalance=15.75, itemsRented=0, date_created=datetime(2013, 5, 8)),
        Patron(patronID=2, firstName='Jane', lastName='Smith', email='jane.smith@example.com', phoneNum='0987654321',
               acctBalance=0.00, itemsRented=0, date_created=datetime(2015, 2, 24)),
        Patron(patronID=3, firstName='Jim', lastName='Johns', email='jim.johns@aol.com', phoneNum='9192012654',
               acctBalance=8.00, itemsRented=0, date_created=datetime(2020, 10, 1)),
        Patron(patronID=4, firstName='Don', lastName='Johnson', email='d.johnson@yahoo.com', phoneNum='9192022654',
               acctBalance=0.00, itemsRented=0, date_created=datetime(2019, 9, 11)),
        Patron(patronID=5, firstName='Bob', lastName='Jones', email='bob.jones@hotmail.com', phoneNum='9192032654',
               acctBalance=0.00, itemsRented=0, date_created=datetime(2016, 12, 30)),
        Patron(patronID=6, firstName='Sally', lastName='Williams', email='sally.williams@outlook.com',
               phoneNum='6192032654', acctBalance=20.25, itemsRented=0, date_created=datetime(2012, 7, 2)),
        Patron(patronID=7, firstName='Mary', lastName='Brown', email='mary.brown@live.com', phoneNum='2052032654',
               acctBalance=1.50, itemsRented=0, date_created=datetime(2018, 3, 14)),
        Patron(patronID=8, firstName='Sue', lastName='Davis', email='sue.davis@gmail.com', phoneNum='8002032654',
               acctBalance=0.00, itemsRented=0, date_created=datetime(2013, 8, 23)),
        Patron(patronID=9, firstName='Mike', lastName='Miller', email='mike.miller@netscape.net', phoneNum='6570583230',
               acctBalance=0.00, itemsRented=0, date_created=datetime(2021, 10, 6)),
        Patron(patronID=10, firstName='Bill', lastName='Wilson', email='bill.wilson@icnet.net', phoneNum='0857651273',
               acctBalance=0.00, itemsRented=0, date_created=datetime(2014, 11, 13)),
        Patron(patronID=11, firstName='Tom', lastName='Moore', email='tom.more@icloud.com', phoneNum='9865390253',
               acctBalance=12.50, itemsRented=0, date_created=datetime(2012, 6, 10)),
        Patron(patronID=12, firstName='Tim', lastName='Taylor', email='tim.taylor@mac.com', phoneNum='1237534087',
               acctBalance=0.00, itemsRented=0, date_created=datetime(2017, 4, 22)),
        Patron(patronID=13, firstName='Sam', lastName='Thomas', email='sam.thomas@me.com', phoneNum='4207203600',
               acctBalance=0.00, itemsRented=0, date_created=datetime(2022, 5, 3)),
        Patron(patronID=14, firstName='Fred', lastName='Jackson', email='fred.jackson@aol.com', phoneNum='6097203600',
               acctBalance=0.00, itemsRented=0, date_created=datetime(2015, 6, 27)),
        Patron(patronID=15, firstName='Joe', lastName='White', email='joe.white@yahoo.com', phoneNum='2345491746',
               acctBalance=0.00, itemsRented=0, date_created=datetime(2022, 7, 20)),
        Patron(patronID=16, firstName='Dave', lastName='Harris', email='dave.harris@hotmail.com', phoneNum='1560785328',
               acctBalance=35.00, itemsRented=0, date_created=datetime(2014, 12, 25)),
        Patron(patronID=17, firstName='Ed', lastName='Martin', email='ed.martin@outlook.com', phoneNum='9998652456',
               acctBalance=0.00, itemsRented=0, date_created=datetime(2019, 5, 16)),
        Patron(patronID=18, firstName='Dan', lastName='Thompson', email='dan.thompson@live.com', phoneNum='7652839434',
               acctBalance=0.00, itemsRented=0, date_created=datetime(2018, 8, 29)),
        Patron(patronID=19, firstName='Frank', lastName='Garcia', email='frank.garcia@gmail.com', phoneNum='8080064682',
               acctBalance=2.00, itemsRented=0, date_created=datetime(2017, 12, 8)),
        Patron(patronID=20, firstName='Carl', lastName='Martinez', email='carl.martinez@netscape.net',
               phoneNum='5211750349', acctBalance=0.00, itemsRented=0, date_created=datetime(2020, 9, 28)),
        Patron(patronID=21, firstName='Kim', lastName='Robinson', email='kim.robinson@icnet.net', phoneNum='5031750349',
               acctBalance=0.00, itemsRented=0, date_created=datetime(2016, 2, 16)),
        Patron(patronID=22, firstName='Ron', lastName='Clark', email='ron.clark@icloud.com', phoneNum='7077774012',
               acctBalance=0.00, itemsRented=0, date_created=datetime(2013, 1, 4)),
        Patron(patronID=23, firstName='Art', lastName='Rodriguez', email='art.rodriguez@mac.com', phoneNum='1658372398',
               acctBalance=2.25, itemsRented=0, date_created=datetime(2016, 7, 31)),
        Patron(patronID=24, firstName='Ken', lastName='Lee', email='ken.lee@me.com', phoneNum='0124126828',
               acctBalance=0.00, itemsRented=21, date_created=datetime(2023, 8, 21)),
    ]

    db.session.add_all(patrons)
    db.session.commit()

    print("Database seeded successfully!")

