# AI-Web-IDS
This is an e-commerce website project built with Python and Flask. Its key feature is the integration of a simple Intrusion Detection System (IDS) that uses AI (TensorFlow) to analyze and flag anomalous web traffic.

## Key Features

* **Functionality:**
    * Browse products by category, search for products.
    * View product details.
    * Dynamic shopping cart (add, update, remove items).
    * Checkout process and order history review.

* **Admin Panel:**
    * A protected admin interface at `/manage`, accessible only by admin accounts.
    * Manage (Create, Update, Delete) users, products, categories, and orders.

* ** AI Intrusion Detection System (AI-IDS):**
    * Automatically logs valid web requests to the database.
    * A `train_model.py` script to train the AI model from log data.
    * An analysis dashboard that displays recent traffic and the AI's classification (Normal, Anomalous, New).
    * Allows exporting log data to CSV or Excel files.

## Tech Stack
* **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Admin.
* **AI & Data:** TensorFlow, Pandas, Scikit-learn, Matplotlib.
* **Frontend:** HTML, JavaScript, Bootstrap 5.
* **Database:** SQLite.