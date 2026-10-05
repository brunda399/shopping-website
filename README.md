# Online E-Commerce Website (ShopEase)

A modern, scalable, and professional Online E-Commerce platform built with Python Flask and SQLAlchemy. Designed with an enterprise-ready 3-tier layered architecture while maintaining an approachable structure for academic excellence and real-world extensibility.

---

## 1. Project Description

**ShopEase** is a complete e-commerce solution providing seamless shopping experiences for customers and robust administrative management tools for store owners. Customers can browse products, search with live auto-suggestions, filter by categories, manage carts and wishlists with slide-out drawers, securely place orders, and review past purchases. Store administrators are equipped with metrics dashboards, product management capabilities, and order status fulfillment workflows.


The system is developed **module by module** using modern software engineering best practices, centralized configuration, secure credential handling, and responsive user-centric design.

---

## 2. Technology Stack

### Frontend
- **HTML5**: Semantic, accessible markup structure.
- **CSS3 (Vanilla)**: Custom design system utilizing CSS variables, responsive fluid grids, mobile-first media queries, and micro-animations.
- **JavaScript (ES6+)**: Modular client logic featuring a centralized `ApiService` wrapper handling asynchronous fetch operations, loading states, and toast notifications.

### Backend
- **Python 3.11+**: Core backend runtime.
- **Flask (v3.1+)**: Modular application factory with Blueprints.
- **Werkzeug**: Cryptographic password hashing (`generate_password_hash`, `check_password_hash`).
- **Python-Dotenv**: Environment configuration isolation.

### Database & ORM
- **SQLite3**: Initial lightweight relational storage located in `instance/ecommerce.db`.
- **SQLAlchemy (v2.0+) / Flask-SQLAlchemy (v3.1+)**: High-performance Object-Relational Mapper enabling migration to PostgreSQL or MySQL without modifying business logic.

### Testing & Quality Assurance
- **Python Unittest**: Automated unit and integration test suite verifying endpoints, schemas, relationships, and error handlers.

---

## 3. Project Structure

```text
projects/
│
├── app.py                     # Application factory and server entry point
├── config.py                  # Centralized configuration (Development, Testing, Production)
├── requirements.txt           # Project dependencies
├── .env                       # Local environment variables (git-ignored)
├── .env.example               # Template environment configuration
├── .gitignore                 # Git ignore rules for Python, virtualenvs, DBs, and secrets
├── README.md                  # Comprehensive project documentation
│
├── instance/                  # Local SQLite database storage
│   └── ecommerce.db           # Relational SQLite database
│
├── logs/                      # Centralized application logs
│   └── ecommerce.log          # Application log stream
│
├── models/                    # SQLAlchemy database entities
│   ├── __init__.py            # DB instance and model exports
│   ├── user.py                # User entity (Customer & Admin roles, hashing)
│   ├── category.py            # Product category entity
│   ├── product.py             # Product entity (pricing, stock, rating, constraints)
│   ├── cart.py                # Cart and CartItem entities
│   ├── wishlist.py            # Wishlist entity with unique constraints
│   └── order.py               # Order and OrderItem entities
│
├── routes/                    # Modular Flask Blueprints (HTTP controller layer)
│   ├── __init__.py            # Blueprint registry and health check API
│   ├── auth_routes.py         # Authentication routing (/api/auth)
│   ├── product_routes.py      # Product catalog routing (/api/products)
│   ├── cart_routes.py         # Cart management routing (/api/cart)
│   ├── wishlist_routes.py     # Wishlist routing (/api/wishlist)
│   ├── order_routes.py        # Order processing routing (/api/orders)
│   └── admin_routes.py        # Admin management routing (/api/admin)
│
├── services/                  # Business logic layer (independent of HTTP routes)
│   ├── __init__.py            # Service package exports
│   ├── auth_service.py        # Registration, authentication, user queries
│   ├── product_service.py     # Product filtering, catalog queries, categories
│   ├── cart_service.py        # Cart totals, item addition, updates
│   ├── order_service.py       # Order creation, status updates, history
│   └── admin_service.py       # Dashboard statistics, analytics
│
├── utils/                     # Cross-cutting utilities
│   ├── __init__.py            # Utility package exports
│   ├── logger.py              # Centralized logging with sensitive data masking
│   ├── error_handlers.py      # Centralized error handlers (400, 401, 403, 404, 409, 500)
│   └── validators.py          # Input sanitization and validation helpers
│
├── templates/                 # Jinja2 HTML templates
│   ├── base.html              # Master layout (header, nav, toast container, footer)
│   ├── index.html             # Home page (hero section, UI state showcases, catalog preview)
│   ├── auth/                  # Authentication views
│   │   ├── login.html         # Sign in page
│   │   ├── register.html      # Sign up registration page
│   │   └── profile.html       # Customer account profile page
│   ├── admin/                 # Store administration templates
│   │   └── products.html      # Admin product management dashboard
│   ├── products/              # Customer product discovery templates (Module 4)
│   │   ├── index.html         # Product catalog page with multi-filter sidebar & grid
│   │   └── detail.html        # Product detail showcase & related recommendations
│   └── errors/                # User-friendly error pages
│       ├── 404.html           # 404 Not Found template
│       └── 500.html           # 500 Internal Server Error template
│
├── static/                    # Client-side static assets
│   ├── css/
│   │   └── style.css          # Design system stylesheet with CSS variables
│   ├── js/
│   │   └── main.js            # ApiService, toast notifications, UI event handling
│   └── images/                # Product images and branding assets
│
└── tests/                     # Automated testing suite
    ├── __init__.py            # Test package definition
    └── test_app.py            # Unit tests for app factory, DB, health check, 404, 500, models
```

---

## 4. Installation & Setup

### Step 1: Clone or Navigate to the Repository
```bash
cd projects
```

### Step 2: Create and Activate a Virtual Environment
**On Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```
**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env` and adjust secrets if desired:
```bash
cp .env.example .env
```
Default `.env` contents:
```ini
FLASK_APP=app.py
FLASK_ENV=development
DEBUG=True
SECRET_KEY=ecommerce_dev_secret_key_2026_academic_secure
DATABASE_URL=sqlite:///instance/ecommerce.db
PORT=5000
HOST=127.0.0.1
```

### Step 5: Initialize the Database
The database tables are automatically verified and created when the application starts via `db.create_all()`.

### Step 6: Run the Application
```bash
python app.py
```
Open your web browser and navigate to:
- **Web Interface:** [http://127.0.0.1:5000](http://127.0.0.1:5000)
- **API Health Endpoint:** [http://127.0.0.1:5000/api/health](http://127.0.0.1:5000/api/health)

---

## 5. Running Automated Tests

Run the test suite via Python's built-in test runner:
```bash
python -m unittest discover -s tests -v
```

All 31 comprehensive test cases will execute:
- **Module 0 Architectural Foundation (10 tests)**:
  - Application factory initialization in test mode
  - Database connectivity and schema generation for all 8 entities
  - Health API (`GET /api/health`) 200 JSON validation
  - Home page HTML rendering validation
  - Product search and category filter API validation
  - API 404 error handling (JSON response)
  - Web 404 error handling (HTML error page response)
  - 500 error handling structure and sensitive trace suppression
  - Password hashing and verification
  - Entity relationships (`User` -> `Cart` -> `CartItem` -> `Product`)
- **Module 2 Authentication & Account System (11 tests)**:
  - Seed default demo accounts (`customer@shopease.local`, `admin@shopease.local`)
  - User registration via API (`POST /api/auth/register`) with session initialization
  - Registration input validation (name, email, password strength, confirmation match)
  - Duplicate email collision rejection
  - User login via API (`POST /api/auth/login`) with credential verification
  - Invalid password and non-existent account rejection (HTTP 401)
  - User logout via API (`POST /api/auth/logout`) and session termination
  - Profile update via API (`PUT /api/auth/profile`) with session synchronization
  - Password change with current password validation and re-authentication
  - HTML authentication view rendering (`GET /register`, `GET /login`)
  - Full end-to-end HTML web flow (Register -> Auto-login -> Profile -> Update -> Sign out -> Protected redirect)
- **Module 3 Product & Category Management (10 tests)**:
  - Category CRUD operations, name uniqueness, and deletion guards
  - Product model database constraints (`price >= 0`, `stock >= 0`, integer, `is_active`)
  - Product field validation (rejects negative price, non-integer/decimal stock, missing names, invalid categories)
  - Image format validation (.jpg, .jpeg, .png, .webp) and path traversal prevention
  - Role-based authorization: admin-only product creation (`POST /api/products`) with 401/403 guards
  - Product modification and stock inventory management (`PATCH /api/products/<id>/stock`)
  - Product visibility status toggling (`PATCH /api/products/<id>/status`) and public catalog filtering
  - Product deletion with safe historical order deactivation
  - Admin Web Dashboard access control (`GET /admin/products`)
  - Admin web form product creation and deletion workflow
- **Module 4 Product Discovery & Catalog (10 tests)**:
  - Discovery Catalog page rendering (`GET /products`) with responsive multi-filter sidebar
  - Product Detail showcase rendering (`GET /products/<id>`) with specifications and 404 guard
  - Case-insensitive full-text keyword search across product name and description (`GET /api/products?q=...`)
  - Department and category filtering (`GET /api/products?category=...`)
  - Price range boundary filtering with min/max (`GET /api/products?min_price=X&max_price=Y`)
  - Availability filtering (`GET /api/products?in_stock=true`)
  - Customer rating threshold filtering (`GET /api/products?min_rating=X`)
  - Multi-attribute sorting (`price_asc`, `price_desc`, `rating_desc`, `alpha`, `newest`)
  - Recommendation engine with same-category prioritization and fallback (`GET /api/products/<id>/related`)
  - Catalog pagination support with metadata (`page`, `per_page`, `total_items`)

---

## 6. Authentication & Demo Credentials (Module 2)

ShopEase includes built-in demo credentials automatically seeded on first launch:

| Role | Email | Password | Privileges |
| :--- | :--- | :--- | :--- |
| **Customer** | `customer@shopease.local` | `Customer123!` | Standard browsing, cart, profile, and orders |
| **Admin** | `admin@shopease.local` | `Admin123!` | Administrative dashboard, catalog management |

### Important Application URLs:
- **Home / Storefront:** [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- **Product Discovery Catalog:** [http://127.0.0.1:5000/products](http://127.0.0.1:5000/products)
- **Product Detail View:** [http://127.0.0.1:5000/products/1](http://127.0.0.1:5000/products/1)
- **Admin Dashboard:** [http://127.0.0.1:5000/admin/products](http://127.0.0.1:5000/admin/products) *(Admin Only)*
- **Sign In:** [http://127.0.0.1:5000/login](http://127.0.0.1:5000/login)
- **Sign Up:** [http://127.0.0.1:5000/register](http://127.0.0.1:5000/register)
- **My Profile:** [http://127.0.0.1:5000/profile](http://127.0.0.1:5000/profile) *(Protected)*
- **Sign Out:** [http://127.0.0.1:5000/logout](http://127.0.0.1:5000/logout)

---

## 7. Product & Category Management (Module 3)

### Product REST API Endpoints:
- `GET /api/products` — Filter products by category, query, sorting, and pagination
- `GET /api/products/<id>` — Get single product details
- `POST /api/products` — *(Admin)* Create product with image upload or icon representation
- `PUT /api/products/<id>` — *(Admin)* Update product details, pricing, and stock
- `DELETE /api/products/<id>` — *(Admin)* Delete or deactivate product
- `PATCH /api/products/<id>/status` — *(Admin)* Toggle product visibility (Active/Inactive)
- `PATCH /api/products/<id>/stock` — *(Admin)* Adjust inventory quantity

### Category REST API Endpoints:
- `GET /api/products/categories` — List all categories with product counts
- `GET /api/products/categories/<id>` — Get category details
- `POST /api/products/categories` — *(Admin)* Create department category
- `PUT /api/products/categories/<id>` — *(Admin)* Update category
- `DELETE /api/products/categories/<id>` — *(Admin)* Delete empty category

---

## 8. Product Browsing, Search & Discovery (Module 4)

Module 4 provides a customer-facing product discovery experience backed dynamically by the SQLite database and REST APIs:

### Key Features:
- **Dedicated Catalog Page (`/products`)**: Dynamic two-column layout with a multi-filter sidebar and responsive product grid.
- **Dynamic Data Binding**: Loads directly from `GET /api/products` via asynchronous client fetch without hardcoded data.
- **Search System**:
  - Live navbar search with debounce, instant dropdown preview with thumbnail, rating, price, and category.
  - Dedicated catalog search bar with clear button and keyword matching.
- **Multi-Filter Engine**:
  - **Category**: Department pills with real-time active product count badges.
  - **Price Range**: Min and Max input fields + quick preset chips (Under $50, $50–$100, $100–$200, $200+).
  - **Availability**: "In Stock Only" toggle.
  - **Rating**: Star rating radios (All, 4.5★ & up, 4.0★ & up, 3.0★ & up).
- **Active Filter Chips**: Interactive chip bar showing all currently applied criteria with individual removal and "Reset All" buttons.
- **Sorting Control**: Real-time sorting by Newest, Price (Low to High, High to Low), Highest Rated, and Alphabetical (A to Z).
- **Loading & State UI**:
  - Animated CSS skeleton shimmer cards during fetch requests.
  - Graceful empty search results state with one-click filter reset.
  - Server/API error recovery state with "Retry Loading" action.
- **Dedicated Product Detail Page (`/products/<id>`)**:
  - High-resolution media showcase and verified stock availability indicators.
  - Detailed product specifications and customer rating score.
  - "You May Also Like" recommendation engine fetching contextual related products from `GET /api/products/<id>/related`.
- **Cart Preparation**: Product cards link to "View Details" (Add to Cart reserved for Module 5).

---

## 9. Development Roadmap (Modules 0 – 12)

- **[x] MODULE 0: Project Foundation & Architecture**
- **[x] MODULE 1: UI Foundation & Home Page**
- **[x] MODULE 2: Authentication (Register, Login, Logout, Sessions)**
- **[x] MODULE 3: Product Management (Admin CRUD & Categories)**
- **[x] MODULE 4: Product Browsing, Search & Filtering** *(Completed)*
- **[ ] MODULE 5: Shopping Cart** *(Next)*
- **[ ] MODULE 6: Wishlist**
- **[ ] MODULE 7: Checkout & Order Management**
- **[ ] MODULE 8: User Profile & Order History**
- **[ ] MODULE 9: Admin Dashboard (Analytics & Fulfillment)**
- **[ ] MODULE 10: Database & API Integration Review**
- **[ ] MODULE 11: Validation, Security & Error Handling**
- **[ ] MODULE 12: Testing, Optimization & Deployment**
