from app import db
from datetime import datetime

class Patron(db.Model):
    patronID = db.Column(db.SmallInteger, primary_key=True)
    firstName = db.Column(db.String(20))
    lastName = db.Column(db.String(20))
    email = db.Column(db.String(30))
    phoneNum = db.Column(db.String(10))
    acctBalance = db.Column(db.Numeric(10, 2))
    itemsRented = db.Column(db.SmallInteger)
    checkouts = db.relationship('Checkout', backref='patron', lazy='dynamic')

class ItemType(db.Model):
    typeID = db.Column(db.SmallInteger, primary_key=True)
    typeName = db.Column(db.String(20))
    rentDuration = db.Column(db.Integer)
    items = db.relationship('Item', backref='item_type', lazy='dynamic')

class Item(db.Model):
    itemID = db.Column(db.SmallInteger, primary_key=True)
    itemTitle = db.Column(db.String(50))
    itemAuthor = db.Column(db.String(50))
    publishDate = db.Column(db.Date)
    itemBranch = db.Column(db.String(50))
    typeID = db.Column(db.SmallInteger, db.ForeignKey('item_type.typeID'))
    checkouts = db.relationship('Checkout', backref='item', lazy='dynamic')
    authors = db.relationship('Author', secondary='item_authors')

class Checkout(db.Model):
    patronID = db.Column(db.SmallInteger, db.ForeignKey('patron.patronID'), primary_key=True)
    itemID = db.Column(db.SmallInteger, db.ForeignKey('item.itemID'), primary_key=True)
    checkoutID = db.Column(db.SmallInteger, primary_key=True)
    returnDate = db.Column(db.Date)

class Author(db.Model):
    authorID = db.Column(db.SmallInteger, primary_key=True)
    firstName = db.Column(db.String(20))
    lastName = db.Column(db.String(20))

class ItemAuthors(db.Model):
    authorID = db.Column(db.SmallInteger, db.ForeignKey('author.authorID'), primary_key=True)
    itemID = db.Column(db.SmallInteger, db.ForeignKey('item.itemID'), primary_key=True)