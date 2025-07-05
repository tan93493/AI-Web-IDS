# order_site/routes.py
from flask import render_template, request, session, jsonify, redirect, url_for
from . import order_bp
from extensions import db
from models import Product, Order, OrderItem, User, CheckOut
from forms import CheckoutForm

def get_cart_data():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            return [], Order()
        order = Order.query.filter_by(user_id=user.id, status='pending').first()
        if order is None:
            order = Order(user_id=user.id, status='pending')
        items = order.items
        return items, order
    return [], Order()

@order_bp.route('/cart')
def cart():
    items, order = get_cart_data()
    return render_template('cart.html', items=items, order=order, cartItems=order.get_cart_items)

@order_bp.route('/update_item/', methods=['POST'])
def update_item():
    data = request.get_json()
    product_id = data.get('productId')
    action = data.get('action')
    if 'username' not in session:
        return jsonify({'error': 'Vui lòng đăng nhập để mua hàng'}), 401
    user = User.query.filter_by(username=session['username']).first()
    product = Product.query.get(product_id)
    if not user or not product:
        return jsonify({'error': 'Người dùng hoặc sản phẩm không hợp lệ'}), 404
    order = Order.query.filter_by(user_id=user.id, status='pending').first()
    if order is None and action == 'add':
        order = Order(user_id=user.id, status='pending')
        db.session.add(order)
        db.session.flush() 
    if order is None:
        return jsonify({'error': 'Giỏ hàng không tồn tại'}), 404
    order_item = OrderItem.query.filter_by(order_id=order.id, product_id=product.id).first()
    if action == 'add':
        if order_item:
            order_item.quantity += 1
        else:
            order_item = OrderItem(order_id=order.id, product_id=product.id, quantity=1)
            db.session.add(order_item)
    elif action == 'remove':
        if order_item:
            order_item.quantity -= 1
            if order_item.quantity <= 0:
                db.session.delete(order_item)
    db.session.flush() 
    if order and not order.items:
        print(f"Đơn hàng {order.id} rỗng, đang xóa...")
        db.session.delete(order)
    db.session.commit()
    cart_items_count = order.get_cart_items if order and db.session.object_session(order) else 0
    return jsonify({'message': 'Giỏ hàng đã được cập nhật!', 'cart_total_items': cart_items_count})

@order_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    form = CheckoutForm()
    items, order = get_cart_data()
    if not items:
        return redirect(url_for('orders.cart'))
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return redirect(url_for('main.home'))
    if form.validate_on_submit():
        order_to_process = Order.query.filter_by(user_id=user.id, status='pending').first()
        if not order_to_process:
            return redirect(url_for('order.cart'))
        new_checkout_info = CheckOut(
            name=form.name.data,
            address=form.address.data,
            phone=form.phone.data,
            note=form.note.data,
            user_id=user.id
        )
        order_to_process.status = 'processing'
        order_to_process.checkout_info = new_checkout_info
        try:
            db.session.commit()
            return redirect(url_for('main.home'))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for('order.checkout'))
    return render_template('checkout.html', items=items, order=order, form=form)

@order_bp.route('/my-orders')
def my_orders():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    user = User.query.filter_by(username=session['username']).first_or_404()
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.date_ordered.desc()).all()
    return render_template('myorders.html', orders=orders)