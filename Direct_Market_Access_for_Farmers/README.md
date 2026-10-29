# Direct Market Access for Farmers 🌱

A web-based agricultural marketplace platform connecting farmers directly with buyers, eliminating middlemen margins, enabling price negotiations, direct crop purchasing, and providing access to government welfare schemes.

## 🚀 Key Features
- **Direct Crop Marketplace**: Search, filter by crop categories (Vegetables, Grains, Fruits, Pulses, Dairy), and buy fresh farm produce.
- **Government Schemes Portal (`/schemes`)**: Comprehensive database of major schemes (PM-KISAN, PMFBY, Soil Health Card, e-NAM, Kisan Credit Card) with eligibility & application links.
- **Multi-Language Support**: Seamless language switching header supporting English, Tamil (தமிழ்), Hindi (हिंदी), Telugu (తెలుగు), Kannada (ಕನ್ನಡ), and Malayalam (മലയാളം).
- **Price Negotiation Workflow**: Buyers can propose custom prices and notes to farmers; farmers can accept or reject offers.
- **Role-Aware Dashboards**:
  - **Farmer**: Listing management, total sales revenue metrics, pending price negotiation offers, customer orders.
  - **Buyer**: Purchase history, direct order tracking with farmer contacts, sent offer status.
  - **Admin**: System control center, user accounts management, crop listings moderation, demo seeder.
- **Interactive Price Calculator**: Real-time total calculation based on selected quantity.

## 📁 Directory Structure
```
Direct_Market_Access_for_Farmers/
├── app.py                      # Flask Application Server & SQLite Database Controller
├── requirements.txt            # Python Dependencies
├── README.md                   # Project Documentation
├── database/
│   └── market.db               # SQLite Database
├── static/
│   ├── css/
│   │   └── style.css           # Agricultural Theme CSS Design System
│   └── js/
│       └── app.js              # Multi-Language Engine & Price Calculator JS
├── templates/                  # Flask Jinja2 Web Templates
│   ├── base.html
│   ├── index.html
│   ├── schemes.html            # Government Schemes Portal
│   ├── login.html
│   ├── register.html
│   ├── farmer_dashboard.html
│   ├── buyer_dashboard.html
│   ├── admin_dashboard.html
│   ├── add_produce.html
│   └── produce_detail.html
└── resources/
    ├── UI_UX_README.md         # UI Architecture Documentation
    ├── website_flow.txt        # User Navigation Tree
    └── templates/              # UI/UX Website HTML Templates Copy
```

## 🛠️ Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python app.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

### 3. Load Demo Seed Data
Navigate to [http://127.0.0.1:5000/seed](http://127.0.0.1:5000/seed) or click **"Re-seed Demo Data"** in the app to initialize sample produce, government schemes, and demo accounts:
- **Farmer**: `farmer@example.com` / `farmer123`
- **Buyer**: `buyer@example.com` / `buyer123`
- **Admin**: `admin@example.com` / `admin123`
