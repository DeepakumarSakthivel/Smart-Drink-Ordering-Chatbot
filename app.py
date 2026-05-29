from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import os
import threading
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import random
import re


def speak_text(text):
    pass

def send_order_email(user_email, order_details):
    sender_email = "deepakumar3105s@gmail.com"
    # IMPORTANT: Replace with actual App Password if you want this to work.
    sender_password = "kgny qenj meri potc" 
    
    msg = MIMEText(f"Thank you for your order!\n\nDetails:\n{order_details}")
    msg['Subject'] = 'BNC App - Order Confirmation'
    msg['From'] = sender_email
    msg['To'] = user_email

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, user_email, msg.as_string())
        server.quit()
        print(f"Email sent successfully to {user_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def send_otp_email(user_email, otp):
    sender_email = "deepakumar3105s@gmail.com"
    sender_password = "kgny qenj meri potc" 
    
    msg = MIMEText(f"Your verification code for BNC App is: {otp}")
    msg['Subject'] = 'BNC App - Verification OTP'
    msg['From'] = sender_email
    msg['To'] = user_email

    print(f"\n--- DEV MODE: OTP is {otp} for {user_email} ---\n") # Print to console

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, user_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send OTP email: {e}")

def send_low_stock_email(product_name, stock):
    sender_email = "deepakumar3105s@gmail.com"
    sender_password = "kgny qenj meri potc" 
    admin_email = "deepakumar3105s@gmail.com"
    
    msg = MIMEText(f"Low Stock Alert!\n\nThe product '{product_name}' has low stock.\nCurrent Stock: {stock} (5 or less)\n\nPlease restock this product as soon as possible.")
    msg['Subject'] = f'BNC App - Low Stock Alert: {product_name}'
    msg['From'] = sender_email
    msg['To'] = admin_email

    print(f"\n--- DEV MODE: Low Stock Alert sent for {product_name} (Stock: {stock}) ---\n") # Print to console

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, admin_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send low stock email alert: {e}")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'bnc_secret_key_123' # required for session and flash

db = SQLAlchemy(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_recent_orders():
    if session.get('role') == 'admin':
        recent_orders = Order.query.order_by(Order.order_date.desc()).limit(5).all()
        low_stock_products = Product.query.filter(Product.stock <= 5).all()
        return dict(recent_orders=recent_orders, low_stock_products=low_stock_products)
    return dict(recent_orders=[], low_stock_products=[])

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    mobile = db.Column(db.String(20), nullable=True)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    orders = db.relationship('Order', backref='user', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email='admin@test.com').first():
        admin = User(email='admin@test.com', password='admin', role='admin')
        db.session.add(admin)
        db.session.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            if user.role == 'admin':
                return redirect(url_for('admin_stock'))
            else:
                return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists. Please login.', 'error')
            return redirect(url_for('signup'))
            
        otp = str(random.randint(100000, 999999))
        session['signup_data'] = {'email': email, 'mobile': mobile, 'password': password, 'otp': otp}
        
        threading.Thread(target=send_otp_email, args=(email, otp)).start()
        
        flash('An OTP has been sent to your email.', 'success')
        return redirect(url_for('verify_otp'))
        
    return render_template('signup.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'signup_data' not in session:
        return redirect(url_for('signup'))
        
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        signup_data = session['signup_data']
        
        if entered_otp == signup_data['otp']:
            new_user = User(
                email=signup_data['email'], 
                mobile=signup_data['mobile'], 
                password=signup_data['password'], 
                role='user'
            )
            db.session.add(new_user)
            db.session.commit()
            session.pop('signup_data', None)
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid OTP. Please try again.', 'error')
            
    return render_template('otp.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/history')
@login_required
def history():
    user_id = session.get('user_id')
    user_orders = Order.query.filter_by(user_id=user_id).order_by(Order.order_date.desc()).all()
    return render_template('history.html', orders=user_orders)

@app.route('/admin/orders')
@admin_required
def admin_orders():
    all_orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('admin_orders.html', orders=all_orders)

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/admin/products', methods=['GET', 'POST'])
@admin_required
def admin_products():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            name = request.form.get('name')
            price = float(request.form.get('price'))
            new_prod = Product(name=name, price=price, stock=0)
            db.session.add(new_prod)
            db.session.commit()
        elif action == 'edit':
            prod_id = int(request.form.get('id'))
            name = request.form.get('name')
            price = float(request.form.get('price'))
            prod = Product.query.get(prod_id)
            if prod:
                prod.name = name
                prod.price = price
                db.session.commit()
        elif action == 'delete':
            prod_id = int(request.form.get('id'))
            prod = Product.query.get(prod_id)
            if prod:
                db.session.delete(prod)
                db.session.commit()
        return redirect(url_for('admin_products'))
    
    products = Product.query.all()
    return render_template('admin_products.html', products=products)

@app.route('/admin/stock', methods=['GET', 'POST'])
@admin_required
def admin_stock():
    if request.method == 'POST':
        prod_id = int(request.form.get('id'))
        stock = int(request.form.get('stock'))
        prod = Product.query.get(prod_id)
        if prod:
            prod.stock = stock
            db.session.commit()
            if prod.stock <= 5:
                threading.Thread(target=send_low_stock_email, args=(prod.name, prod.stock)).start()
        return redirect(url_for('admin_stock'))

    products = Product.query.all()
    return render_template('admin_stock.html', products=products)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None
    
    data = request.get_json()
    message = data.get('message', '').strip().lower()
    
    products = Product.query.all()
    product_names = {p.name.lower(): p for p in products}
    
    response_text = ""
    
    if any(greet in message for greet in ['hello', 'hi', 'show menu', 'menu', 'products']):
        if not products:
            response_text = "Hello! We currently don't have any products available."
        else:
            product_list = ", ".join([f"{p.name} (₹{p.price:.2f})" for p in products if p.stock > 0])
            if product_list:
                response_text = f"Hello! We have the following products available: {product_list}. What would you like to order?"
            else:
                response_text = "Hello! Sorry, all our products are currently out of stock."
            
    elif any(order_word in message for order_word in ['order', 'want', 'buy', 'get']):
        orders_to_place = []
        
        for p_name, p_data in product_names.items():
            if p_name in message:
                qty = 1
                match1 = re.search(r'\b' + re.escape(p_name) + r'\s+(\d+)\b', message)
                match2 = re.search(r'\b(\d+)\s+' + re.escape(p_name) + r'\b', message)
                if match1:
                    qty = int(match1.group(1))
                elif match2:
                    qty = int(match2.group(1))
                orders_to_place.append({'product': p_data, 'qty': qty})
        
        if orders_to_place:
            total_price = 0
            order_messages = []
            email_details = []
            
            insufficient_stock = False
            for item in orders_to_place:
                p = item['product']
                if p.stock < item['qty']:
                    response_text = f"Sorry, we only have {p.stock} of {p.name} in stock, but you asked for {item['qty']}. Please adjust your order."
                    insufficient_stock = True
                    break
            
            if not insufficient_stock:
                for item in orders_to_place:
                    p = item['product']
                    qty = item['qty']
                    p.stock -= qty
                    
                    if p.stock <= 5:
                        threading.Thread(target=send_low_stock_email, args=(p.name, p.stock)).start()
                    
                    item_price = p.price * qty
                    total_price += item_price
                    
                    product_label = f"{p.name} (x{qty})" if qty > 1 else p.name
                    order_messages.append(product_label)
                    email_details.append(f"{product_label} - ₹{item_price:.2f}")
                    
                    if user:
                        new_order = Order(user_id=user.id, product_name=product_label, price=item_price)
                        db.session.add(new_order)
                
                db.session.commit()
                response_text = f"Order confirmed! You ordered: {', '.join(order_messages)}. Total will be ₹{total_price:.2f}."
                threading.Thread(target=speak_text, args=(response_text,)).start()
                
                if user and user.email:
                    details_str = "\n".join(email_details) + f"\n\nTotal: ₹{total_price:.2f}"
                    threading.Thread(target=send_order_email, args=(user.email, details_str)).start()
        else:
            response_text = "I'm sorry, I couldn't recognize which product you want to order. Please mention a valid product."
    else:
        response_text = "I'm a simple bot. You can say 'show menu' to see drinks, or 'I want [drink name]' to order."
    
    return jsonify({"reply": response_text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
