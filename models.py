from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()



class Product(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(100), nullable=False)
    prices= db.relationship("Price", backref="product")
    search_term= db.Column(db.String(100))
    def __repr__(self) -> str:
        return f"Product {self.id}: {self.name}"

class Store(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    chain=db.Column(db.String(50))
    locationid=db.Column(db.Integer, nullable=False)
    city=db.Column(db.String(50), nullable=False)
    prices = db.relationship("Price", backref="store")

class Price(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer,db.ForeignKey("product.id"))
    store_id=db.Column(db.Integer,db.ForeignKey("store.id"))
    price=db.Column(db.Numeric(10,2), nullable=False)
    size=db.Column(db.String(50))
    u_o_m=db.Column(db.String(50))

class Users(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(50), unique=True, nullable=False)
    email=db.Column(db.String(50), unique=True, nullable=False)
    password_hash=db.Column(db.String(255))
    admin=db.Column(db.Boolean, default=False)


    @property
    def password(self):
        raise AttributeError("Passwords are not a readable attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def password_check(self, password):
        return check_password_hash(self.password_hash, password)

class Alerts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey("store.id"), nullable=False)
    target_price = db.Column(db.Numeric(10,2), nullable=False)
    active = db.Column(db.Boolean, default=False)
    product = db.relationship("Product", backref="alerts")
    store = db.relationship("Store", backref="alerts")
    email = db.Column(db.String(50), nullable=False)
    user = db.relationship("Users", backref="alerts")