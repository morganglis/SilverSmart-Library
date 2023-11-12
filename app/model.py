from app import db
from datetime import datetime

# added Ian's database code implementing the ERD.
class Patron(db.Model):
    patronID = db.Column(db.SmallInteger, primary_key=True)
    firstName = db.Column(db.String(20))
    lastName = db.Column(db.String(20))
    email = db.Column(db.String(30))
    phoneNum = db.Column(db.String(10))
    acctBalance = db.Column(db.Numeric(10, 2))
    itemsRented = db.Column(db.SmallInteger)
    date_created = db.Column(db.DateTime, default=datetime.utcnow) # I added this to track when a patron was created so we can check if expired
    checkouts = db.relationship('Checkout', backref='patron', lazy='dynamic')

class ItemType(db.Model):
    typeID = db.Column(db.Integer, primary_key=True)
    typeName = db.Column(db.String(20))
    rentDuration = db.Column(db.Integer)
    items = db.relationship('Item', backref='item_type', lazy='dynamic')

class Item(db.Model):
    itemID = db.Column(db.SmallInteger, primary_key=True)
    itemTitle = db.Column(db.String(50))
    # itemAuthor = db.Column(db.String(50)) This should come out I believe because of the many to many relationship
    publishDate = db.Column(db.Date)
    itemBranch = db.Column(db.String(50))
    typeID = db.Column(db.SmallInteger, db.ForeignKey('item_type.typeID'))
    isCheckedOut = db.Column(db.Boolean, default=False, nullable=False)  # Added attribute for item availability
    checkouts = db.relationship('Checkout', backref='item', lazy='dynamic')
    authors = db.relationship('Author', secondary='item_authors', backref=db.backref('items', lazy='dynamic'))
    isSecure = db.Column(db.Boolean, default=True, nullable=False)
    
class Checkout(db.Model):
    checkoutID = db.Column(db.Integer, primary_key=True,autoincrement = True) # this is unique for primary key
    patronID = db.Column(db.SmallInteger, db.ForeignKey('patron.patronID')) # this does not need to be primary key
    itemID = db.Column(db.SmallInteger, db.ForeignKey('item.itemID')) # this does not need to be primary key
    dueDate = db.Column(db.Date)# this needs to be due date because you can return late.
class Author(db.Model):
    authorID = db.Column(db.SmallInteger, primary_key=True)
    firstName = db.Column(db.String(20))
    lastName = db.Column(db.String(20))
class ItemAuthors(db.Model):
    __tablename__ = 'item_authors'  # Explicit table name declaration
    authorID = db.Column(db.SmallInteger, db.ForeignKey('author.authorID'), primary_key=True)
    itemID = db.Column(db.SmallInteger, db.ForeignKey('item.itemID'), primary_key=True)