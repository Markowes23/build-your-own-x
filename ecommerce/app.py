from flask import Flask, jsonify, request, session, render_template, redirect, url_for

app = Flask(__name__)
app.secret_key = "secret-key"

# Sample product catalog
PRODUCTS = {
    1: {"id": 1, "name": "Widget", "price": 9.99},
    2: {"id": 2, "name": "Gadget", "price": 14.99},
    3: {"id": 3, "name": "Doodad", "price": 4.99},
}


def get_cart() -> dict:
    """Return the cart stored in the session."""
    return session.setdefault("cart", {})


# Web UI routes -------------------------------------------------------------
@app.route("/")
def index():
    """Display product catalog."""
    return render_template("index.html", title="Products", products=PRODUCTS.values())


@app.post("/add/<int:product_id>")
def add_to_cart(product_id: int):
    """Add a product to the cart and redirect back to the catalog."""
    cart = get_cart()
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session["cart"] = cart
    return redirect(url_for("index"))


@app.route("/cart")
def show_cart():
    """Show items in the cart."""
    cart = get_cart()
    items = [{**PRODUCTS[int(pid)], "qty": qty} for pid, qty in cart.items()]
    total = sum(PRODUCTS[int(pid)]["price"] * qty for pid, qty in cart.items())
    return render_template("cart.html", title="Your Cart", items=items, total=total)


# JSON API -----------------------------------------------------------------
@app.route("/api/products")
def api_products():
    return jsonify(list(PRODUCTS.values()))


@app.route("/api/cart", methods=["GET", "POST"])
def api_cart():
    cart = get_cart()
    if request.method == "POST":
        item_id = int(request.json.get("id"))
        cart[str(item_id)] = cart.get(str(item_id), 0) + 1
        session["cart"] = cart
        return jsonify({"message": "added", "cart": cart})
    items = [{**PRODUCTS[int(i)], "qty": qty} for i, qty in cart.items()]
    total = sum(PRODUCTS[int(i)]["price"] * qty for i, qty in cart.items())
    return jsonify({"items": items, "total": total})


if __name__ == "__main__":
    app.run(debug=True)
