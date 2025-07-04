# main_site/routes.py
from flask import render_template, request
from . import main_bp
from extensions import db
from models import Product, Category
from order_site.routes import get_cart_data

@main_bp.route('/')
def home():
    products = Product.query.all()
    _, order = get_cart_data()
    return render_template('home.html', products=products, cartItems=order.get_cart_items)

@main_bp.route('/search', methods=['GET', 'POST'])
def search():
    products = []
    query = ""
    if request.method == 'POST':
        query = request.form.get('query', "")
        if query:
            search_term = f"%{query}%"
            products = Product.query.filter(Product.name.ilike(search_term)).all()
    return render_template('search.html', products=products, query=query)

@main_bp.route('/category/')
@main_bp.route('/category/<slug>')
def category(slug=None):
    _, order = get_cart_data()
    if slug:
        category_obj = Category.query.filter_by(slug=slug).first_or_404()
        products = category_obj.products
        active_category_name = category_obj.name
    else:
        products = Product.query.all()
        active_category_name = "Tất cả sản phẩm"
    return render_template('category.html', products=products, active_category=active_category_name, cartItems=order.get_cart_items)

@main_bp.route('/product/<int:product_id>')
def detail(product_id):
    product = Product.query.get_or_404(product_id)
    _, order = get_cart_data()
    return render_template('detail.html', product=product, cartItems=order.get_cart_items)