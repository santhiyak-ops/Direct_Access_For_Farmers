from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import random
import string
from pathlib import Path

app = Flask(__name__)
app.secret_key = "farmdirect-secret-key-farmers-access"
DB_DIR = Path(__file__).parent / "database"
DB = DB_DIR / "market.db"

DELIVERY_RANGES = {
  "Local (0 - 25 km)": 50.0,
  "Regional (25 - 100 km)": 150.0,
  "Inter-District (100 - 300 km)": 350.0,
  "State-wide Direct Freight (> 300 km)": 600.0
}

@app.before_request
def sanitize_legacy_sessions():
    if session.get("name") and "freshmarket" in session.get("name", "").lower():
        session["name"] = "Anbarasan Buyer"

def get_db():
    DB_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      email TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      role TEXT NOT NULL CHECK(role IN ('farmer','buyer','admin')),
      phone TEXT,
      location TEXT
    );
    CREATE TABLE IF NOT EXISTS produce(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      farmer_id INTEGER NOT NULL,
      name TEXT NOT NULL,
      category TEXT NOT NULL,
      quantity REAL NOT NULL,
      unit TEXT NOT NULL,
      price REAL NOT NULL,
      location TEXT NOT NULL,
      description TEXT,
      image_url TEXT,
      status TEXT DEFAULT 'Available',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(farmer_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS offers(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      produce_id INTEGER NOT NULL,
      buyer_id INTEGER NOT NULL,
      offered_price REAL NOT NULL,
      message TEXT,
      status TEXT DEFAULT 'Pending',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(produce_id) REFERENCES produce(id),
      FOREIGN KEY(buyer_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS orders(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      produce_id INTEGER NOT NULL,
      buyer_id INTEGER NOT NULL,
      quantity REAL NOT NULL,
      subtotal REAL DEFAULT 0,
      delivery_range TEXT DEFAULT 'Local (0 - 25 km)',
      delivery_fee REAL DEFAULT 50.0,
      total REAL NOT NULL,
      payment_method TEXT DEFAULT 'UPI / Online',
      payment_status TEXT DEFAULT 'Paid',
      transaction_id TEXT,
      shipping_address TEXT,
      status TEXT DEFAULT 'Confirmed',
      delivery_status TEXT DEFAULT 'Processing',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(produce_id) REFERENCES produce(id),
      FOREIGN KEY(buyer_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS schemes(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      category TEXT NOT NULL,
      description TEXT NOT NULL,
      eligibility TEXT NOT NULL,
      benefits TEXT NOT NULL,
      application_link TEXT,
      icon TEXT DEFAULT '🌾'
    );
    """)
    conn.commit()

    # Clean up any legacy FreshMarket Retailers records
    conn.execute("DELETE FROM users WHERE LOWER(name) LIKE '%freshmarket%'")
    conn.commit()

    # Auto seed schemes if empty
    count_schemes = conn.execute("SELECT COUNT(*) FROM schemes").fetchone()[0]
    if count_schemes == 0:
        seed_schemes(conn)

    # Auto seed demo users and produce if empty
    count_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count_users == 0:
        seed_demo_data(conn)

    conn.close()

def seed_schemes(conn):
    sample_schemes = [
        ("PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)", "Financial Support",
         "Direct income support of ₹6,000 per year in three equal installments to small and marginal farmer families.",
         "Small & Marginal farmers with cultivable landholding up to 2 hectares.",
         "Direct cash transfer of ₹6,000 annually into bank account.", "https://pmkisan.gov.in", "💰"),
        ("PMFBY (Pradhan Mantri Fasal Bima Yojana)", "Crop Insurance",
         "Comprehensive crop insurance policy covering yield loss due to non-preventable natural risks.",
         "All farmers including sharecroppers and tenant farmers growing notified crops.",
         "Financial protection against crop loss due to drought, flood, or pests.", "https://pmfby.gov.in", "🛡️"),
        ("Soil Health Card Scheme", "Agri Inputs & Health",
         "Provides soil health cards to farmers every 2 years with nutrient status & fertilizer recommendations.",
         "All land-holding farmers across India.",
         "Customized fertilizer recommendations to improve yield and soil quality.", "https://soilhealth.dac.gov.in", "🌱"),
        ("e-NAM (National Agriculture Market)", "Market Access",
         "Pan-India electronic trading portal networking existing APMC mandis to create a unified national market.",
         "Registered farmers, buyers, and FPOs across participating states.",
         "Transparent price discovery and direct online trading.", "https://www.enam.gov.in", "🌐"),
        ("Kisan Credit Card (KCC)", "Credit & Loans",
         "Provides short-term formal credit to farmers for crop cultivation, post-harvest expenses, and allied activities.",
         "Farmers, tenant farmers, oral lessees, and SHGs.",
         "Flexible credit limit up to ₹3 Lakhs at subsidized interest rates (4% p.a.).", "https://pmkisan.gov.in", "💳"),
        ("Agri-Infrastructure Fund (AIF)", "Infrastructure",
         "Medium to long term debt financing facility for investment in viable post-harvest management infrastructure.",
         "Farmers, FPOs, Agri-entrepreneurs, and Startups.",
         "3% Interest subvention on loans up to ₹2 Crores for 7 years.", "https://agriinfra.dac.gov.in", "🏗️")
    ]
    conn.executemany("""INSERT INTO schemes (title, category, description, eligibility, benefits, application_link, icon)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""", sample_schemes)
    conn.commit()

def seed_demo_data(conn):
    try:
        conn.execute("""
            INSERT INTO users (name, email, password, role, phone, location)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("Santhiya", "farmer@example.com", "farmer123", "farmer", "+91 9876543210", "Kovilpatti, Tamil Nadu"))

        conn.execute("""
            INSERT INTO users (name, email, password, role, phone, location)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("Anbarasan Buyer", "buyer@example.com", "buyer123", "buyer", "+91 9123456789", "Madurai, Tamil Nadu"))

        conn.execute("""
            INSERT INTO users (name, email, password, role, phone, location)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("AgriAdmin", "admin@example.com", "admin123", "admin", "+91 9000000000", "Chennai, Tamil Nadu"))

        farmer_id = conn.execute("SELECT id FROM users WHERE email = 'farmer@example.com'").fetchone()["id"]
        buyer_id = conn.execute("SELECT id FROM users WHERE email = 'buyer@example.com'").fetchone()["id"]

        sample_produce = [
            (farmer_id, "Organic Country Tomatoes", "Vegetables", 150.0, "kg", 38.0, "Kovilpatti", "Vine-ripened organic red tomatoes cultivated without chemical pesticides.", "🍅"),
            (farmer_id, "Premium Samba Rice", "Grains & Cereals", 500.0, "kg", 62.0, "Thanjavur", "Traditional aromatic Samba paddy rice directly harvested from Tanjore delta.", "🌾"),
            (farmer_id, "Fresh Red Onions", "Vegetables", 300.0, "kg", 32.0, "Perambalur", "Medium-sized pungent farm fresh red onions with long shelf life.", "🧅"),
            (farmer_id, "Farm Fresh Alphonso Mangoes", "Fruits", 80.0, "kg", 180.0, "Salem", "Sweet naturally ripened Alphonso mangoes direct from Salem orchards.", "🥭"),
            (farmer_id, "Green Gram (Moong Dal)", "Pulses", 200.0, "kg", 95.0, "Tirunelveli", "Unpolished organic green gram rich in protein and dietary fiber.", "🫘"),
            (farmer_id, "Pure Desi Cow Milk", "Dairy & Livestock", 100.0, "Litre", 55.0, "Erode", "Fresh unpasteurized A2 cow milk from free-range indigenous cattle.", "🥛")
        ]

        conn.executemany("""
            INSERT INTO produce (farmer_id, name, category, quantity, unit, price, location, description, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_produce)

        produce_id = conn.execute("SELECT id FROM produce WHERE name LIKE '%Tomatoes%'").fetchone()["id"]

        conn.execute("""
            INSERT INTO offers (produce_id, buyer_id, offered_price, message, status)
            VALUES (?, ?, ?, ?, ?)
        """, (produce_id, buyer_id, 34.0, "Looking for bulk purchase of 100 kg. Can you lower price to ₹34/kg?", "Pending"))

        conn.execute("""
            INSERT INTO orders (produce_id, buyer_id, quantity, subtotal, delivery_range, delivery_fee, total, payment_method, payment_status, transaction_id, shipping_address, status, delivery_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'UPI / GPay', 'Paid', 'TXN9849201948', '12 Market Road, Madurai', 'Confirmed', 'In-Transit (Regional Freight)')
        """, (produce_id, buyer_id, 50.0, 1900.0, "Regional (25 - 100 km)", 150.0, 2050.0))

        conn.commit()
    except sqlite3.IntegrityError:
        pass

def get_cart_details():
    cart = session.get("cart", {})
    if not cart:
        return [], 0, 0, 0

    conn = get_db()
    items = []
    subtotal = 0
    total_delivery_fee = 0

    for pid_str, details in cart.items():
        pid = int(pid_str)
        produce = conn.execute("SELECT p.*, u.name as farmer_name FROM produce p JOIN users u ON p.farmer_id = u.id WHERE p.id = ?", (pid,)).fetchone()
        if produce:
            qty = float(details.get("quantity", 1))
            range_name = details.get("delivery_range", "Local (0 - 25 km)")
            delivery_fee = DELIVERY_RANGES.get(range_name, 50.0)
            item_subtotal = qty * produce["price"]
            
            subtotal += item_subtotal
            total_delivery_fee += delivery_fee

            items.append({
                "produce_id": pid,
                "name": produce["name"],
                "category": produce["category"],
                "unit": produce["unit"],
                "price": produce["price"],
                "image_url": produce["image_url"],
                "farmer_name": produce["farmer_name"],
                "quantity": qty,
                "delivery_range": range_name,
                "delivery_fee": delivery_fee,
                "item_subtotal": item_subtotal,
                "item_total": item_subtotal + delivery_fee,
                "stock": produce["quantity"]
            })
    conn.close()
    grand_total = subtotal + total_delivery_fee
    return items, subtotal, total_delivery_fee, grand_total

@app.route("/")
def index():
    conn = get_db()
    category = request.args.get("category", "")
    search = request.args.get("search", "")

    query = """SELECT p.*, u.name as farmer_name, u.phone as farmer_phone 
               FROM produce p JOIN users u ON p.farmer_id = u.id 
               WHERE p.status = 'Available'"""
    params = []

    if category:
        query += " AND p.category = ?"
        params.append(category)
    if search:
        query += " AND (p.name LIKE ? OR p.location LIKE ? OR p.description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    query += " ORDER BY p.id DESC"

    produce_items = conn.execute(query, params).fetchall()
    categories = conn.execute("SELECT DISTINCT category FROM produce").fetchall()
    conn.close()

    return render_template("index.html", produce=produce_items, categories=[c[0] for c in categories], current_category=category, search_query=search)

@app.route("/schemes")
def schemes():
    conn = get_db()
    category = request.args.get("category", "")
    search = request.args.get("search", "")

    query = "SELECT * FROM schemes WHERE 1=1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)
    if search:
        query += " AND (title LIKE ? OR description LIKE ? OR eligibility LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    query += " ORDER BY id ASC"

    scheme_list = conn.execute(query, params).fetchall()
    categories = conn.execute("SELECT DISTINCT category FROM schemes").fetchall()
    conn.close()

    return render_template("schemes.html", schemes=scheme_list, categories=[c[0] for c in categories], current_category=category, search_query=search)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        conn = get_db()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "farmer")
        phone = request.form.get("phone", "").strip()
        location = request.form.get("location", "").strip()

        try:
            conn.execute("INSERT INTO users (name, email, password, role, phone, location) VALUES (?, ?, ?, ?, ?, ?)",
                         (name, email, password, role, phone, location))
            conn.commit()
            flash("Registration successful! Please login to continue.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email address is already registered. Please use another email.", "error")
        finally:
            conn.close()

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = get_db()
        user_input = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = conn.execute("""
            SELECT * FROM users 
            WHERE (LOWER(email) = ? OR LOWER(name) = ?) AND password = ?
        """, (user_input, user_input, password)).fetchone()
        conn.close()

        if user:
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            session["role"] = user["role"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email/username or password. Please try again.", "error")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please log in to access your dashboard.", "error")
        return redirect(url_for("login"))

    conn = get_db()
    role = session["role"]
    user_id = session["user_id"]

    if role == "farmer":
        produce = conn.execute("SELECT * FROM produce WHERE farmer_id = ? ORDER BY id DESC", (user_id,)).fetchall()
        offers = conn.execute("""
            SELECT o.*, p.name as produce_name, u.name as buyer_name, u.phone as buyer_phone
            FROM offers o
            JOIN produce p ON o.produce_id = p.id
            JOIN users u ON o.buyer_id = u.id
            WHERE p.farmer_id = ? ORDER BY o.id DESC
        """, (user_id,)).fetchall()
        orders = conn.execute("""
            SELECT ord.*, p.name as produce_name, u.name as buyer_name, u.phone as buyer_phone, u.location as buyer_location
            FROM orders ord
            JOIN produce p ON ord.produce_id = p.id
            JOIN users u ON ord.buyer_id = u.id
            WHERE p.farmer_id = ? ORDER BY ord.id DESC
        """, (user_id,)).fetchall()
        
        total_sales = sum([o["total"] for o in orders if o["status"] in ("Confirmed", "Delivered")])
        conn.close()
        return render_template("farmer_dashboard.html", produce=produce, offers=offers, orders=orders, total_sales=total_sales)

    elif role == "admin":
        users = conn.execute("SELECT id, name, email, role, phone, location FROM users ORDER BY id DESC").fetchall()
        produce = conn.execute("""
            SELECT p.*, u.name as farmer_name FROM produce p JOIN users u ON p.farmer_id = u.id ORDER BY p.id DESC
        """).fetchall()
        orders = conn.execute("""
            SELECT ord.*, p.name as produce_name, u.name as buyer_name FROM orders ord
            JOIN produce p ON ord.produce_id = p.id JOIN users u ON ord.buyer_id = u.id ORDER BY ord.id DESC
        """).fetchall()
        conn.close()
        return render_template("admin_dashboard.html", users=users, produce=produce, orders=orders)

    else: # buyer
        orders = conn.execute("""
            SELECT ord.*, p.name as produce_name, p.unit, p.price as original_price, u.name as farmer_name, u.phone as farmer_phone
            FROM orders ord
            JOIN produce p ON ord.produce_id = p.id
            JOIN users u ON p.farmer_id = u.id
            WHERE ord.buyer_id = ? ORDER BY ord.id DESC
        """, (user_id,)).fetchall()
        offers = conn.execute("""
            SELECT o.*, p.name as produce_name, p.price as listed_price, u.name as farmer_name
            FROM offers o
            JOIN produce p ON o.produce_id = p.id
            JOIN users u ON p.farmer_id = u.id
            WHERE o.buyer_id = ? ORDER BY o.id DESC
        """, (user_id,)).fetchall()
        
        total_spent = sum([o["total"] for o in orders])
        conn.close()
        return render_template("buyer_dashboard.html", orders=orders, offers=offers, total_spent=total_spent)

@app.route("/produce/add", methods=["GET", "POST"])
def add_produce():
    if session.get("role") != "farmer":
        flash("Only registered farmers can list produce.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "Vegetables")
        quantity = float(request.form.get("quantity", 0))
        unit = request.form.get("unit", "kg")
        price = float(request.form.get("price", 0))
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip()
        image_url = request.form.get("image_url", "").strip()

        if not name or quantity <= 0 or price <= 0:
            flash("Please provide valid product details, quantity, and price.", "error")
            return redirect(url_for("add_produce"))

        conn = get_db()
        conn.execute("""
            INSERT INTO produce (farmer_id, name, category, quantity, unit, price, location, description, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (session["user_id"], name, category, quantity, unit, price, location, description, image_url))
        conn.commit()
        conn.close()

        flash("Produce listed successfully on the marketplace!", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_produce.html")

@app.route("/produce/<int:produce_id>")
def produce_detail(produce_id):
    conn = get_db()
    produce = conn.execute("""
        SELECT p.*, u.name as farmer_name, u.email as farmer_email, u.phone as farmer_phone, u.location as farmer_location
        FROM produce p JOIN users u ON p.farmer_id = u.id
        WHERE p.id = ?
    """, (produce_id,)).fetchone()
    conn.close()

    if not produce:
        flash("Produce item not found.", "error")
        return redirect(url_for("index"))

    return render_template("produce_detail.html", item=produce, delivery_ranges=DELIVERY_RANGES)

@app.route("/cart")
def view_cart():
    cart_items, subtotal, delivery_fee, grand_total = get_cart_details()
    return render_template("cart.html", cart_items=cart_items, subtotal=subtotal, delivery_fee=delivery_fee, grand_total=grand_total, delivery_ranges=DELIVERY_RANGES)

@app.route("/cart/add/<int:produce_id>", methods=["POST"])
def add_to_cart(produce_id):
    if session.get("role") and session.get("role") != "buyer":
        flash("Only registered buyer accounts can add produce to cart.", "error")
        return redirect(url_for("produce_detail", produce_id=produce_id))

    qty = float(request.form.get("quantity", 1))
    delivery_range = request.form.get("delivery_range", "Local (0 - 25 km)")

    conn = get_db()
    produce = conn.execute("SELECT * FROM produce WHERE id = ?", (produce_id,)).fetchone()
    conn.close()

    if not produce or qty <= 0 or qty > produce["quantity"]:
        flash("Invalid quantity or insufficient produce stock.", "error")
        return redirect(url_for("produce_detail", produce_id=produce_id))

    cart = session.get("cart", {})
    pid_str = str(produce_id)

    if pid_str in cart:
        cart[pid_str]["quantity"] = qty
        cart[pid_str]["delivery_range"] = delivery_range
    else:
        cart[pid_str] = {"quantity": qty, "delivery_range": delivery_range}

    session["cart"] = cart
    session.modified = True
    flash(f"Added {qty} {produce['unit']} of {produce['name']} to your cart!", "success")
    return redirect(url_for("view_cart"))

@app.route("/cart/update", methods=["POST"])
def update_cart():
    cart = session.get("cart", {})
    for key in request.form:
        if key.startswith("qty_"):
            pid_str = key.split("_")[1]
            if pid_str in cart:
                try:
                    new_qty = float(request.form[key])
                    if new_qty > 0:
                        cart[pid_str]["quantity"] = new_qty
                    else:
                        del cart[pid_str]
                except ValueError:
                    pass
        elif key.startswith("range_"):
            pid_str = key.split("_")[1]
            if pid_str in cart:
                cart[pid_str]["delivery_range"] = request.form[key]

    session["cart"] = cart
    session.modified = True
    flash("Cart updated successfully.", "info")
    return redirect(url_for("view_cart"))

@app.route("/cart/remove/<int:produce_id>", methods=["POST"])
def remove_from_cart(produce_id):
    cart = session.get("cart", {})
    pid_str = str(produce_id)
    if pid_str in cart:
        del cart[pid_str]
        session["cart"] = cart
        session.modified = True
        flash("Item removed from cart.", "info")
    return redirect(url_for("view_cart"))

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if session.get("role") != "buyer":
        flash("Please log in as a buyer to proceed with payment.", "error")
        return redirect(url_for("login"))

    cart_items, subtotal, delivery_fee, grand_total = get_cart_details()
    if not cart_items:
        flash("Your cart is empty. Add produce items before checkout.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        payment_method = request.form.get("payment_method", "UPI / GPay / PhonePe")
        shipping_address = request.form.get("shipping_address", "").strip()
        
        txn_id = "TXN" + "".join(random.choices(string.digits, k=10))

        conn = get_db()
        created_orders = []

        for item in cart_items:
            pid = item["produce_id"]
            qty = item["quantity"]
            item_subtotal = item["item_subtotal"]
            del_range = item["delivery_range"]
            del_fee = item["delivery_fee"]
            item_total = item["item_total"]

            cursor = conn.execute("""
                INSERT INTO orders (produce_id, buyer_id, quantity, subtotal, delivery_range, delivery_fee, total, payment_method, payment_status, transaction_id, shipping_address, status, delivery_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Paid', ?, ?, 'Confirmed', 'Dispatched for Delivery Range')
            """, (pid, session["user_id"], qty, item_subtotal, del_range, del_fee, item_total, payment_method, txn_id, shipping_address))

            new_qty = item["stock"] - qty
            status_text = "Available" if new_qty > 0 else "Sold Out"
            conn.execute("UPDATE produce SET quantity = ?, status = ? WHERE id = ?", (new_qty, status_text, pid))

            created_orders.append(cursor.lastrowid)

        conn.commit()
        conn.close()

        session.pop("cart", None)
        flash(f"Payment successful! Transaction ID: {txn_id}. Orders confirmed.", "success")
        return render_template("order_confirmation.html", orders=created_orders, txn_id=txn_id, total_paid=grand_total, payment_method=payment_method, shipping_address=shipping_address)

    return render_template("checkout.html", cart_items=cart_items, subtotal=subtotal, delivery_fee=delivery_fee, grand_total=grand_total)

@app.route("/offer/<int:produce_id>", methods=["POST"])
def make_offer(produce_id):
    if session.get("role") != "buyer":
        flash("Only buyers can submit price offers.", "error")
        return redirect(url_for("login"))

    offered_price = float(request.form.get("offered_price", 0))
    message = request.form.get("message", "").strip()

    if offered_price <= 0:
        flash("Please enter a valid offer price.", "error")
        return redirect(url_for("produce_detail", produce_id=produce_id))

    conn = get_db()
    conn.execute("""
        INSERT INTO offers (produce_id, buyer_id, offered_price, message)
        VALUES (?, ?, ?, ?)
    """, (produce_id, session["user_id"], offered_price, message))
    conn.commit()
    conn.close()

    flash("Your price negotiation offer has been sent to the farmer!", "success")
    return redirect(url_for("produce_detail", produce_id=produce_id))

@app.route("/order/<int:produce_id>", methods=["POST"])
def place_order(produce_id):
    if session.get("role") != "buyer":
        flash("Please log in as a buyer to place an order.", "error")
        return redirect(url_for("login"))

    qty = float(request.form.get("quantity", 0))
    delivery_range = request.form.get("delivery_range", "Local (0 - 25 km)")

    cart = session.get("cart", {})
    cart[str(produce_id)] = {"quantity": qty, "delivery_range": delivery_range}
    session["cart"] = cart
    session.modified = True

    return redirect(url_for("checkout"))

@app.route("/order/<int:order_id>/delivery/<delivery_status>")
def update_delivery_status(order_id, delivery_status):
    if session.get("role") not in ("farmer", "admin"):
        flash("Unauthorized action.", "error")
        return redirect(url_for("login"))

    valid_statuses = ["Processing", "Dispatched for Delivery Range", "In-Transit (Regional Freight)", "Out for Delivery", "Delivered to Buyer"]
    if delivery_status not in valid_statuses:
        flash("Invalid delivery status.", "error")
        return redirect(url_for("dashboard"))

    conn = get_db()
    conn.execute("UPDATE orders SET delivery_status = ? WHERE id = ?", (delivery_status, order_id))
    conn.commit()
    conn.close()

    flash(f"Order #{order_id} delivery status updated to '{delivery_status}'.", "info")
    return redirect(url_for("dashboard"))

@app.route("/offer/<int:offer_id>/update/<status>")
def update_offer(offer_id, status):
    if session.get("role") != "farmer" or status not in ("Accepted", "Rejected"):
        flash("Unauthorized action.", "error")
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute("UPDATE offers SET status = ? WHERE id = ?", (status, offer_id))
    conn.commit()
    conn.close()

    flash(f"Offer marked as {status}.", "info")
    return redirect(url_for("dashboard"))

@app.route("/seed")
def seed():
    conn = get_db()
    conn.execute("DELETE FROM users WHERE LOWER(name) LIKE '%freshmarket%'")
    conn.commit()
    seed_demo_data(conn)
    conn.close()
    flash("Demo data seeded!", "success")
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    print("Direct Market Access for Farmers - Running at http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
