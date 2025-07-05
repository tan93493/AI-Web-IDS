# app.py
from flask import Flask, request
import datetime
from extensions import db, migrate, csrf
from models import User, Product, Category, Order, OrderItem, CheckOut, Log
from main_site.routes import get_cart_data
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from admin_site.views import ProductAdminView, OrderAdminView, UserAdminView, MyAdminIndexView, LogAdminView

def create_app():
    app = Flask(__name__)
    app.secret_key = 'wd34efdtrdfgff@dfsdgt4tguy57697rtey44'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project_database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    manage = Admin(
        app, 
        name='Admin Site',
        template_mode='bootstrap4',
        url='/manage',
        index_view=MyAdminIndexView(name="Dashboard AI", url='/manage')
    )
    manage.add_view(UserAdminView(User, db.session))
    manage.add_view(ProductAdminView(Product, db.session))
    manage.add_view(ModelView(Category, db.session))
    manage.add_view(OrderAdminView(Order, db.session))
    manage.add_view(ModelView(OrderItem, db.session))
    manage.add_view(ModelView(CheckOut, db.session))
    manage.add_view(LogAdminView(Log, db.session))

    from main_site import main_bp
    from auth_site import auth_bp
    from order_site import order_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(order_bp, url_prefix='/order')

    @app.before_request
    def auto_log_request():
        path = request.path
        if '/static/' in path:
            return
        if path.startswith('/manage'):
            return
        user_agent = request.headers.get('User-Agent', '').lower()
        if 'bot' in user_agent:
            return
        payload_data = None
        if request.method == 'POST':
            try:
                payload_data = str(request.form.to_dict())
            except Exception:
                payload_data = "Error reading form data."
        new_log = Log(
            timestamp=datetime.datetime.now(),
            ip=request.remote_addr,
            method=request.method,
            path=path,
            payload=payload_data 
        )
        db.session.add(new_log)
        db.session.commit()

    with app.app_context():
        db.create_all()
        
    @app.context_processor
    def inject_common_data():
        all_categories = Category.query.all()
        _, cart_order = get_cart_data()
        return dict(all_categories=all_categories, cart_order=cart_order)
    return app