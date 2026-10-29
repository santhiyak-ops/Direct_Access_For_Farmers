# Direct Market Access for Farmers - UI/UX Architecture

The complete website UI/UX is built with responsive HTML5 Jinja2 templates, a custom CSS3 design system, and multi-language client interactivity.

## Template Locations
- Flask App Runtime Templates: `templates/`
- Documentation & Resource Copy: `resources/templates/`

## Screens Included (10 Pages):
1. **Marketplace Home (`index.html`)**: Crop search, category filters, market advisories, hero stats.
2. **Government Schemes Portal (`schemes.html`)**: PM-KISAN, crop insurance, credit cards, subsidies, eligibility, and official links.
3. **Login (`login.html`)**: Multi-role login (Farmer, Buyer, Admin) with demo shortcuts.
4. **Register (`register.html`)**: Account creation with role selection, mobile number, and location.
5. **Farmer Dashboard (`farmer_dashboard.html`)**: Revenue metrics, crop management, incoming price offer negotiations, direct orders.
6. **Buyer Dashboard (`buyer_dashboard.html`)**: Spend metrics, direct order history with farmer contacts, sent offer tracking.
7. **Admin Dashboard (`admin_dashboard.html`)**: User management, produce moderation, system statistics, re-seeder.
8. **Add Produce (`add_produce.html`)**: Farmer crop listing form with unit, quantity, direct price, description, and emoji icons.
9. **Produce Detail (`produce_detail.html`)**: Live interactive price calculator, direct order placement, counter-offer form, farmer contact info.
10. **Base Master Layout (`base.html`)**: Sticky header navbar, multi-language switcher dropdown, flash notification container, and footer.

## Multi-Language Options Supported:
- English (EN)
- Tamil (தமிழ்)
- Hindi (हिंदी)
- Telugu (తెలుగు)
- Kannada (ಕನ್ನಡ)
- Malayalam (മലയാളം)
