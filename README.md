# AI-Web-IDS: AI-Powered Web Intrusion Detection System

This is an e-commerce website project built with Python and Flask, featuring an intelligent **Intrusion Detection System (IDS)**. The system leverages AI (TensorFlow) to analyze web traffic in real-time to detect anomalous behavior and provides automated threat response capabilities.

## Core Features

### 1. E-commerce Platform
* **User Experience:**
    * Browse products by category and search for products.
    * View detailed product information.
    * Dynamic shopping cart (add, update, remove items).
    * Checkout process and order history review.

### 2. AI-Powered Intrusion Detection System (AI-IDS)
The core security feature of the project, designed to identify and respond to potential threats.
* **Real-time Analysis:** Every request to the server is logged and immediately passed through the AI model for analysis.
* **Attack Tracking:** The system maintains a counter, tracking the number of times an IP address is flagged for suspicious behavior.
* **Automated Threat Response:** When an IP exceeds a configurable attack threshold (e.g., 5 attempts), it is automatically added to a blacklist, effectively blocking it.
* **Temporary Blocking:** Blacklisted IPs are automatically removed after a set period (e.g., 60 minutes).

### 3. Advanced Admin Panel
A protected admin interface at `/manage`, accessible only by admin accounts.
* **CRUD Management:** Provides full Create, Read, Update, and Delete functionality for Users, Products, Categories, and Orders.
* **Security Dashboard:**
    * A single-screen, intuitive interface for all security information.
    * Displays a high-level overview of total site traffic.
    * Features a real-time "IP Blacklist" panel and an "Anomalous Activity Log" as detected by the AI.
* **Blacklist Management:** A dedicated page allows administrators to view all currently blocked IPs and manually unblock them if necessary.
* **Log Export:** Allows exporting the entire access log to CSV or Excel files for further analysis.

## Project Structure


├── admin_site/         # Logic and views for the admin site

├── auth_site/          # Logic and views for authentication (login, register)

├── main_site/          # Logic and views for user-facing pages (home, products)

├── order_site/         # Logic and views for the shopping cart and checkout

├── model/              # Contains the trained AI model files

├── static/             # Static files (CSS, JS, images)

├── templates/          # HTML templates

├── migrations/         # Database migration files

├── app.py              # Main Flask application factory

├── models.py           # Database models (User, Product, Log, Blacklist...)

├── train_model.py      # Script to train the AI model from log data

├── run.py              # Script to run the application

└── requirements.txt    # List of required Python packages


## Tech Stack
* **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Admin, Flask-WTF
* **AI & Data:** TensorFlow, Pandas, Scikit-learn
* **Frontend:** HTML, CSS, JavaScript (using Flask-Admin's base templates)
* **Database:** SQLite

## Installation and Setup Guide

**Prerequisites:** Python 3.8+ and pip.

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/tan93493/AI-Web-IDS.git
    cd ai-web-ids
    ```

2.  **Create and Activate a Virtual Environment**
    ```bash
    # On Windows
    python -m venv venv
    .\venv\Scripts\activate

    # On macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Required Packages**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize and Upgrade the Database**
    On the first run, you need to create the database tables.
    ```bash
    flask db upgrade
    ```
    *If you encounter an error, first try `flask db migrate -m "Initial migration"` and then `upgrade`.*

5.  **Train the AI Model**
    For the AI system to work, you need to train the model using sample data.
    ```bash
    python train_model.py
    ```
    This command will create `ai_ids_model.h5` and `preprocessor.pkl` inside the `model/` directory.

6.  **Run the Application**
    ```bash
    python run.py
    ```
