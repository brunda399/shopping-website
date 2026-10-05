import unittest
import json
from app import create_app
from models import db, User, Category, Product, Cart, CartItem, Wishlist, Order, OrderItem


class Module0FoundationTestCase(unittest.TestCase):
    """Test suite validating Module 0 architectural requirements."""

    def setUp(self):
        """Set up test client and initialize an in-memory database."""
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """Clean up database session and drop all tables."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_app_starts_and_configures(self):
        """Verify the Flask application initializes properly in test mode."""
        self.assertIsNotNone(self.app)
        self.assertTrue(self.app.config["TESTING"])
        self.assertEqual(self.app.config["ENV"], "testing")

    def test_database_connection_and_tables(self):
        """Verify database tables for all 8 entities exist."""
        # Querying each table to confirm ORM and database schema readiness
        self.assertEqual(User.query.count(), 0)
        self.assertEqual(Category.query.count(), 0)
        self.assertEqual(Product.query.count(), 0)
        self.assertEqual(Cart.query.count(), 0)
        self.assertEqual(CartItem.query.count(), 0)
        self.assertEqual(Wishlist.query.count(), 0)
        self.assertEqual(Order.query.count(), 0)
        self.assertEqual(OrderItem.query.count(), 0)

    def test_health_api_endpoint(self):
        """Verify GET /api/health responds with 200 and expected JSON structure."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/json")
        
        data = response.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("message"), "E-Commerce API is running")

    def test_home_page_renders_successfully(self):
        """Verify GET / returns 200 HTML page with ShopEase branding."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ShopEase", response.data)
        self.assertIn(b"Smart, Reliable &amp; Effortless", response.data)

    def test_product_search_and_filter_api(self):
        """Verify GET /api/products supports category filtering and keyword search."""
        # Create category and product
        cat = Category(name="Electronics", description="Audio and gear")
        db.session.add(cat)
        db.session.flush()

        prod1 = Product(name="Noise-Cancelling Headphones Pro", price=129.99, category_id=cat.id, stock=10)
        prod2 = Product(name="Running Shoes", price=69.99, category_id=cat.id, stock=15)
        db.session.add_all([prod1, prod2])
        db.session.commit()

        # Query all products
        res_all = self.client.get("/api/products")
        self.assertEqual(res_all.status_code, 200)
        data_all = res_all.get_json()
        self.assertEqual(data_all["count"], 2)

        # Query with keyword search
        res_search = self.client.get("/api/products?q=Headphones")
        self.assertEqual(res_search.status_code, 200)
        data_search = res_search.get_json()
        self.assertEqual(data_search["count"], 1)
        self.assertIn("Headphones", data_search["data"][0]["name"])

        # Query with category_id filter
        res_cat = self.client.get(f"/api/products?category_id={cat.id}")
        self.assertEqual(res_cat.status_code, 200)
        data_cat = res_cat.get_json()
        self.assertEqual(data_cat["count"], 2)


    def test_404_error_handling_api(self):
        """Verify 404 on API route returns structured JSON."""
        response = self.client.get("/api/non-existent-route")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, "application/json")
        
        data = response.get_json()
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("error", {}).get("code"), 404)

    def test_404_error_handling_html(self):
        """Verify 404 on web route returns user-friendly HTML error page."""
        response = self.client.get("/non-existent-page")
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"Page Not Found", response.data)

    def test_user_password_hashing(self):
        """Verify secure password hashing and verification."""
        user = User(name="Test Customer", email="customer@example.com")
        user.set_password("SecurePassword123!")
        
        db.session.add(user)
        db.session.commit()

        # Plain text must not match stored hash directly
        self.assertNotEqual(user.password_hash, "SecurePassword123!")
        # Correct password must verify
        self.assertTrue(user.check_password("SecurePassword123!"))
        # Incorrect password must fail
        self.assertFalse(user.check_password("WrongPassword"))
        # Serialization must omit password_hash
        user_dict = user.to_dict()
        self.assertNotIn("password_hash", user_dict)
        self.assertEqual(user_dict["email"], "customer@example.com")

    def test_database_relationships_cart_and_items(self):
        """Verify User -> Cart -> CartItem -> Product relationship integrity."""
        # Create category & product
        category = Category(name="Electronics", description="Gadgets and tech")
        db.session.add(category)
        db.session.flush()

        product = Product(
            name="Wireless Earbuds",
            description="High quality sound",
            price=49.99,
            category_id=category.id,
            stock=100,
        )
        db.session.add(product)
        
        # Create user
        user = User(name="Jane Doe", email="jane@example.com")
        user.set_password("Password123")
        db.session.add(user)
        db.session.flush()

        # Create cart and cart item
        cart = Cart(user_id=user.id)
        db.session.add(cart)
        db.session.flush()

        cart_item = CartItem(cart_id=cart.id, product_id=product.id, quantity=2)
        db.session.add(cart_item)
        db.session.commit()

        # Query back
        saved_user = User.query.filter_by(email="jane@example.com").first()
        self.assertIsNotNone(saved_user.cart)
        self.assertEqual(saved_user.cart.items.count(), 1)
        item = saved_user.cart.items.first()
        self.assertEqual(item.product.name, "Wireless Earbuds")
        self.assertEqual(item.to_dict()["subtotal"], 99.98)

    def test_500_error_handler_structure(self):
        """Verify 500 internal server error handler structure and safe responses."""
        # 500 error handler exists in app error handlers
        self.assertIn(500, self.app.error_handler_spec[None])
        handler = self.app.error_handler_spec[None][500]
        self.assertIsNotNone(handler)

        # Test API response under 500 handler
        with self.app.test_request_context("/api/test-error", headers={"Accept": "application/json"}):
            handler_func = list(handler.values())[0] if isinstance(handler, dict) else handler
            response, status_code = handler_func(Exception("Simulated unexpected failure"))
            self.assertEqual(status_code, 500)
            data = json.loads(response.get_data(as_text=True))
            self.assertFalse(data["success"])
            self.assertEqual(data["error"]["code"], 500)
            # Ensure internal exception trace is not exposed
            self.assertNotIn("Simulated unexpected failure", data["error"]["message"])


class Module2AuthenticationTestCase(unittest.TestCase):
    """Test suite validating Module 2 User Authentication & Account System requirements."""

    def setUp(self):
        """Initialize test client with isolated in-memory SQLite database."""
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """Clean up database session and drop tables."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_seed_default_users(self):
        """Verify seeding creates customer and admin users with valid password hashes."""
        from services.auth_service import AuthService
        seeded = AuthService.seed_default_users()
        self.assertGreaterEqual(len(seeded), 2)

        # Verify customer
        cust = User.query.filter_by(email="customer@shopease.local").first()
        self.assertIsNotNone(cust)
        self.assertEqual(cust.role, User.ROLE_USER)
        self.assertTrue(cust.check_password("Customer123!"))

        # Verify admin
        admin = User.query.filter_by(email="admin@shopease.local").first()
        self.assertIsNotNone(admin)
        self.assertEqual(admin.role, User.ROLE_ADMIN)
        self.assertTrue(admin.is_admin)
        self.assertTrue(admin.check_password("Admin123!"))

    def test_api_register_success(self):
        """Verify POST /api/auth/register creates user, establishes session, returns 201."""
        payload = {
            "name": "Sarah Connor",
            "email": "sarah@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "phone": "+1 555-0199"
        }
        res = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["email"], "sarah@example.com")
        self.assertEqual(data["data"]["name"], "Sarah Connor")
        self.assertNotIn("password_hash", data["data"])

        # Check user exists in database
        user = User.query.filter_by(email="sarah@example.com").first()
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password("Password123!"))

        # Check session is active
        status_res = self.client.get("/api/auth/status")
        status_data = status_res.get_json()
        self.assertTrue(status_data["is_authenticated"])
        self.assertEqual(status_data["user_name"], "Sarah Connor")

    def test_api_register_validation_errors(self):
        """Verify registration rejects invalid inputs with HTTP 400 and clear error messages."""
        # 1. Missing name
        res = self.client.post("/api/auth/register", json={
            "name": "",
            "email": "test@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!"
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("Name is required", res.get_json()["error"]["message"])

        # 2. Invalid email format
        res = self.client.post("/api/auth/register", json={
            "name": "Test User",
            "email": "not-an-email",
            "password": "Password123!",
            "confirm_password": "Password123!"
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("valid email", res.get_json()["error"]["message"].lower())

        # 3. Short password
        res = self.client.post("/api/auth/register", json={
            "name": "Test User",
            "email": "valid@example.com",
            "password": "123",
            "confirm_password": "123"
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("at least 6 characters", res.get_json()["error"]["message"])

        # 4. Mismatched passwords
        res = self.client.post("/api/auth/register", json={
            "name": "Test User",
            "email": "valid@example.com",
            "password": "Password123!",
            "confirm_password": "DifferentPassword!"
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("do not match", res.get_json()["error"]["message"].lower())

    def test_api_register_duplicate_email(self):
        """Verify registering with an existing email returns 400."""
        from services.auth_service import AuthService
        AuthService.register_user("Alice", "alice@example.com", "Password123!", "Password123!")

        res = self.client.post("/api/auth/register", json={
            "name": "Alice Duplicate",
            "email": "alice@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!"
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("already exists", res.get_json()["error"]["message"])

    def test_api_login_success(self):
        """Verify POST /api/auth/login authenticates valid credentials."""
        from services.auth_service import AuthService
        AuthService.register_user("Bob Smith", "bob@example.com", "SecretPass123!", "SecretPass123!")

        res = self.client.post("/api/auth/login", json={
            "email": "bob@example.com",
            "password": "SecretPass123!"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["email"], "bob@example.com")
        self.assertEqual(data["data"]["name"], "Bob Smith")

        # Verify /api/auth/me returns current user
        me_res = self.client.get("/api/auth/me")
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.get_json()["data"]["email"], "bob@example.com")

    def test_api_login_invalid_credentials(self):
        """Verify login fails with HTTP 401 for wrong password or unknown email."""
        from services.auth_service import AuthService
        AuthService.register_user("Charlie", "charlie@example.com", "SecretPass123!", "SecretPass123!")

        # Incorrect password
        res = self.client.post("/api/auth/login", json={
            "email": "charlie@example.com",
            "password": "WrongPassword!"
        })
        self.assertEqual(res.status_code, 401)
        self.assertIn("Invalid email or password", res.get_json()["error"]["message"])

        # Non-existent email
        res_nonexistent = self.client.post("/api/auth/login", json={
            "email": "nobody@example.com",
            "password": "AnyPassword"
        })
        self.assertEqual(res_nonexistent.status_code, 401)

    def test_api_logout(self):
        """Verify POST /api/auth/logout clears active session."""
        from services.auth_service import AuthService
        AuthService.register_user("David", "david@example.com", "Pass123456", "Pass123456")

        self.client.post("/api/auth/login", json={"email": "david@example.com", "password": "Pass123456"})
        
        # Verify active
        self.assertTrue(self.client.get("/api/auth/status").get_json()["is_authenticated"])

        # Logout
        logout_res = self.client.post("/api/auth/logout")
        self.assertEqual(logout_res.status_code, 200)

        # Verify inactive
        self.assertFalse(self.client.get("/api/auth/status").get_json()["is_authenticated"])
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_api_update_profile(self):
        """Verify PUT /api/auth/profile updates user details."""
        from services.auth_service import AuthService
        AuthService.register_user("Emma", "emma@example.com", "Pass123456", "Pass123456")
        self.client.post("/api/auth/login", json={"email": "emma@example.com", "password": "Pass123456"})

        update_res = self.client.put("/api/auth/profile", json={
            "name": "Emma Watson",
            "phone": "+1 555-9876"
        })
        self.assertEqual(update_res.status_code, 200)
        data = update_res.get_json()
        self.assertEqual(data["data"]["name"], "Emma Watson")
        self.assertEqual(data["data"]["phone"], "+1 555-9876")

        # Verify persisted in database
        updated_user = User.query.filter_by(email="emma@example.com").first()
        self.assertEqual(updated_user.name, "Emma Watson")
        self.assertEqual(updated_user.phone, "+1 555-9876")

    def test_api_change_password(self):
        """Verify password change requires valid current password and updates hash."""
        from services.auth_service import AuthService
        AuthService.register_user("Frank", "frank@example.com", "OldPassword1!", "OldPassword1!")
        self.client.post("/api/auth/login", json={"email": "frank@example.com", "password": "OldPassword1!"})

        # Incorrect current password
        bad_change = self.client.put("/api/auth/change-password", json={
            "current_password": "WrongCurrentPassword",
            "new_password": "NewPassword2!",
            "confirm_password": "NewPassword2!"
        })
        self.assertEqual(bad_change.status_code, 400)
        self.assertIn("Current password is incorrect", bad_change.get_json()["error"]["message"])

        # Correct change
        good_change = self.client.put("/api/auth/change-password", json={
            "current_password": "OldPassword1!",
            "new_password": "NewPassword2!",
            "confirm_password": "NewPassword2!"
        })
        self.assertEqual(good_change.status_code, 200)

        # Verify old password fails
        self.client.post("/api/auth/logout")
        fail_login = self.client.post("/api/auth/login", json={
            "email": "frank@example.com",
            "password": "OldPassword1!"
        })
        self.assertEqual(fail_login.status_code, 401)

        # Verify new password succeeds
        pass_login = self.client.post("/api/auth/login", json={
            "email": "frank@example.com",
            "password": "NewPassword2!"
        })
        self.assertEqual(pass_login.status_code, 200)

    def test_html_views_registration_and_login(self):
        """Verify GET /register and GET /login render HTML forms."""
        reg_page = self.client.get("/register")
        self.assertEqual(reg_page.status_code, 200)
        self.assertIn(b"Create Your Account", reg_page.data)
        self.assertIn(b"Confirm Password", reg_page.data)

        login_page = self.client.get("/login")
        self.assertEqual(login_page.status_code, 200)
        self.assertIn(b"Welcome Back", login_page.data)
        self.assertIn(b"Remember me on this device", login_page.data)

    def test_html_form_registration_and_login_flow(self):
        """Verify HTML form POST for registration, login, profile view and logout."""
        # 1. Register via form
        post_reg = self.client.post("/register", data={
            "name": "Grace Hopper",
            "email": "grace@example.com",
            "password": "Compiler1952!",
            "confirm_password": "Compiler1952!",
            "phone": "555-0100"
        }, follow_redirects=True)
        self.assertEqual(post_reg.status_code, 200)
        self.assertIn(b"Grace", post_reg.data)

        # 2. View profile
        profile_res = self.client.get("/profile")
        self.assertEqual(profile_res.status_code, 200)
        self.assertIn(b"Grace Hopper", profile_res.data)
        self.assertIn(b"grace@example.com", profile_res.data)

        # 3. Update profile via form
        post_profile = self.client.post("/profile", data={
            "action": "update_profile",
            "name": "Admiral Grace Hopper",
            "phone": "555-0200"
        }, follow_redirects=True)
        self.assertEqual(post_profile.status_code, 200)
        self.assertIn(b"Admiral Grace Hopper", post_profile.data)

        # 4. Logout via link
        logout_res = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(logout_res.status_code, 200)
        self.assertIn(b"signed out successfully", logout_res.data)

        # 5. Profile should now redirect to login
        unauth_profile = self.client.get("/profile", follow_redirects=False)
        self.assertEqual(unauth_profile.status_code, 302)
        self.assertIn("/login", unauth_profile.location)


class Module3ProductManagementTestCase(unittest.TestCase):
    """Test suite validating Module 3 Product & Category Management requirements."""

    def setUp(self):
        """Set up test client, isolated database, and seed initial demo accounts/categories."""
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed categories
        from services.product_service import ProductService
        from services.auth_service import AuthService
        ProductService.seed_initial_data()
        AuthService.seed_default_users()

    def tearDown(self):
        """Clean up database session and drop tables."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _login_as_admin(self):
        """Helper to establish an admin session."""
        return self.client.post("/api/auth/login", json={
            "email": "admin@shopease.local",
            "password": "Admin123!"
        })

    def _login_as_customer(self):
        """Helper to establish a regular customer session."""
        return self.client.post("/api/auth/login", json={
            "email": "customer@shopease.local",
            "password": "Customer123!"
        })

    def test_category_crud_and_validation(self):
        """Verify Category CRUD operations, uniqueness, and deletion guards."""
        from services.product_service import ProductService

        # 1. Create Category
        success, msg, cat = ProductService.create_category("Smart Wearables", "Wearable sensors and trackers")
        self.assertTrue(success)
        self.assertEqual(cat["name"], "Smart Wearables")

        # 2. Duplicate Category rejection
        dup_success, dup_msg, _ = ProductService.create_category("Smart Wearables", "Another one")
        self.assertFalse(dup_success)
        self.assertIn("already exists", dup_msg.lower())

        # 3. Empty name rejection
        empty_success, empty_msg, _ = ProductService.create_category("", "No name")
        self.assertFalse(empty_success)
        self.assertIn("required", empty_msg.lower())

        # 4. Update Category
        upd_success, upd_msg, upd_cat = ProductService.update_category(cat["id"], "Smart Wearables Pro", "Updated desc")
        self.assertTrue(upd_success)
        self.assertEqual(upd_cat["name"], "Smart Wearables Pro")

        # 5. Delete empty category
        del_success, del_msg = ProductService.delete_category(cat["id"])
        self.assertTrue(del_success)
        self.assertIsNone(ProductService.get_category_by_id(cat["id"]))

    def test_product_model_constraints_and_defaults(self):
        """Verify product model defaults (is_active=True) and database constraints."""
        from services.product_service import ProductService
        cat = Category.query.first()
        self.assertIsNotNone(cat)

        success, msg, prod = ProductService.create_product(
            name="Mechanical Keyboard RGB",
            category_id=cat.id,
            price=89.99,
            stock=15,
            description="Hot-swappable tactile switches with RGB lighting",
            image="⌨️"
        )
        self.assertTrue(success)
        self.assertTrue(prod["is_active"])
        self.assertTrue(prod["is_in_stock"])
        self.assertEqual(prod["stock_status"], "in_stock")
        self.assertEqual(prod["price"], 89.99)
        self.assertEqual(prod["stock"], 15)

    def test_product_validation_rules(self):
        """Verify validation rejects negative price, non-integer stock, and missing name."""
        from services.product_service import ProductService
        cat = Category.query.first()

        # 1. Empty name
        s, err, _ = ProductService.create_product("", cat.id, 29.99, 10)
        self.assertFalse(s)
        self.assertIn("name is required", err.lower())

        # 2. Negative price
        s, err, _ = ProductService.create_product("Test Item", cat.id, -10.50, 10)
        self.assertFalse(s)
        self.assertIn("cannot be negative", err.lower())

        # 3. Invalid non-numeric price string
        s, err, _ = ProductService.create_product("Test Item", cat.id, "not-a-price", 10)
        self.assertFalse(s)
        self.assertIn("valid number", err.lower())

        # 4. Negative stock
        s, err, _ = ProductService.create_product("Test Item", cat.id, 29.99, -5)
        self.assertFalse(s)
        self.assertIn("cannot be negative", err.lower())

        # 5. Non-integer decimal stock e.g. 10.5
        s, err, _ = ProductService.create_product("Test Item", cat.id, 29.99, "10.5")
        self.assertFalse(s)
        self.assertIn("whole integer", err.lower())

        # 6. Invalid category ID
        s, err, _ = ProductService.create_product("Test Item", 99999, 29.99, 10)
        self.assertFalse(s)
        self.assertIn("does not exist", err.lower())

    def test_product_image_validation_and_filename_sanitization(self):
        """Verify image format restrictions, path traversal prevention, and unique filename generation."""
        from utils.validators import validate_image_file, generate_secure_image_filename

        # Valid image formats
        for ext in ("test.jpg", "pic.jpeg", "banner.png", "asset.webp"):
            valid, _ = validate_image_file(ext)
            self.assertTrue(valid)

        # Invalid formats
        for ext in ("malicious.exe", "script.py", "payload.sh", "doc.pdf", "archive.zip"):
            valid, err = validate_image_file(ext)
            self.assertFalse(valid)
            self.assertIn("Invalid image format", err)

        # Path traversal prevention
        secure_name = generate_secure_image_filename("../../etc/passwd.png")
        self.assertNotIn("..", secure_name)
        self.assertNotIn("/", secure_name)
        self.assertNotIn("\\", secure_name)
        self.assertTrue(secure_name.startswith("prod_"))
        self.assertTrue(secure_name.endswith(".png"))

    def test_api_product_creation_rbac(self):
        """Verify only administrators can create products via POST /api/products."""
        cat = Category.query.first()
        payload = {
            "name": "Smart Security Camera",
            "category_id": cat.id,
            "price": 59.99,
            "stock": 20,
            "description": "1080p night vision security camera",
            "image": "📹"
        }

        # 1. Unauthenticated request -> 401
        res_unauth = self.client.post("/api/products", json=payload)
        self.assertEqual(res_unauth.status_code, 401)

        # 2. Customer request -> 403 Forbidden
        self._login_as_customer()
        res_customer = self.client.post("/api/products", json=payload)
        self.assertEqual(res_customer.status_code, 403)
        self.client.post("/api/auth/logout")

        # 3. Admin request -> 201 Created
        self._login_as_admin()
        res_admin = self.client.post("/api/products", json=payload)
        self.assertEqual(res_admin.status_code, 201)
        data = res_admin.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["name"], "Smart Security Camera")
        self.assertEqual(data["data"]["price"], 59.99)
        self.assertEqual(data["data"]["stock"], 20)

    def test_api_product_update_and_stock_management(self):
        """Verify admin can update product attributes and inventory quantity."""
        self._login_as_admin()
        prod = Product.query.first()

        # Update product price and description
        res_update = self.client.put(f"/api/products/{prod.id}", json={
            "price": 149.99,
            "description": "Updated premium specification description"
        })
        self.assertEqual(res_update.status_code, 200)
        data_upd = res_update.get_json()
        self.assertEqual(data_upd["data"]["price"], 149.99)

        # Update stock quantity via stock endpoint
        res_stock = self.client.patch(f"/api/products/{prod.id}/stock", json={"stock": 3})
        self.assertEqual(res_stock.status_code, 200)
        data_stock = res_stock.get_json()
        self.assertEqual(data_stock["data"]["stock"], 3)
        self.assertEqual(data_stock["data"]["stock_status"], "low_stock")

    def test_api_product_status_toggle_and_catalog_filtering(self):
        """Verify deactivating a product hides it from public storefront while visible to admin."""
        self._login_as_admin()
        prod = Product.query.first()
        prod_id = prod.id

        # Toggle status to inactive
        res_toggle = self.client.patch(f"/api/products/{prod_id}/status")
        self.assertEqual(res_toggle.status_code, 200)
        data = res_toggle.get_json()
        self.assertFalse(data["data"]["is_active"])

        # Public storefront query: should NOT include the deactivated product
        self.client.post("/api/auth/logout")
        res_public = self.client.get("/api/products")
        self.assertEqual(res_public.status_code, 200)
        public_ids = [p["id"] for p in res_public.get_json()["data"]]
        self.assertNotIn(prod_id, public_ids)

        # Direct public single product query returns 404
        res_single = self.client.get(f"/api/products/{prod_id}")
        self.assertEqual(res_single.status_code, 404)

        # Admin query with include_inactive=true DOES include the deactivated product
        self._login_as_admin()
        res_admin = self.client.get("/api/products?include_inactive=true")
        self.assertEqual(res_admin.status_code, 200)
        admin_ids = [p["id"] for p in res_admin.get_json()["data"]]
        self.assertIn(prod_id, admin_ids)

    def test_api_product_deletion(self):
        """Verify admin can delete a product without order dependencies."""
        self._login_as_admin()
        cat = Category.query.first()

        # Create temporary product
        from services.product_service import ProductService
        _, _, temp_prod = ProductService.create_product(
            name="Temporary Test Gadget",
            category_id=cat.id,
            price=19.99,
            stock=5
        )

        # Delete product
        res_del = self.client.delete(f"/api/products/{temp_prod['id']}")
        self.assertEqual(res_del.status_code, 200)
        self.assertTrue(res_del.get_json()["success"])

        # Verify not found
        res_check = self.client.get(f"/api/products/{temp_prod['id']}")
        self.assertEqual(res_check.status_code, 404)

    def test_admin_web_dashboard_access_and_rendering(self):
        """Verify GET /admin/products renders dashboard for admins and restricts non-admins."""
        # 1. Unauthenticated -> redirects to login
        res_unauth = self.client.get("/admin/products", follow_redirects=False)
        self.assertEqual(res_unauth.status_code, 302)
        self.assertIn("/login", res_unauth.location)

        # 2. Customer login -> redirected to home
        self._login_as_customer()
        res_cust = self.client.get("/admin/products", follow_redirects=False)
        self.assertEqual(res_cust.status_code, 302)
        self.assertEqual(res_cust.location, "/")
        self.client.post("/api/auth/logout")

        # 3. Admin login -> 200 OK with dashboard table, modals, and KPI counters
        self._login_as_admin()
        res_admin = self.client.get("/admin/products")
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn(b"Product &amp; Category Management", res_admin.data)
        self.assertIn(b"Total Products", res_admin.data)
        self.assertIn(b"Add New Product", res_admin.data)
        self.assertIn(b"admin-products-table", res_admin.data)

    def test_admin_web_form_create_and_delete_flow(self):
        """Verify creating and deleting a product via admin web form submissions."""
        self._login_as_admin()
        cat = Category.query.first()

        # Post create form
        create_res = self.client.post("/admin/products/create", data={
            "name": "Web Form Studio Microphone",
            "category_id": cat.id,
            "price": "75.00",
            "stock": "12",
            "description": "Studio condenser USB microphone with pop filter",
            "image_url": "🎙️",
            "is_active": "1"
        }, follow_redirects=True)

        self.assertEqual(create_res.status_code, 200)
        self.assertIn(b"Web Form Studio Microphone", create_res.data)

        # Find created product
        prod = Product.query.filter_by(name="Web Form Studio Microphone").first()
        self.assertIsNotNone(prod)

        # Post delete form
        delete_res = self.client.post(f"/admin/products/{prod.id}/delete", follow_redirects=True)
        self.assertEqual(delete_res.status_code, 200)
        self.assertIn(b"deleted successfully", delete_res.data.lower())


class Module4ProductDiscoveryTestCase(unittest.TestCase):
    """Test suite validating Module 4 Product Browsing, Search, Filtering, Sorting & Discovery."""

    def setUp(self):
        """Set up test client, isolated database, and seed initial demo catalog."""
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        from services.product_service import ProductService
        ProductService.seed_initial_data()

    def tearDown(self):
        """Clean up database session and drop tables."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_catalog_html_page_rendering(self):
        """Verify GET /products renders discovery catalog page with all UI controls."""
        res = self.client.get("/products")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"ShopEase", res.data)
        self.assertIn(b"Products", res.data)
        self.assertIn(b"catalog-search-input", res.data)
        self.assertIn(b"sidebar-category-list", res.data)
        self.assertIn(b"catalog-sort-select", res.data)
        self.assertIn(b"catalog-product-grid", res.data)
        self.assertIn(b"active-filter-chips", res.data)
        self.assertIn(b"btn-sidebar-reset", res.data)

    def test_product_detail_page_rendering_and_404(self):
        """Verify GET /products/<id> renders product detail page, and non-existent IDs return 404."""
        prod = Product.query.first()
        self.assertIsNotNone(prod)

        res = self.client.get(f"/products/{prod.id}")
        self.assertEqual(res.status_code, 200)
        self.assertIn(prod.name.encode(), res.data)
        self.assertIn(b"In Stock", res.data)
        self.assertIn(b"Product Details &amp; Specifications", res.data)
        self.assertIn(b"You May Also Like", res.data)

        # Non-existent product ID
        res_404 = self.client.get("/products/999999")
        self.assertEqual(res_404.status_code, 404)

    def test_api_products_text_search(self):
        """Verify GET /api/products?q=... performs keyword matching in product name and description."""
        res = self.client.get("/api/products?q=wireless")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertGreaterEqual(len(data.get("data", [])), 1)

        for item in data["data"]:
            match = ("wireless" in item["name"].lower()) or ("wireless" in (item.get("description") or "").lower())
            self.assertTrue(match)

        # Unmatched query returns empty results
        res_empty = self.client.get("/api/products?q=nonexistentxyzitem999")
        self.assertEqual(res_empty.status_code, 200)
        empty_data = res_empty.get_json()
        self.assertEqual(len(empty_data.get("data", [])), 0)

    def test_api_products_category_filtering(self):
        """Verify GET /api/products?category=... filters products by category name."""
        res = self.client.get("/api/products?category=Electronics")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertGreaterEqual(len(data.get("data", [])), 1)

        for item in data["data"]:
            self.assertEqual(item["category_name"], "Electronics")

    def test_api_products_price_range_filtering(self):
        """Verify GET /api/products?min_price=X&max_price=Y filters within price boundaries."""
        res = self.client.get("/api/products?min_price=50&max_price=150")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertGreaterEqual(len(data.get("data", [])), 1)

        for item in data["data"]:
            self.assertGreaterEqual(item["price"], 50.0)
            self.assertLessEqual(item["price"], 150.0)

    def test_api_products_in_stock_filtering(self):
        """Verify GET /api/products?in_stock=true excludes out-of-stock items."""
        # Force one product out of stock
        prod = Product.query.first()
        prod.stock = 0
        db.session.commit()

        res = self.client.get("/api/products?in_stock=true")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))

        for item in data["data"]:
            self.assertGreater(item["stock"], 0)
            self.assertNotEqual(item["id"], prod.id)

    def test_api_products_rating_filtering(self):
        """Verify GET /api/products?min_rating=4.5 returns products meeting rating threshold."""
        res = self.client.get("/api/products?min_rating=4.5")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))

        for item in data["data"]:
            self.assertGreaterEqual(item["rating"], 4.5)

    def test_api_products_sorting_options(self):
        """Verify GET /api/products?sort_by=... correctly orders returned products."""
        # Price ascending
        res_asc = self.client.get("/api/products?sort_by=price_asc")
        prices_asc = [p["price"] for p in res_asc.get_json()["data"]]
        self.assertEqual(prices_asc, sorted(prices_asc))

        # Price descending
        res_desc = self.client.get("/api/products?sort_by=price_desc")
        prices_desc = [p["price"] for p in res_desc.get_json()["data"]]
        self.assertEqual(prices_desc, sorted(prices_desc, reverse=True))

        # Rating descending
        res_rating = self.client.get("/api/products?sort_by=rating_desc")
        ratings = [p["rating"] for p in res_rating.get_json()["data"]]
        self.assertEqual(ratings, sorted(ratings, reverse=True))

        # Alphabetical
        res_alpha = self.client.get("/api/products?sort_by=alpha")
        names = [p["name"].lower() for p in res_alpha.get_json()["data"]]
        self.assertEqual(names, sorted(names))

    def test_api_related_products_recommendations(self):
        """Verify GET /api/products/<id>/related returns recommendations from same category."""
        prod = Product.query.first()
        self.assertIsNotNone(prod)

        res = self.client.get(f"/api/products/{prod.id}/related")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        items = data.get("data", [])
        self.assertGreater(len(items), 0)

        for item in items:
            self.assertNotEqual(item["id"], prod.id)

        # The first recommended item should match the same category
        if prod.category_id:
            same_cat_items = [i for i in items if i["category_id"] == prod.category_id]
            self.assertGreaterEqual(len(same_cat_items), 1)

    def test_api_products_pagination(self):
        """Verify GET /api/products with page and per_page pagination parameters."""
        res = self.client.get("/api/products?page=1&per_page=3")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(len(data.get("data", [])), 3)
        self.assertIn("pagination", data)
        self.assertEqual(data["pagination"]["page"], 1)
        self.assertEqual(data["pagination"]["per_page"], 3)


class Module5ShoppingCartTestCase(unittest.TestCase):
    """Test suite validating Module 5 Shopping Cart System requirements."""

    def setUp(self):
        """Set up test client, in-memory SQLite database, and seed data."""
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed categories
        self.cat = Category(name="Electronics", description="Gadgets and tech")
        db.session.add(self.cat)
        db.session.flush()

        # Seed products
        self.prod1 = Product(
            name="Wireless Noise-Canceling Headphones",
            description="Premium audio",
            price=120.00,
            stock=10,
            category_id=self.cat.id,
            image="🎧",
            is_active=True
        )
        self.prod2 = Product(
            name="Smartphone Fast Charger Cable",
            description="Durable braided cable",
            price=15.00,
            stock=25,
            category_id=self.cat.id,
            image="🔌",
            is_active=True
        )
        self.prod_out_of_stock = Product(
            name="Limited Edition Smart Watch",
            description="Sold out item",
            price=250.00,
            stock=0,
            category_id=self.cat.id,
            image="⌚",
            is_active=True
        )
        self.prod_inactive = Product(
            name="Discontinued Item",
            description="No longer sold",
            price=50.00,
            stock=5,
            category_id=self.cat.id,
            image="📦",
            is_active=False
        )

        # Seed test user
        self.user = User(
            name="Cart Tester",
            email="carttester@example.com",
            role=User.ROLE_USER
        )
        self.user.set_password("Secret123!")

        db.session.add_all([self.prod1, self.prod2, self.prod_out_of_stock, self.prod_inactive, self.user])
        db.session.commit()

    def tearDown(self):
        """Clean up database session and drop all tables."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _login(self):
        """Helper to establish an authenticated session for self.user."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["user_name"] = self.user.name
            sess["user_email"] = self.user.email
            sess["user_role"] = self.user.role

    def test_cart_status_endpoint(self):
        """Verify GET /api/cart/status returns 200 and operational health message."""
        res = self.client.get("/api/cart/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("Module 5 Active", data.get("message"))

    def test_cart_html_page_renders_successfully(self):
        """Verify GET /cart returns 200 with complete cart view and summary elements."""
        res = self.client.get("/cart")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Shopping Bag", res.data)
        self.assertIn(b"Order Summary", res.data)
        self.assertIn(b"Have a Promo Code?", res.data)

    def test_api_cart_empty_state(self):
        """Verify GET /api/cart for guest returns 0 items and 0 subtotal."""
        res = self.client.get("/api/cart")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        cart = data.get("data", {})
        self.assertEqual(cart.get("items_count"), 0)
        self.assertEqual(cart.get("total_quantity"), 0)
        self.assertEqual(cart.get("subtotal"), 0.0)
        self.assertEqual(cart.get("total"), 0.0)

    def test_guest_add_to_cart_success(self):
        """Verify POST /api/cart/items succeeds for valid product and quantity within stock."""
        res = self.client.post("/api/cart/items", json={
            "product_id": self.prod1.id,
            "quantity": 2
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["data"]["product_id"], self.prod1.id)
        self.assertEqual(data["data"]["quantity"], 2)
        self.assertEqual(data["data"]["subtotal"], 240.00)

    def test_guest_add_to_cart_exceeds_stock(self):
        """Verify POST /api/cart/items rejects quantity exceeding available inventory."""
        res = self.client.post("/api/cart/items", json={
            "product_id": self.prod1.id,
            "quantity": 999
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data.get("success"))
        self.assertIn("units in stock", data["error"]["message"])

    def test_guest_add_to_cart_out_of_stock_and_inactive(self):
        """Verify adding out-of-stock or inactive products is rejected."""
        # Out of stock
        res_oos = self.client.post("/api/cart/items", json={
            "product_id": self.prod_out_of_stock.id,
            "quantity": 1
        })
        self.assertEqual(res_oos.status_code, 400)
        self.assertIn("out of stock", res_oos.get_json()["error"]["message"])

        # Inactive product
        res_inact = self.client.post("/api/cart/items", json={
            "product_id": self.prod_inactive.id,
            "quantity": 1
        })
        self.assertEqual(res_inact.status_code, 404)

    def test_authenticated_user_cart_crud_lifecycle(self):
        """Verify end-to-end cart lifecycle: add, view, update quantity, remove item."""
        self._login()

        # 1. Add item
        res_add = self.client.post("/api/cart/items", json={
            "product_id": self.prod2.id,
            "quantity": 2
        })
        self.assertEqual(res_add.status_code, 200)
        self.assertEqual(res_add.get_json()["data"]["quantity"], 2)

        # 2. View cart
        res_view = self.client.get("/api/cart")
        self.assertEqual(res_view.status_code, 200)
        cart_data = res_view.get_json()["data"]
        self.assertEqual(cart_data["items_count"], 1)
        self.assertEqual(cart_data["total_quantity"], 2)
        self.assertEqual(cart_data["subtotal"], 30.00)
        # Subtotal < 50 => shipping = 5.00
        self.assertEqual(cart_data["shipping"], 5.00)
        self.assertEqual(cart_data["total"], 35.00)

        # 3. Update quantity
        res_upd = self.client.put(f"/api/cart/items/{self.prod2.id}", json={
            "quantity": 5
        })
        self.assertEqual(res_upd.status_code, 200)
        cart_upd = res_upd.get_json()["cart"]
        self.assertEqual(cart_upd["total_quantity"], 5)
        self.assertEqual(cart_upd["subtotal"], 75.00)
        # Subtotal >= 50 => free shipping!
        self.assertEqual(cart_upd["shipping"], 0.0)
        self.assertTrue(cart_upd["free_shipping_eligible"])

        # 4. Remove item
        res_del = self.client.delete(f"/api/cart/items/{self.prod2.id}")
        self.assertEqual(res_del.status_code, 200)
        self.assertEqual(res_del.get_json()["cart"]["items_count"], 0)

    def test_clear_cart(self):
        """Verify DELETE /api/cart empties all items from user cart."""
        self._login()
        self.client.post("/api/cart/items", json={"product_id": self.prod1.id, "quantity": 1})
        self.client.post("/api/cart/items", json={"product_id": self.prod2.id, "quantity": 1})

        # Clear cart
        res_clear = self.client.delete("/api/cart")
        self.assertEqual(res_clear.status_code, 200)
        self.assertEqual(res_clear.get_json()["cart"]["items_count"], 0)

        # Verify DB is clean
        res_get = self.client.get("/api/cart")
        self.assertEqual(res_get.get_json()["data"]["items_count"], 0)

    def test_promotional_coupon_application_and_removal(self):
        """Verify valid coupon codes apply discount, invalid codes fail, and deletion removes discount."""
        self._login()
        # Add prod1 ($120.00)
        self.client.post("/api/cart/items", json={"product_id": self.prod1.id, "quantity": 1})

        # Apply invalid coupon
        res_invalid = self.client.post("/api/cart/coupon", json={"coupon_code": "INVALID_CODE"})
        self.assertEqual(res_invalid.status_code, 400)

        # Apply EASE50 (50% off capped at $50)
        res_ease50 = self.client.post("/api/cart/coupon", json={"coupon_code": "EASE50"})
        self.assertEqual(res_ease50.status_code, 200)
        coupon_data = res_ease50.get_json()["data"]
        self.assertEqual(coupon_data["code"], "EASE50")
        self.assertEqual(coupon_data["discount_amount"], 50.00)

        # Check cart summary reflects discount
        res_cart = self.client.get("/api/cart")
        cart_data = res_cart.get_json()["data"]
        self.assertEqual(cart_data["discount"], 50.00)
        self.assertEqual(cart_data["total"], 70.00)

        # Remove coupon
        res_rem = self.client.delete("/api/cart/coupon")
        self.assertEqual(res_rem.status_code, 200)

        res_cart2 = self.client.get("/api/cart")
        self.assertEqual(res_cart2.get_json()["data"]["discount"], 0.0)

    def test_guest_cart_synchronization(self):
        """Verify POST /api/cart/sync merges guest items into user cart upon login."""
        self._login()
        guest_payload = {
            "items": [
                {"product_id": self.prod1.id, "quantity": 1},
                {"product_id": self.prod2.id, "quantity": 3}
            ]
        }
        res_sync = self.client.post("/api/cart/sync", json=guest_payload)
        self.assertEqual(res_sync.status_code, 200)
        summary = res_sync.get_json()["data"]
        self.assertEqual(summary["items_count"], 2)
        self.assertEqual(summary["total_quantity"], 4)
        expected_subtotal = round(120.00 + (15.00 * 3), 2)
        self.assertEqual(summary["subtotal"], expected_subtotal)


class Module6WishlistTestCase(unittest.TestCase):
    """Test suite validating Module 6 Wishlist System requirements."""

    def setUp(self):
        """Set up test client, in-memory SQLite database, and seed data."""
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed categories
        self.cat = Category(name="Fashion", description="Apparel & Accessories")
        db.session.add(self.cat)
        db.session.flush()

        # Seed products
        self.prod1 = Product(
            name="Classic Denim Jacket",
            description="Timeless vintage jacket",
            price=89.99,
            stock=15,
            category_id=self.cat.id,
            image="🧥",
            is_active=True
        )
        self.prod2 = Product(
            name="Leather Chelsea Boots",
            description="Premium handmade leather",
            price=149.99,
            stock=8,
            category_id=self.cat.id,
            image="🥾",
            is_active=True
        )
        self.prod_oos = Product(
            name="Limited Edition Silk Scarf",
            description="Sold out luxury silk",
            price=65.00,
            stock=0,
            category_id=self.cat.id,
            image="🧣",
            is_active=True
        )
        self.prod_inactive = Product(
            name="Archived Item",
            description="No longer sold",
            price=45.00,
            stock=10,
            category_id=self.cat.id,
            image="📦",
            is_active=False
        )

        # Seed test user
        self.user = User(
            name="Wishlist Enthusiast",
            email="wishlistuser@example.com",
            role=User.ROLE_USER
        )
        self.user.set_password("Secret123!")

        db.session.add_all([self.prod1, self.prod2, self.prod_oos, self.prod_inactive, self.user])
        db.session.commit()

    def tearDown(self):
        """Clean up database session and drop all tables."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _login(self):
        """Establish authenticated session for self.user."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["user_name"] = self.user.name
            sess["user_email"] = self.user.email
            sess["user_role"] = self.user.role

    def test_wishlist_status_endpoint(self):
        """Verify GET /api/wishlist/status returns 200 and operational health message."""
        res = self.client.get("/api/wishlist/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("Module 6 Active", data.get("message"))

    def test_wishlist_html_page_renders_successfully(self):
        """Verify GET /wishlist returns 200 with complete wishlist view and toolbar."""
        res = self.client.get("/wishlist")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"My Saved Favorites", res.data)
        self.assertIn(b"Move All to Bag", res.data)
        self.assertIn(b"Share Wishlist", res.data)

    def test_api_wishlist_empty_state(self):
        """Verify GET /api/wishlist returns empty array and 0 count."""
        res = self.client.get("/api/wishlist")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["data"]["items_count"], 0)
        self.assertEqual(data["data"]["items"], [])

    def test_add_to_wishlist_authenticated(self):
        """Verify authenticated user can add product to wishlist."""
        self._login()
        res = self.client.post("/api/wishlist/items", json={"product_id": self.prod1.id})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["wishlist"]["items_count"], 1)

        # Query back
        res_get = self.client.get("/api/wishlist")
        self.assertEqual(res_get.status_code, 200)
        items = res_get.get_json()["data"]["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["product_id"], self.prod1.id)
        self.assertEqual(items[0]["name"], self.prod1.name)

    def test_add_to_wishlist_duplicate_guard(self):
        """Verify adding an existing item does not duplicate rows."""
        self._login()
        self.client.post("/api/wishlist/items", json={"product_id": self.prod1.id})
        res2 = self.client.post("/api/wishlist/items", json={"product_id": self.prod1.id})
        self.assertEqual(res2.status_code, 200)
        self.assertIn("already in your wishlist", res2.get_json()["message"])

        res_get = self.client.get("/api/wishlist")
        self.assertEqual(res_get.get_json()["data"]["items_count"], 1)

    def test_add_to_wishlist_invalid_or_inactive(self):
        """Verify adding inactive or nonexistent product returns 404."""
        self._login()
        # Nonexistent
        res_non = self.client.post("/api/wishlist/items", json={"product_id": 99999})
        self.assertEqual(res_non.status_code, 404)

        # Inactive
        res_inact = self.client.post("/api/wishlist/items", json={"product_id": self.prod_inactive.id})
        self.assertEqual(res_inact.status_code, 404)

    def test_toggle_wishlist_lifecycle(self):
        """Verify toggling adds item when absent and removes when present."""
        self._login()

        # 1. Toggle ON
        res1 = self.client.post("/api/wishlist/toggle", json={"product_id": self.prod2.id})
        self.assertEqual(res1.status_code, 200)
        data1 = res1.get_json()
        self.assertTrue(data1["is_in_wishlist"])
        self.assertEqual(data1["wishlist"]["items_count"], 1)

        # 2. Toggle OFF
        res2 = self.client.post("/api/wishlist/toggle", json={"product_id": self.prod2.id})
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertFalse(data2["is_in_wishlist"])
        self.assertEqual(data2["wishlist"]["items_count"], 0)

    def test_remove_from_wishlist(self):
        """Verify DELETE /api/wishlist/items/<id> removes item."""
        self._login()
        self.client.post("/api/wishlist/items", json={"product_id": self.prod1.id})
        res_del = self.client.delete(f"/api/wishlist/items/{self.prod1.id}")
        self.assertEqual(res_del.status_code, 200)
        self.assertEqual(res_del.get_json()["wishlist"]["items_count"], 0)

    def test_clear_wishlist(self):
        """Verify DELETE /api/wishlist clears all items."""
        self._login()
        self.client.post("/api/wishlist/items", json={"product_id": self.prod1.id})
        self.client.post("/api/wishlist/items", json={"product_id": self.prod2.id})

        res_clear = self.client.delete("/api/wishlist")
        self.assertEqual(res_clear.status_code, 200)
        self.assertEqual(res_clear.get_json()["wishlist"]["items_count"], 0)

    def test_move_item_to_cart(self):
        """Verify POST /api/wishlist/items/<id>/move-to-cart transfers product from wishlist to cart."""
        self._login()
        self.client.post("/api/wishlist/items", json={"product_id": self.prod1.id})

        res_move = self.client.post(f"/api/wishlist/items/{self.prod1.id}/move-to-cart")
        self.assertEqual(res_move.status_code, 200)
        data = res_move.get_json()
        self.assertEqual(data["wishlist"]["items_count"], 0)
        self.assertEqual(data["cart"]["items_count"], 1)
        self.assertEqual(data["cart"]["items"][0]["product"]["id"], self.prod1.id)

    def test_move_all_items_to_cart(self):
        """Verify POST /api/wishlist/move-all-to-cart transfers in-stock items and skips out-of-stock items."""
        self._login()
        self.client.post("/api/wishlist/items", json={"product_id": self.prod1.id})
        self.client.post("/api/wishlist/items", json={"product_id": self.prod2.id})
        self.client.post("/api/wishlist/items", json={"product_id": self.prod_oos.id})

        res_move_all = self.client.post("/api/wishlist/move-all-to-cart")
        self.assertEqual(res_move_all.status_code, 200)
        data = res_move_all.get_json()
        self.assertEqual(data["data"]["moved_count"], 2)
        self.assertEqual(data["data"]["skipped_count"], 1)
        self.assertEqual(data["cart"]["items_count"], 2)
        # Out-of-stock item remains in wishlist
        self.assertEqual(data["wishlist"]["items_count"], 1)

    def test_guest_wishlist_sync_upon_login(self):
        """Verify POST /api/wishlist/sync merges guest product IDs into user wishlist."""
        self._login()
        payload = {"product_ids": [self.prod1.id, self.prod2.id]}
        res_sync = self.client.post("/api/wishlist/sync", json=payload)
        self.assertEqual(res_sync.status_code, 200)
        data = res_sync.get_json()["data"]
        self.assertEqual(data["items_count"], 2)

    def test_guest_wishlist_hydration(self):
        """Verify GET /api/wishlist?product_ids=... hydrates product details for guests."""
        res = self.client.get(f"/api/wishlist?product_ids={self.prod1.id},{self.prod2.id}")
        self.assertEqual(res.status_code, 200)
        items = res.get_json()["data"]["items"]
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["name"], self.prod1.name)
        self.assertEqual(items[1]["name"], self.prod2.name)


if __name__ == "__main__":
    unittest.main()




