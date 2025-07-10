# Flask E-commerce Demo

This demo shows a minimal e-commerce site built with Flask. It keeps a product catalog in memory and stores the shopping cart in the session. A small web UI powered by Bootstrap lets you browse products and manage your cart.

## Prerequisites
- Python 3.8+
- `flask`

## Setup
```bash
pip install flask
python app.py
```
Then open <http://localhost:5000> in your browser.

Available API endpoints:
- `GET /api/products` — list all products
- `GET /api/cart` — view items in your cart
- `POST /api/cart` with JSON `{ "id": <product_id> }` — add an item to your cart
