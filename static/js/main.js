/**
 * ShopEase — Core JavaScript & Frontend Foundation
 * Module 1 — Frontend Foundation & Home Page
 */

// -----------------------------------------------------------------------------
// 1. Centralized API Service Foundation
// -----------------------------------------------------------------------------
const ApiService = {
    baseUrl: '',

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            ...(options.headers || {})
        };

        const token = localStorage.getItem('shopease_auth_token');
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, { ...options, headers });
            const contentType = response.headers.get('content-type') || '';
            const data = contentType.includes('application/json') ? await response.json() : await response.text();

            if (!response.ok) {
                const errorMessage = (typeof data === 'object' && data.error && data.error.message)
                    ? data.error.message
                    : `HTTP Error ${response.status}: ${response.statusText}`;
                return {
                    success: false,
                    status: response.status,
                    error: errorMessage,
                    data: null
                };
            }

            return {
                success: true,
                status: response.status,
                data: data
            };
        } catch (networkError) {
            return {
                success: false,
                status: 0,
                error: 'Network connectivity error. Could not contact the server.',
                data: null
            };
        }
    },

    get(endpoint, headers = {}) {
        return this.request(endpoint, { method: 'GET', headers });
    },

    post(endpoint, body = {}, headers = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(body),
            headers
        });
    },

    put(endpoint, body = {}, headers = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(body),
            headers
        });
    },

    delete(endpoint, headers = {}) {
        return this.request(endpoint, {
            method: 'DELETE',
            headers
        });
    }
};

// -----------------------------------------------------------------------------
// 2. Reusable Toast Notification System
// -----------------------------------------------------------------------------
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    else if (type === 'error') icon = '⚠️';
    else if (type === 'warning') icon = '🔔';

    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.transition = 'opacity 300ms ease, transform 300ms ease';
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(60px)';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// -----------------------------------------------------------------------------
// 3. Client State Management (Cart, Wishlist, Discounts)
// -----------------------------------------------------------------------------
const AppState = {
    cart: JSON.parse(localStorage.getItem('shopease_cart') || '[]'),
    wishlist: JSON.parse(localStorage.getItem('shopease_wishlist') || '[]'),
    discountPercent: 0,
    appliedCoupon: '',

    saveCart() {
        localStorage.setItem('shopease_cart', JSON.stringify(this.cart));
        this.renderCart();
    },

    saveWishlist() {
        localStorage.setItem('shopease_wishlist', JSON.stringify(this.wishlist));
        this.renderWishlist();
    },

    async init() {
        const isAuth = document.body && document.body.dataset.authenticated === 'true';
        if (isAuth) {
            if (this.cart.length > 0) {
                try {
                    const syncRes = await ApiService.post('/api/cart/sync', { items: this.cart });
                    if (syncRes.success && syncRes.data && syncRes.data.data) {
                        const s = syncRes.data.data;
                        this.cart = (s.items || []).map(i => ({
                            id: i.product.id,
                            name: i.product.name,
                            price: parseFloat(i.product.price),
                            image: i.product.image || '📦',
                            category: i.product.category_name || 'General',
                            quantity: i.quantity
                        }));
                        if (s.coupon) {
                            this.discountPercent = s.coupon.discount_percent;
                            this.appliedCoupon = s.coupon.code;
                        }
                        this.saveCart();
                    }
                } catch (e) {
                    console.error('Cart sync error:', e);
                }
            } else {
                try {
                    const cartRes = await ApiService.get('/api/cart');
                    if (cartRes.success && cartRes.data && cartRes.data.data) {
                        const s = cartRes.data.data;
                        this.cart = (s.items || []).map(i => ({
                            id: i.product.id,
                            name: i.product.name,
                            price: parseFloat(i.product.price),
                            image: i.product.image || '📦',
                            category: i.product.category_name || 'General',
                            quantity: i.quantity
                        }));
                        if (s.coupon) {
                            this.discountPercent = s.coupon.discount_percent;
                            this.appliedCoupon = s.coupon.code;
                        }
                        this.saveCart();
                    }
                } catch (e) {
                    console.error('Cart fetch error:', e);
                }
            }
        }
        this.renderCart();
        this.renderWishlist();
    },

    async addToCart(product) {
        const qtyToAdd = product.quantity && product.quantity > 0 ? parseInt(product.quantity) : 1;
        const productId = parseInt(product.id || product.product_id);

        const res = await ApiService.post('/api/cart/items', {
            product_id: productId,
            quantity: qtyToAdd
        });

        if (res.success) {
            const existing = this.cart.find(item => item.id == productId);
            if (existing) {
                existing.quantity += qtyToAdd;
            } else {
                this.cart.push({
                    id: productId,
                    name: product.name,
                    price: parseFloat(product.price),
                    image: product.image || '📦',
                    category: product.category || 'General',
                    quantity: qtyToAdd
                });
            }
            this.saveCart();
            showToast(`Added "${product.name}" to shopping bag!`, 'success');
            openCartDrawer();
            return true;
        } else {
            showToast(res.error || `Could not add "${product.name}" to cart.`, 'error');
            return false;
        }
    },

    async updateCartQuantity(productId, delta) {
        const item = this.cart.find(i => i.id == productId);
        if (!item) return;

        const newQty = item.quantity + delta;
        if (newQty <= 0) {
            await this.removeFromCart(productId);
            return;
        }

        const res = await ApiService.put(`/api/cart/items/${productId}`, {
            quantity: newQty
        });

        if (res.success) {
            item.quantity = newQty;
            this.saveCart();
        } else {
            showToast(res.error || 'Could not update quantity.', 'error');
        }
    },

    async removeFromCart(productId) {
        const item = this.cart.find(i => i.id == productId);
        await ApiService.delete(`/api/cart/items/${productId}`);

        this.cart = this.cart.filter(i => i.id != productId);
        this.saveCart();
        if (item) {
            showToast(`Removed "${item.name}" from shopping bag.`, 'info');
        }
    },

    toggleWishlist(product) {
        const index = this.wishlist.findIndex(id => id == product.id);
        if (index > -1) {
            this.wishlist.splice(index, 1);
            this.saveWishlist();
            showToast(`Removed "${product.name}" from your wishlist.`, 'info');
            return false;
        } else {
            this.wishlist.push(product.id);
            this.saveWishlist();
            showToast(`Added "${product.name}" to your wishlist!`, 'success');
            return true;
        }
    },

    renderCart() {
        const cartBadge = document.getElementById('cart-badge');
        const cartDrawerBadge = document.getElementById('cart-drawer-badge');
        const cartTotalPreview = document.getElementById('cart-total-preview');
        const cartItemsList = document.getElementById('cart-items-list');
        const cartEmptyView = document.getElementById('cart-empty-view');
        const mobileCartCount = document.querySelector('.mobile-cart-count');

        const totalItems = this.cart.reduce((sum, item) => sum + item.quantity, 0);
        let subtotal = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

        if (cartBadge) cartBadge.textContent = totalItems;
        if (cartDrawerBadge) cartDrawerBadge.textContent = `${totalItems} item${totalItems === 1 ? '' : 's'}`;
        if (mobileCartCount) mobileCartCount.textContent = totalItems;

        // Calculate discounts & shipping
        const discountAmount = subtotal * (this.discountPercent / 100);
        const finalSubtotal = subtotal - discountAmount;
        const shipping = (finalSubtotal >= 50 || finalSubtotal === 0) ? 0 : 5.00;
        const total = finalSubtotal > 0 ? (finalSubtotal + shipping) : 0;

        if (cartTotalPreview) {
            cartTotalPreview.textContent = `$${total.toFixed(2)}`;
        }

        // Summary breakdowns
        const drawerSubtotal = document.getElementById('drawer-subtotal');
        const drawerDiscountRow = document.getElementById('drawer-discount-row');
        const drawerDiscount = document.getElementById('drawer-discount');
        const drawerShipping = document.getElementById('drawer-shipping');
        const drawerTotal = document.getElementById('drawer-total');

        if (drawerSubtotal) drawerSubtotal.textContent = `$${subtotal.toFixed(2)}`;
        if (drawerDiscountRow && drawerDiscount) {
            if (this.discountPercent > 0) {
                drawerDiscountRow.classList.remove('hidden');
                drawerDiscount.textContent = `-$${discountAmount.toFixed(2)} (${this.discountPercent}%)`;
            } else {
                drawerDiscountRow.classList.add('hidden');
            }
        }
        if (drawerShipping) {
            drawerShipping.textContent = (shipping === 0) ? 'FREE' : `$${shipping.toFixed(2)}`;
        }
        if (drawerTotal) {
            drawerTotal.textContent = `$${total.toFixed(2)}`;
        }

        // Render Cart items list
        if (!cartItemsList || !cartEmptyView) return;

        if (this.cart.length === 0) {
            cartEmptyView.classList.remove('hidden');
            cartItemsList.classList.add('hidden');
            cartItemsList.innerHTML = '';
        } else {
            cartEmptyView.classList.add('hidden');
            cartItemsList.classList.remove('hidden');
            cartItemsList.innerHTML = this.cart.map(item => `
                <div class="cart-item-card" data-id="${item.id}">
                    <div class="cart-item-media">
                        <span>${item.image}</span>
                    </div>
                    <div class="cart-item-details">
                        <h5 title="${item.name}">${item.name}</h5>
                        <div class="cart-item-meta">${item.category}</div>
                        <div class="cart-item-bottom">
                            <span class="cart-item-price">$${(item.price * item.quantity).toFixed(2)}</span>
                            <div class="cart-qty-controls">
                                <button class="qty-btn btn-qty-minus" data-id="${item.id}" aria-label="Decrease quantity">−</button>
                                <span class="qty-val">${item.quantity}</span>
                                <button class="qty-btn btn-qty-plus" data-id="${item.id}" aria-label="Increase quantity">+</button>
                            </div>
                            <button class="cart-remove-item" data-id="${item.id}" title="Remove item" aria-label="Remove item">🗑️</button>
                        </div>
                    </div>
                </div>
            `).join('');

            // Bind listeners inside cart list
            cartItemsList.querySelectorAll('.btn-qty-minus').forEach(btn => {
                btn.addEventListener('click', () => {
                    const id = btn.getAttribute('data-id');
                    AppState.updateCartQuantity(id, -1);
                });
            });

            cartItemsList.querySelectorAll('.btn-qty-plus').forEach(btn => {
                btn.addEventListener('click', () => {
                    const id = btn.getAttribute('data-id');
                    AppState.updateCartQuantity(id, 1);
                });
            });

            cartItemsList.querySelectorAll('.cart-remove-item').forEach(btn => {
                btn.addEventListener('click', () => {
                    const id = btn.getAttribute('data-id');
                    AppState.removeFromCart(id);
                });
            });
        }
    },

    renderWishlist() {
        const wishlistBadge = document.getElementById('wishlist-badge');
        const mobileWishlistCount = document.querySelector('.mobile-wishlist-count');
        const count = this.wishlist.length;

        if (wishlistBadge) wishlistBadge.textContent = count;
        if (mobileWishlistCount) mobileWishlistCount.textContent = count;

        // Update all heart icons on the page
        document.querySelectorAll('.wishlist-toggle-btn').forEach(btn => {
            const id = btn.getAttribute('data-id');
            if (this.wishlist.includes(parseInt(id)) || this.wishlist.includes(String(id))) {
                btn.classList.add('active');
                btn.querySelector('.heart-icon').textContent = '❤️';
            } else {
                btn.classList.remove('active');
                btn.querySelector('.heart-icon').textContent = '🤍';
            }
        });
    }
};

// -----------------------------------------------------------------------------
// 4. Drawer & Modal Controller Functions
// -----------------------------------------------------------------------------
function openCartDrawer() {
    const drawer = document.getElementById('cart-drawer');
    const backdrop = document.getElementById('cart-drawer-backdrop');
    if (drawer && backdrop) {
        drawer.classList.add('open');
        backdrop.classList.add('active');
        drawer.setAttribute('aria-hidden', 'false');
        backdrop.setAttribute('aria-hidden', 'false');
    }
}

function closeCartDrawer() {
    const drawer = document.getElementById('cart-drawer');
    const backdrop = document.getElementById('cart-drawer-backdrop');
    if (drawer && backdrop) {
        drawer.classList.remove('open');
        backdrop.classList.remove('active');
        drawer.setAttribute('aria-hidden', 'true');
        backdrop.setAttribute('aria-hidden', 'true');
    }
}

function openMobileDrawer() {
    const drawer = document.getElementById('mobile-drawer');
    const backdrop = document.getElementById('mobile-drawer-backdrop');
    const toggleBtn = document.getElementById('nav-toggle-btn');
    if (drawer && backdrop) {
        drawer.classList.add('open');
        backdrop.classList.add('active');
        drawer.setAttribute('aria-hidden', 'false');
        if (toggleBtn) toggleBtn.setAttribute('aria-expanded', 'true');
    }
}

function closeMobileDrawer() {
    const drawer = document.getElementById('mobile-drawer');
    const backdrop = document.getElementById('mobile-drawer-backdrop');
    const toggleBtn = document.getElementById('nav-toggle-btn');
    if (drawer && backdrop) {
        drawer.classList.remove('open');
        backdrop.classList.remove('active');
        drawer.setAttribute('aria-hidden', 'true');
        if (toggleBtn) toggleBtn.setAttribute('aria-expanded', 'false');
    }
}

function openGeneralModal(title, bodyHtml) {
    const modal = document.getElementById('general-modal');
    const titleEl = document.getElementById('modal-title');
    const bodyEl = document.getElementById('modal-body');
    if (modal && titleEl && bodyEl) {
        titleEl.textContent = title;
        bodyEl.innerHTML = bodyHtml;
        modal.classList.remove('hidden');
        modal.setAttribute('aria-hidden', 'false');
    }
}

function closeGeneralModal() {
    const modal = document.getElementById('general-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.setAttribute('aria-hidden', 'true');
    }
}

// -----------------------------------------------------------------------------
// 5. DOM Initialization & Event Listeners
// -----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    // 5.1 Initialize State & Sync
    AppState.init();

    // 5.2 Navigation & Drawer Listeners
    const navCartBtn = document.getElementById('nav-cart-btn');
    const cartCloseBtn = document.getElementById('cart-drawer-close');
    const cartBackdrop = document.getElementById('cart-drawer-backdrop');
    const cartContinueBtn = document.getElementById('cart-continue-btn');
    const cartEmptyExplore = document.getElementById('cart-empty-explore-btn');

    if (navCartBtn) navCartBtn.addEventListener('click', openCartDrawer);
    if (cartCloseBtn) cartCloseBtn.addEventListener('click', closeCartDrawer);
    if (cartBackdrop) cartBackdrop.addEventListener('click', closeCartDrawer);
    if (cartContinueBtn) cartContinueBtn.addEventListener('click', closeCartDrawer);
    if (cartEmptyExplore) {
        cartEmptyExplore.addEventListener('click', () => {
            closeCartDrawer();
            window.location.href = '/products';
        });
    }

    const navToggleBtn = document.getElementById('nav-toggle-btn');
    const mobileCloseBtn = document.getElementById('mobile-drawer-close');
    const mobileBackdrop = document.getElementById('mobile-drawer-backdrop');

    if (navToggleBtn) navToggleBtn.addEventListener('click', openMobileDrawer);
    if (mobileCloseBtn) mobileCloseBtn.addEventListener('click', closeMobileDrawer);
    if (mobileBackdrop) mobileBackdrop.addEventListener('click', closeMobileDrawer);

    // Modal listeners
    const modalClose = document.getElementById('general-modal-close');
    const modalConfirm = document.getElementById('modal-confirm-btn');
    const generalModal = document.getElementById('general-modal');

    if (modalClose) modalClose.addEventListener('click', closeGeneralModal);
    if (modalConfirm) modalConfirm.addEventListener('click', closeGeneralModal);
    if (generalModal) {
        generalModal.addEventListener('click', (e) => {
            if (e.target === generalModal) closeGeneralModal();
        });
    }

    // Escape key closes modals and drawers
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeCartDrawer();
            closeMobileDrawer();
            closeGeneralModal();
            closeSearchDropdown();
        }
    });

    // 5.3 Checkout Navigation
    const checkoutBtn = document.getElementById('cart-checkout-btn');
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', (e) => {
            if (AppState.cart.length === 0) {
                e.preventDefault();
                showToast('Your shopping bag is empty! Add products first.', 'warning');
                return;
            }
        });
    }

    // 5.4 Coupon / Promo Code Form
    const applyCouponBtn = document.getElementById('apply-coupon-btn');
    const couponInput = document.getElementById('coupon-code-input');
    const couponFeedback = document.getElementById('coupon-feedback');

    if (applyCouponBtn && couponInput) {
        applyCouponBtn.addEventListener('click', async () => {
            const code = couponInput.value.trim().toUpperCase();
            if (!code) {
                showToast('Please enter a promo code.', 'warning');
                return;
            }
            const currentSubtotal = AppState.cart.reduce((s, i) => s + (i.price * i.quantity), 0);
            const res = await ApiService.post('/api/cart/coupon', {
                coupon_code: code,
                subtotal: currentSubtotal
            });

            if (res.success && res.data && res.data.data) {
                const couponData = res.data.data;
                AppState.discountPercent = couponData.discount_percent;
                AppState.appliedCoupon = couponData.code;
                AppState.renderCart();
                if (couponFeedback) {
                    couponFeedback.className = 'coupon-feedback text-success';
                    couponFeedback.textContent = `🎉 ${couponData.description}`;
                    couponFeedback.classList.remove('hidden');
                }
                showToast(`Promo code "${code}" applied!`, 'success');
            } else {
                AppState.discountPercent = 0;
                AppState.appliedCoupon = '';
                AppState.renderCart();
                if (couponFeedback) {
                    couponFeedback.className = 'coupon-feedback text-danger';
                    couponFeedback.textContent = res.error || 'Invalid promo code.';
                    couponFeedback.classList.remove('hidden');
                }
                showToast(res.error || 'Invalid promo code.', 'error');
            }
        });
    }

    // 5.5 Add-to-cart Buttons
    function bindAddToCartButtons() {
        document.querySelectorAll('.add-to-cart-btn, .hero-quick-add, .btn-card-add-cart').forEach(btn => {
            btn.onclick = (e) => {
                e.stopPropagation();
                const id = btn.getAttribute('data-id');
                const name = btn.getAttribute('data-name');
                const price = btn.getAttribute('data-price');
                const image = btn.getAttribute('data-image');
                const category = btn.getAttribute('data-category');

                AppState.addToCart({ id, name, price, image, category });
            };
        });
    }
    bindAddToCartButtons();

    // 5.6 Wishlist Buttons
    function bindWishlistButtons() {
        document.querySelectorAll('.wishlist-toggle-btn').forEach(btn => {
            btn.onclick = (e) => {
                e.stopPropagation();
                const id = btn.getAttribute('data-id');
                const name = btn.getAttribute('data-name');
                AppState.toggleWishlist({ id, name });
            };
        });
    }
    bindWishlistButtons();

    // Wishlist top button click
    const navWishlistBtn = document.getElementById('nav-wishlist-btn');
    if (navWishlistBtn) {
        navWishlistBtn.addEventListener('click', () => {
            if (AppState.wishlist.length === 0) {
                showToast('Your wishlist is empty. Tap any ❤️ to save favorites!', 'info');
            } else {
                openGeneralModal(
                    'My Wishlist',
                    `<p>You have <strong>${AppState.wishlist.length} item(s)</strong> saved in your favorites list.</p>
                     <p style="margin-top: 0.5rem; color: #4f46e5; font-weight: 600;">
                        Full dedicated Wishlist management will be expanded in <strong>Module 6</strong>.
                     </p>`
                );
            }
        });
    }

    // 5.7 Category Filtering Logic
    let activeCategory = '';

    function filterProducts(category) {
        activeCategory = category;
        const activeFilterBar = document.getElementById('active-filter-bar');
        const activeFilterLabel = document.getElementById('active-filter-label');
        const cards = document.querySelectorAll('#main-products-grid .product-card');

        // Update tabs active state
        document.querySelectorAll('#catalog-category-tabs .filter-tab').forEach(tab => {
            const cat = tab.getAttribute('data-category') || '';
            tab.classList.toggle('active', cat === category);
        });

        // Update sub-nav active state
        document.querySelectorAll('#sub-nav-categories .sub-nav-link').forEach(link => {
            const cat = link.getAttribute('data-category') || '';
            link.classList.toggle('active', cat === category);
        });

        // Show/hide filter bar
        if (category) {
            if (activeFilterBar && activeFilterLabel) {
                activeFilterBar.classList.remove('hidden');
                activeFilterLabel.textContent = category;
            }
        } else {
            if (activeFilterBar) activeFilterBar.classList.add('hidden');
        }

        // Filter cards in grid
        let visibleCount = 0;
        cards.forEach(card => {
            const cardCat = card.getAttribute('data-category') || '';
            const matches = !category || cardCat.toLowerCase() === category.toLowerCase();
            card.style.display = matches ? 'flex' : 'none';
            if (matches) visibleCount++;
        });

        if (category) {
            showToast(`Filtering by "${category}" (${visibleCount} items found)`, 'info');
        }
    }

    // Filter tab clicks
    document.querySelectorAll('#catalog-category-tabs .filter-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const cat = tab.getAttribute('data-category') || '';
            filterProducts(cat);
        });
    });

    // Sub-nav category clicks
    document.querySelectorAll('#sub-nav-categories .sub-nav-link').forEach(btn => {
        btn.addEventListener('click', (e) => {
            if (btn.classList.contains('special-deal')) return;
            const cat = btn.getAttribute('data-category') || '';
            const section = document.getElementById('products-section');
            if (section) {
                filterProducts(cat);
                section.scrollIntoView({ behavior: 'smooth' });
            } else {
                window.location.href = cat ? `/products?category=${encodeURIComponent(cat)}` : '/products';
            }
        });
    });

    // Category cards click
    document.querySelectorAll('.category-card').forEach(card => {
        card.addEventListener('click', () => {
            const cat = card.getAttribute('data-category') || '';
            const section = document.getElementById('products-section');
            if (section) {
                filterProducts(cat);
                section.scrollIntoView({ behavior: 'smooth' });
            } else {
                window.location.href = cat ? `/products?category=${encodeURIComponent(cat)}` : '/products';
            }
        });
    });

    // Footer category links click
    document.querySelectorAll('.footer-cat-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const cat = link.getAttribute('data-cat') || '';
            const section = document.getElementById('products-section');
            if (section) {
                filterProducts(cat);
                section.scrollIntoView({ behavior: 'smooth' });
            } else {
                window.location.href = cat ? `/products?category=${encodeURIComponent(cat)}` : '/products';
            }
        });
    });

    // Mobile category links click
    document.querySelectorAll('.mobile-category-link').forEach(link => {
        link.addEventListener('click', () => {
            const cat = link.getAttribute('data-category') || '';
            closeMobileDrawer();
            const section = document.getElementById('products-section');
            if (section) {
                filterProducts(cat);
                section.scrollIntoView({ behavior: 'smooth' });
            } else {
                window.location.href = cat ? `/products?category=${encodeURIComponent(cat)}` : '/products';
            }
        });
    });

    // Clear active filter button
    const clearFilterBtn = document.getElementById('btn-clear-active-filter');
    if (clearFilterBtn) {
        clearFilterBtn.addEventListener('click', () => {
            filterProducts('');
        });
    }

    // 5.8 Sorting Logic
    const sortSelect = document.getElementById('catalog-sort-select');
    if (sortSelect) {
        sortSelect.addEventListener('change', () => {
            const val = sortSelect.value;
            const grid = document.getElementById('main-products-grid');
            if (!grid) return;

            const cards = Array.from(grid.querySelectorAll('.product-card'));
            cards.sort((a, b) => {
                const priceA = parseFloat(a.getAttribute('data-price') || 0);
                const priceB = parseFloat(b.getAttribute('data-price') || 0);
                const ratingA = parseFloat(a.getAttribute('data-rating') || 0);
                const ratingB = parseFloat(b.getAttribute('data-rating') || 0);

                if (val === 'price-low') return priceA - priceB;
                if (val === 'price-high') return priceB - priceA;
                if (val === 'rating') return ratingB - ratingA;
                return 0; // default order
            });

            cards.forEach(card => grid.appendChild(card));
            showToast(`Sorted catalog by ${sortSelect.options[sortSelect.selectedIndex].text}`, 'info');
        });
    }

    // 5.9 Live Search with Debounce & Dropdown Suggestions
    const searchInput = document.getElementById('site-search-input');
    const searchCategorySelect = document.getElementById('search-category-select');
    const searchDropdown = document.getElementById('search-results-dropdown');
    const searchDropdownList = document.getElementById('search-dropdown-list');
    const searchCountEl = document.getElementById('search-results-count');
    const searchClearBtn = document.getElementById('search-clear-btn');
    const viewAllSearchBtn = document.getElementById('view-all-search-btn');
    let searchTimeout = null;

    function closeSearchDropdown() {
        if (searchDropdown) searchDropdown.classList.add('hidden');
    }

    if (searchInput && searchDropdown && searchDropdownList) {
        searchInput.addEventListener('input', () => {
            const query = searchInput.value.trim();
            if (searchClearBtn) {
                searchClearBtn.classList.toggle('hidden', query.length === 0);
            }

            clearTimeout(searchTimeout);
            if (query.length < 2) {
                closeSearchDropdown();
                return;
            }

            searchTimeout = setTimeout(async () => {
                const selectedCat = searchCategorySelect ? searchCategorySelect.value : '';
                let endpoint = `/api/products?q=${encodeURIComponent(query)}`;
                const res = await ApiService.get(endpoint);

                if (res.success && res.data && res.data.data) {
                    let matches = res.data.data;
                    if (selectedCat) {
                        matches = matches.filter(p => p.category_name === selectedCat);
                    }

                    if (searchCountEl) searchCountEl.textContent = `${matches.length} found`;
                    searchDropdown.classList.remove('hidden');

                    if (matches.length === 0) {
                        searchDropdownList.innerHTML = `
                            <div style="padding: 1.25rem; text-align: center; color: #94a3b8; font-size: 0.88rem;">
                                No products found matching "<strong>${query}</strong>"
                            </div>
                        `;
                    } else {
                        searchDropdownList.innerHTML = matches.slice(0, 5).map(item => `
                            <div class="search-dropdown-item" data-id="${item.id}" data-name="${item.name}" data-price="${item.price}" data-category="${item.category_name}" data-image="${item.image}">
                                <div class="search-item-media">
                                    <span>${item.image && !item.image.endsWith('.png') ? item.image : '📦'}</span>
                                </div>
                                <div class="search-item-info">
                                    <div class="search-item-title">${item.name}</div>
                                    <div class="search-item-cat">${item.category_name}</div>
                                </div>
                                <div class="search-item-price">$${parseFloat(item.price).toFixed(2)}</div>
                            </div>
                        `).join('');

                        // Bind clicks on search items: navigate directly to product detail page
                        searchDropdownList.querySelectorAll('.search-dropdown-item').forEach(itemEl => {
                            itemEl.addEventListener('click', () => {
                                const id = itemEl.getAttribute('data-id');
                                closeSearchDropdown();
                                window.location.href = `/products/${id}`;
                            });
                        });
                    }

                    if (viewAllSearchBtn) {
                        let viewAllUrl = `/products?q=${encodeURIComponent(query)}`;
                        if (selectedCat) viewAllUrl += `&category=${encodeURIComponent(selectedCat)}`;
                        viewAllSearchBtn.href = viewAllUrl;
                        viewAllSearchBtn.textContent = `View All Matching Products (${matches.length}) →`;
                    }
                }
            }, 250);
        });

        function triggerHeaderSearch() {
            const query = searchInput.value.trim();
            const selectedCat = searchCategorySelect ? searchCategorySelect.value : '';
            closeSearchDropdown();
            let target = '/products';
            const params = new URLSearchParams();
            if (query) params.set('q', query);
            if (selectedCat) params.set('category', selectedCat);
            if (params.toString()) target += '?' + params.toString();
            window.location.href = target;
        }

        const searchForm = document.getElementById('search-form');
        const searchSubmitBtn = document.getElementById('search-submit-btn');

        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                triggerHeaderSearch();
            });
        }

        if (searchSubmitBtn) {
            searchSubmitBtn.addEventListener('click', (e) => {
                e.preventDefault();
                triggerHeaderSearch();
            });
        }

        if (searchClearBtn) {
            searchClearBtn.addEventListener('click', () => {
                searchInput.value = '';
                searchClearBtn.classList.add('hidden');
                closeSearchDropdown();
                const section = document.getElementById('products-section');
                if (section) {
                    filterProducts('');
                }
            });
        }

        if (viewAllSearchBtn) {
            viewAllSearchBtn.addEventListener('click', (e) => {
                closeSearchDropdown();
            });
        }

        // Close search dropdown on click outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
                closeSearchDropdown();
            }
        });
    }

    // Mobile Search Submission
    const mobileSearchInput = document.getElementById('mobile-search-input');
    const mobileSearchSubmit = document.getElementById('mobile-search-submit');
    if (mobileSearchSubmit && mobileSearchInput) {
        const doMobileSearch = () => {
            const val = mobileSearchInput.value.trim();
            window.location.href = val ? `/products?q=${encodeURIComponent(val)}` : '/products';
        };
        mobileSearchSubmit.addEventListener('click', doMobileSearch);
        mobileSearchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                doMobileSearch();
            }
        });
    }

    // 5.10 Deal Countdown Timer
    function startDealCountdown() {
        let totalSeconds = 8 * 3600 + 45 * 60 + 30; // 8 hrs 45 mins 30 secs
        const hoursEl = document.getElementById('countdown-hours');
        const minsEl = document.getElementById('countdown-minutes');
        const secsEl = document.getElementById('countdown-seconds');

        if (!hoursEl || !minsEl || !secsEl) return;

        setInterval(() => {
            if (totalSeconds <= 0) {
                totalSeconds = 12 * 3600; // Reset for demo continuity
            }
            totalSeconds--;

            const hours = Math.floor(totalSeconds / 3600);
            const minutes = Math.floor((totalSeconds % 3600) / 60);
            const seconds = totalSeconds % 60;

            hoursEl.textContent = String(hours).padStart(2, '0');
            minsEl.textContent = String(minutes).padStart(2, '0');
            secsEl.textContent = String(seconds).padStart(2, '0');
        }, 1000);
    }
    startDealCountdown();

    // 5.11 Newsletter Subscription Form
    const newsletterForm = document.getElementById('newsletter-form');
    const newsletterEmail = document.getElementById('newsletter-email');

    if (newsletterForm && newsletterEmail) {
        newsletterForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const email = newsletterEmail.value.trim();
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

            if (!email || !emailRegex.test(email)) {
                showToast('Please enter a valid email address.', 'error');
                return;
            }

            showToast(`Welcome! Use code "EASE50" for 50% off your purchase.`, 'success');
            newsletterEmail.value = '';
        });
    }

    // 5.12 User Account Dropdown Toggle (Module 2)
    const userDropdownBtn = document.getElementById('nav-user-dropdown-btn');
    const userDropdownMenu = document.getElementById('user-dropdown-menu');
    const userDropdownContainer = document.getElementById('user-dropdown-container');

    if (userDropdownBtn && userDropdownMenu) {
        userDropdownBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isExpanded = userDropdownBtn.getAttribute('aria-expanded') === 'true';
            userDropdownBtn.setAttribute('aria-expanded', !isExpanded);
            userDropdownMenu.classList.toggle('hidden', isExpanded);
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (userDropdownContainer && !userDropdownContainer.contains(e.target)) {
                userDropdownMenu.classList.add('hidden');
                userDropdownBtn.setAttribute('aria-expanded', 'false');
            }
        });
    }

    // 5.13 Order Tracking Trigger
    const trackOrderBtn = document.getElementById('btn-track-order');
    const footerTrackOrder = document.getElementById('footer-track-order');

    function promptOrderTracking() {
        openGeneralModal(
            'Order Tracking',
            `<p>Track your shipment status with real-time updates.</p>
             <p style="margin-top: 0.5rem; color: #4f46e5; font-weight: 600;">
                Full Order Tracking and History will be available in <strong>Module 7 &amp; 8</strong>.
             </p>`
        );
    }

    if (trackOrderBtn) trackOrderBtn.addEventListener('click', promptOrderTracking);
    if (footerTrackOrder) footerTrackOrder.addEventListener('click', (e) => {
        e.preventDefault();
        promptOrderTracking();
    });

    // 5.14 Check API Health Status on load
    async function checkApiHealth() {
        const res = await ApiService.get('/api/health');
        const statusEl = document.getElementById('footer-api-status');
        const statusDot = document.getElementById('footer-status-dot');

        if (res.success && res.data && res.data.success) {
            if (statusEl) statusEl.textContent = 'API Status: Connected (200 OK)';
            if (statusDot) statusDot.className = 'status-indicator online';
        } else {
            if (statusEl) statusEl.textContent = 'API Status: Offline';
            if (statusDot) statusDot.className = 'status-indicator offline';
        }
    }
    checkApiHealth();
});
