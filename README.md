
# Bijoux Chic E-Commerce Backend API

A RESTful API for managing products, orders, users, and payments for a jewelry e-commerce platform.

## Features

* User registration and authentication (JWT or session-based)
* CRUD operations for products (rings, necklaces, bracelets, earrings, etc.)
* Order management and status tracking
* Cart management
* Admin endpoints for product and order management
* Payment processing integration (PayStack)
* Secure and scalable API design

## Technologies Used

* **Backend:** Django + Django REST Framework
* **Database:** PostgreSQL 
* **Authentication:** JWT 
* **Payment Integration:** PayStack

## Getting Started

1. **Clone the repository**

```bash
git clone https://github.com/GordenArcher/Bijoux-chic-api.git
cd Bijoux-chic-api
```

2. **Set up virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set environment variables**

```bash
export SECRET_KEY='your-secret-key'
export DEBUG=True
export DATABASE_URL='your-database-url'
export STRIPE_API_KEY='your-stripe-key'  # if using Stripe
```

5. **Run migrations**

```bash
python manage.py migrate
```

6. **Run the server**

```bash
python manage.py runserver
```

7. **API Base URL**

```
http://127.0.0.1:8000/
```

---

## Example API Endpoints

* **User**

  * `POST /api/v1/auth/register/` — register a new user
  * `POST /api/v1/auth/login/` — login and get JWT token
  * `GET /api/v1/auth/me/` — get current user details

* **Products**

  * `GET /api/v1/products/all/` — list all products
  * `POST /api/v1/products/` — create a product (admin only)
  * `GET /api/v1/products/<id>/` — retrieve a product
  * `PUT /api/v1/products/<id>/edit/` — update product (admin only)
  * `DELETE /api/v1/products/delete/` — delete product (admin only)

* **Orders**

  * `GET /api/v1/me/orders/` — list user orders
  * `POST /api/v1/all_orders/` — create a new order
  * `GET /api/v1/orders/<id>/` — get order details
  * `PUT /api/v1/orders/<id>/status/` — update order status (admin only)

* **Cart**

  * `GET /api/v1/cart/` — view user cart
  * `POST /api/v1/cart/add/` — add item to cart
  * `DELETE /api/v1/cart/remove/<item_id>/` — remove item from cart

* **Payments**

  * `POST /api/v1/order/checkout/` — process payment

---

## Contributing

1. Fork the repository
2. Create a branch (`git checkout -b feature/my-feature`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License.

---
