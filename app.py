from flask import Flask, render_template, request, redirect, url_for, flash
from mysql.connector import Error
from config import Config
from database import query_all
from services.inventory_service import (
    get_dashboard_data, get_products, get_product, add_product, update_product,
    get_suppliers, add_supplier, create_transaction, get_transactions,
    get_movement_report, get_low_stock
)
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

app = Flask(__name__)
app.config.from_object(Config)

CHART_DIR = os.path.join(app.root_path, "static", "generated")
os.makedirs(CHART_DIR, exist_ok=True)

def make_charts(products, movement):
    stock_path = os.path.join(CHART_DIR, "stock_levels.png")
    movement_path = os.path.join(CHART_DIR, "product_movement.png")

    plt.figure(figsize=(9, 4.5))
    if products:
        names = [str(p["product_name"])[:18] for p in products[:12]]
        values = [int(p["current_stock"]) for p in products[:12]]
        plt.bar(names, values)
        plt.title("Current Stock Levels (first 12 products)")
        plt.ylabel("Units")
        plt.xticks(rotation=35, ha="right")
        plt.tight_layout()
    else:
        plt.text(0.5, 0.5, "Add products to view stock levels", ha="center", va="center")
        plt.axis("off")
    plt.savefig(stock_path, dpi=120)
    plt.close()

    plt.figure(figsize=(9, 4.5))
    if movement:
        rows = movement[:12]
        names = [str(p["product_name"])[:18] for p in rows]
        ins = [int(p["stock_in"]) for p in rows]
        outs = [int(p["stock_out"]) for p in rows]
        x = range(len(names))
        plt.bar([i - 0.2 for i in x], ins, width=0.4, label="Stock In")
        plt.bar([i + 0.2 for i in x], outs, width=0.4, label="Stock Out")
        plt.title("Product Stock Movement")
        plt.ylabel("Units")
        plt.xticks(list(x), names, rotation=35, ha="right")
        plt.legend()
        plt.tight_layout()
    else:
        plt.text(0.5, 0.5, "Record transactions to view movement", ha="center", va="center")
        plt.axis("off")
    plt.savefig(movement_path, dpi=120)
    plt.close()

@app.route("/")
def dashboard():
    try:
        data = get_dashboard_data()
        movement = get_movement_report()
        make_charts(data["products"], movement)
        return render_template("dashboard.html", data=data)
    except Error as exc:
        return render_template("error.html",
            message="Could not connect to MySQL. Check that MySQL is running, the database exists, and your .env settings are correct.",
            details=str(exc)), 500

@app.route("/products")
def products():
    return render_template("products.html", products=get_products())

@app.route("/products/add", methods=["GET", "POST"])
def product_add():
    if request.method == "POST":
        try:
            data = validate_product_form(request.form)
            add_product(data)
            flash("Product added successfully.", "success")
            return redirect(url_for("products"))
        except (ValueError, Error) as exc:
            flash(f"Could not add product: {exc}", "error")
    return render_template("product_form.html", product=None, form=request.form)

@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def product_edit(product_id):
    product = get_product(product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("products"))
    if request.method == "POST":
        try:
            data = validate_product_form(request.form)
            update_product(product_id, data)
            flash("Product updated successfully.", "success")
            return redirect(url_for("products"))
        except (ValueError, Error) as exc:
            flash(f"Could not update product: {exc}", "error")
    return render_template("product_form.html", product=product, form=request.form)

def validate_product_form(form):
    sku = form.get("sku", "").strip()
    name = form.get("product_name", "").strip()
    category = form.get("category", "").strip()
    if not sku or not name or not category:
        raise ValueError("SKU, product name, and category are required.")
    opening = int(form.get("opening_stock", "0"))
    reorder = int(form.get("reorder_level", "0"))
    cost = float(form.get("unit_cost", "0"))
    if opening < 0 or reorder < 0 or cost < 0:
        raise ValueError("Stock, reorder level, and cost cannot be negative.")
    return {"sku": sku, "product_name": name, "category": category,
            "opening_stock": opening, "reorder_level": reorder, "unit_cost": cost}

@app.route("/suppliers")
def suppliers():
    return render_template("suppliers.html", suppliers=get_suppliers())

@app.route("/suppliers/add", methods=["GET", "POST"])
def supplier_add():
    if request.method == "POST":
        name = request.form.get("supplier_name", "").strip()
        if not name:
            flash("Supplier name is required.", "error")
        else:
            try:
                add_supplier(request.form)
                flash("Supplier added successfully.", "success")
                return redirect(url_for("suppliers"))
            except Error as exc:
                flash(f"Could not add supplier: {exc}", "error")
    return render_template("supplier_form.html", form=request.form)

@app.route("/transactions")
def transactions():
    return render_template("transactions.html", transactions=get_transactions())

@app.route("/transactions/add", methods=["GET", "POST"])
def transaction_add():
    products = get_products()
    suppliers_list = get_suppliers()
    if request.method == "POST":
        try:
            create_transaction(request.form)
            flash("Stock transaction recorded. Stock history has been updated.", "success")
            return redirect(url_for("transactions"))
        except (ValueError, Error) as exc:
            flash(f"Transaction was not saved: {exc}", "error")
    return render_template("transaction_form.html", products=products,
                           suppliers=suppliers_list, form=request.form)

@app.route("/reports")
def reports():
    products = get_products()
    movement = get_movement_report()
    low_stock = get_low_stock()
    total_value = sum(max(0, int(p["current_stock"])) * float(p["unit_cost"]) for p in products)
    make_charts(products, movement)
    return render_template("reports.html", products=products, movement=movement,
                           low_stock=low_stock, total_value=total_value)

@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", message="The page you requested was not found.",
                           details="Check the address or use the navigation menu."), 404

if __name__ == "__main__":
    app.run(debug=True)
