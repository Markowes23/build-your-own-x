from flask import Flask, jsonify, request, session

app = Flask(__name__)
app.secret_key = 'secret-key'

# Sample product catalog
PRODUCTS = {
    1: {"id": 1, "name": "Widget", "price": 9.99},
    2: {"id": 2, "name": "Gadget", "price": 14.99},
    3: {"id": 3, "name": "Doodad", "price": 4.99},
}

@app.route('/products')
def list_products():
    return jsonify(list(PRODUCTS.values()))

@app.route('/cart', methods=['GET', 'POST'])
def manage_cart():
    cart = session.setdefault('cart', {})
    if request.method == 'POST':
        item_id = int(request.json.get('id'))
        cart[item_id] = cart.get(item_id, 0) + 1
        session['cart'] = cart
        return jsonify({'message': 'added', 'cart': cart})
    else:
        items = [{**PRODUCTS[int(i)], 'qty': qty} for i, qty in cart.items()]
        total = sum(PRODUCTS[int(i)]['price'] * qty for i, qty in cart.items())
        return jsonify({'items': items, 'total': total})

if __name__ == '__main__':
    app.run(debug=True)

