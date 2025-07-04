from app import create_app

app = create_app()
with app.app_context():
    from extensions import db
    from models import User, Product, Category, Order, OrderItem, CheckOut, Log

if __name__ == '__main__':
    app.run(debug=True)