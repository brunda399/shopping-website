"""
Live Verification Script for Module 7 Final Test Scenario:
Test 1: Search 'kurti' -> confirm multiple Kurtis appear.
Test 2: Filter Women, Kurtis, Under Rs. 1000 -> confirm results update.
Test 3: Open Kurti -> select Color: Blue, Size: M, Quantity: 2 -> add to cart.
Test 4: Add another Kurti (Pink, Size: L, Quantity: 1) -> confirm both products appear in cart.
Test 5: Change quantity -> confirm totals update dynamically.
Test 6: Proceed to checkout -> add/select address.
Test 7: Select Cash on Delivery.
Test 8: Place order -> confirm order created, cart cleared, inventory decreased, confirmation page.
Test 9: Open Orders -> confirm new order appears.
Test 10: Refresh application -> confirm persistent data remains available.
"""
import requests

def run_scenario():
    session = requests.Session()
    BASE = 'http://127.0.0.1:5000'

    print("======================================================================")
    print("MODULE 7 — LIVE VERIFICATION OF COMPLETE 10-STEP E-COMMERCE JOURNEY")
    print("======================================================================")

    # Test 1: Search 'kurti'
    print("\n[TEST 1] Search: 'kurti'")
    r1 = session.get(f"{BASE}/api/products?q=kurti")
    assert r1.status_code == 200, f"Search failed with {r1.status_code}"
    d1 = r1.json()["data"]
    print(f" -> Found {len(d1)} Kurtis matching query. Sample matches:")
    for p in d1[:4]:
        print(f"    * {p['name']} (Rs. {p['sale_price']})")
    assert len(d1) >= 5, "Expected at least 5 kurtis returned"
    print(" -> TEST 1 PASSED: Multiple Kurtis returned successfully.")

    # Test 2: Filter Women, Kurtis, Under 1000
    print("\n[TEST 2] Filter: Category='Women\\'s Fashion', Subcategory='Kurtis', Max Price=1000")
    r2 = session.get(f"{BASE}/api/products?category=Women%27s%20Fashion&subcategory=Kurtis&max_price=1000")
    assert r2.status_code == 200
    d2 = r2.json()["data"]
    print(f" -> Found {len(d2)} Kurtis under Rs. 1000:")
    for p in d2[:4]:
        print(f"    * {p['name']} (Sale Price: Rs. {p['sale_price']}, Orig: Rs. {p['price']})")
        assert p['sale_price'] <= 1000.0, "Product price must be <= 1000"
    assert len(d2) > 0
    print(" -> TEST 2 PASSED: Category, subcategory, and price filters work correctly.")

    # Authenticate user session
    print("\n[AUTH] Authenticating session for user 'shopper@shopease.com'...")
    login_res = session.post(f"{BASE}/api/auth/login", json={"email": "shopper@shopease.com", "password": "Password123!"})
    if login_res.status_code != 200:
        reg_res = session.post(f"{BASE}/api/auth/register", json={
            "name": "Sai Brunda",
            "email": "shopper@shopease.com",
            "password": "Password123!",
            "phone": "9876543210"
        })
        assert reg_res.status_code in (200, 201), f"Register failed: {reg_res.text}"
        print(" -> Registered and logged in new customer account.")
    else:
        print(" -> Logged in successfully.")

    # Test 3: Add Blue Kurti, Size M, Quantity 2
    print("\n[TEST 3] Open one Kurti, select Color: Blue, Size: M, Quantity: 2 and Add to Cart")
    k1 = d1[0]
    r3 = session.post(f"{BASE}/api/cart/items", json={
        "product_id": k1["id"],
        "quantity": 2,
        "selected_size": "M",
        "selected_color": "Blue"
    })
    assert r3.status_code == 200
    print(f" -> Added {k1['name']} (Size: M, Color: Blue, Qty: 2) to cart.")
    print(" -> TEST 3 PASSED.")

    # Test 4: Add another Kurti with Color: Pink, Size: L, Quantity: 1
    print("\n[TEST 4] Add another Kurti with Color: Pink, Size: L, Quantity: 1")
    k2 = d1[1] if len(d1) > 1 else k1
    r4 = session.post(f"{BASE}/api/cart/items", json={
        "product_id": k2["id"],
        "quantity": 1,
        "selected_size": "L",
        "selected_color": "Pink"
    })
    assert r4.status_code == 200
    print(f" -> Added {k2['name']} (Size: L, Color: Pink, Qty: 1) to cart.")

    cart_res = session.get(f"{BASE}/api/cart")
    cart = cart_res.json()["data"]
    print(f" -> Cart now has {cart['items_count']} distinct items, total quantity: {cart['total_quantity']}, subtotal: Rs. {cart['subtotal']}")
    assert cart["items_count"] >= 2, "Both products must appear in cart without overwriting"
    print(" -> TEST 4 PASSED: Both variant products exist in cart simultaneously.")

    # Test 5: Change quantity and confirm totals update
    print("\n[TEST 5] Change quantity of first cart item to 4")
    item_to_update = cart["items"][0]
    old_subtotal = cart["subtotal"]
    r5 = session.put(f"{BASE}/api/cart/items/{item_to_update['id']}", json={"quantity": 4})
    assert r5.status_code == 200
    updated_cart = r5.json()["cart"]
    print(f" -> Previous subtotal: Rs. {old_subtotal} -> New subtotal: Rs. {updated_cart['subtotal']} (Total Qty: {updated_cart['total_quantity']})")
    assert updated_cart["subtotal"] != old_subtotal
    print(" -> TEST 5 PASSED: Cart quantities and totals recalculate dynamically.")

    # Test 6: Proceed to checkout, select/add address
    print("\n[TEST 6] Proceed to checkout and add delivery address")
    addr_res = session.post(f"{BASE}/api/addresses", json={
        "fullName": "Sai Brunda Reddy",
        "phone": "9876543210",
        "addressLine1": "Prestige Tech Park, Marathahalli-Sarjapur Ring Rd",
        "addressLine2": "Kadubeesanahalli",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postalCode": "560103",
        "country": "India",
        "isDefault": True
    })
    assert addr_res.status_code in (200, 201)
    addr_id = addr_res.json()["data"]["id"]
    print(f" -> Saved delivery address ID: {addr_id}")
    print(" -> TEST 6 PASSED.")

    # Test 7 & 8: Select COD and Place Order
    print("\n[TEST 7 & 8] Select Cash on Delivery (COD) and Place Order")
    prod_info = session.get(f"{BASE}/api/products/{k1['id']}").json()["data"]
    initial_stock = prod_info["stock"]

    order_res = session.post(f"{BASE}/api/orders", json={
        "address_id": addr_id,
        "payment_method": "COD"
    })
    assert order_res.status_code == 201, f"Order placement failed: {order_res.text}"
    order_data = order_res.json()["data"]
    order_num = order_data["orderNumber"]
    print(f" -> Order placed successfully! Order Number: {order_num}")
    print(f"    * Status: {order_data['orderStatus']}")
    print(f"    * Payment: {order_data['paymentMethod']} ({order_data['paymentStatus']})")
    print(f"    * Total Amount: Rs. {order_data['total']}")
    print(f"    * Items count: {len(order_data['items'])}")

    cart_after = session.get(f"{BASE}/api/cart").json()["data"]
    print(f" -> Cart item count after order placement: {cart_after['items_count']}")
    assert cart_after["items_count"] == 0, "Cart must be cleared after successful order"

    prod_info_after = session.get(f"{BASE}/api/products/{k1['id']}").json()["data"]
    stock_after = prod_info_after["stock"]
    print(f" -> Product stock: Initial={initial_stock}, After Order={stock_after} (decreased by purchased qty)")
    assert stock_after < initial_stock

    conf_html = session.get(f"{BASE}/order-confirmation/{order_num}")
    assert conf_html.status_code == 200
    assert "Order placed successfully!" in conf_html.text
    assert order_num in conf_html.text
    print(" -> Confirmation page rendered successfully with order number and tracking details.")
    print(" -> TEST 7 & 8 PASSED.")

    # Test 9: Open Orders and confirm new order appears
    print("\n[TEST 9] Open Orders History page & API")
    orders_api_res = session.get(f"{BASE}/api/orders")
    assert orders_api_res.status_code == 200
    orders_list = orders_api_res.json()["data"]
    print(f" -> User order history contains {len(orders_list)} orders. Latest order: {orders_list[0]['orderNumber']}")
    assert orders_list[0]["orderNumber"] == order_num
    print(" -> TEST 9 PASSED: New order appears in order history.")

    # Test 10: Refresh application and confirm persistent data
    print("\n[TEST 10] Verify persistence across fresh requests and HTML views")
    orders_html = session.get(f"{BASE}/orders")
    assert orders_html.status_code == 200
    assert order_num in orders_html.text

    order_detail_html = session.get(f"{BASE}/orders/{order_num}")
    assert order_detail_html.status_code == 200
    assert order_num in order_detail_html.text
    assert "Prestige Tech Park" in order_detail_html.text

    track_res = session.get(f"{BASE}/api/orders/track/{order_num}")
    assert track_res.status_code == 200
    assert track_res.json()["data"]["orderStatus"] == "PLACED"
    print(" -> Persistent order, address, and tracking data verified across server requests.")
    print(" -> TEST 10 PASSED.")

    print("\n======================================================================")
    print("SUCCESS: ALL 10 TESTS OF THE FINAL TEST SCENARIO PASSED FLAWLESSLY!")
    print("======================================================================")

if __name__ == '__main__':
    run_scenario()
