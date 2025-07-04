# models.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
import secrets

product_categories = db.Table('product_categories',
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    is_admin = db.Column(db.Boolean, default=False)
    
    orders = db.relationship('Order', backref='customer', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), index=True)
    parent = db.relationship('Category', remote_side=[id], backref='sub_categories')

    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200)) 
    detail = db.Column(db.Text)
    stock = db.Column(db.Integer, default=0) 
    is_available = db.Column(db.Boolean, default=True)
    date_added = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    categories = db.relationship('Category', secondary=product_categories,
                                 lazy='subquery', backref=db.backref('products', lazy=True))

    def __repr__(self):
        return f'<Product {self.name}>'

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    status = db.Column(db.String(50), default='pending', nullable=False)
    date_ordered = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)
    transaction_id = db.Column(db.String(100), unique=True, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")
    checkout_info = db.relationship('CheckOut', backref='order', uselist=False, cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.order_number is None:
            self.generate_order_number()

    def generate_order_number(self):
        date_str = datetime.datetime.now().strftime('%Y%m%d')
        random_str = secrets.token_hex(2).upper()
        self.order_number = f"ORD-{date_str}-{random_str}"

    @property
    def get_cart_total(self):
        return sum(item.get_total for item in self.items)

    @property
    def get_cart_items(self):
        return sum(item.quantity for item in self.items)
    
    def __repr__(self):
        return f'<Order {self.order_number}>'

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    
    product = db.relationship('Product')

    @property
    def get_total(self):
        if self.product:
            return self.product.price * self.quantity
        return 0

class CheckOut(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250))
    address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    note = db.Column(db.String(250))

    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __repr__(self):
        return f'<CheckOut for Order ID: {self.order_id}>'

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True), server_default=func.now())
    ip = db.Column(db.String(45))
    method = db.Column(db.String(10))
    path = db.Column(db.String(200))
    
    def __repr__(self):
        return f'<Log from {self.ip} at {self.timestamp}>'
