# Simple Flask E-commerce Example

This demo shows a tiny e-commerce backend built with Flask. It keeps a product catalog in memory and stores the shopping cart in the session. For more background see the [Flask documentation](https://flask.palletsprojects.com/).

## Prerequisites
- Python 3.8+
- `flask`

## Setup
```bash
pip install flask
python app.py
```

Available endpoints:
- `GET /products` — list all products
- `GET /cart` — view items in your cart
- `POST /cart` with JSON `{ "id": <product_id> }` — add an item to your cart

