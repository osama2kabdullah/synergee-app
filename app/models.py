from . import db
from sqlalchemy.dialects.sqlite import JSON

class Shop(db.Model):
    __tablename__ = "shop"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    domain = db.Column(db.String(255), unique=True, nullable=False)
    products = db.relationship('Product', backref='shop', lazy=True)


class Product(db.Model):
    __tablename__ = "product"

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    shopify_id = db.Column(db.String(100), unique=True, nullable=False)  # Shopify product ID
    variants = db.relationship('Variant', backref='product', lazy=True)


class Variant(db.Model):
    __tablename__ = "variant"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    shopify_id = db.Column(db.String(100), unique=True, nullable=False)  # Shopify variant ID
    urls = db.Column(JSON, nullable=True)  # store URLs as a JSON array
