from database import get_connection, query_all, query_one
import pandas as pd
import numpy as np

STOCK_SQL = """
SELECT p.product_id, p.sku, p.product_name, p.category, p.opening_stock,
       p.reorder_level, p.unit_cost,
       p.opening_stock
         + COALESCE(SUM(
             CASE
               WHEN t.transaction_type IN ('IN', 'ADJUSTMENT_IN') THEN t.quantity
               WHEN t.transaction_type IN ('OUT', 'ADJUSTMENT_OUT') THEN -t.quantity
               ELSE 0
             END
           ), 0) AS current_stock
FROM products p
LEFT JOIN stock_transactions t ON t.product_id = p.product_id
"""

def get_stock_rows(where_sql="", params=()):
    sql = STOCK_SQL + " "
    if where_sql:
        sql += where_sql + " "
    sql += """GROUP BY p.product_id, p.sku, p.product_name, p.category,
              p.opening_stock, p.reorder_level, p.unit_cost
              ORDER BY p.product_name"""
    return query_all(sql, params)

def get_dashboard_data():
    products = get_stock_rows()
    df = pd.DataFrame(products)
    if df.empty:
        return {
            "products": [], "product_count": 0, "total_units": 0,
            "low_stock_count": 0, "inventory_value": 0.0,
            "recent_transactions": [], "movement_summary": {"IN": 0, "OUT": 0},
        }

    df["current_stock"] = pd.to_numeric(df["current_stock"])
    df["unit_cost"] = pd.to_numeric(df["unit_cost"])
    df["stock_value"] = np.maximum(df["current_stock"], 0) * df["unit_cost"]
    low_stock = df[df["current_stock"] <= df["reorder_level"]]
    movement = query_all("""
        SELECT transaction_type, COALESCE(SUM(quantity), 0) AS total_quantity
        FROM stock_transactions
        GROUP BY transaction_type
    """)
    movement_summary = {"IN": 0, "OUT": 0}
    for row in movement:
        if row["transaction_type"] in ("IN", "ADJUSTMENT_IN"):
            movement_summary["IN"] += int(row["total_quantity"])
        else:
            movement_summary["OUT"] += int(row["total_quantity"])

    recent = query_all("""
        SELECT t.transaction_id, t.transaction_date, t.transaction_type,
               t.quantity, t.notes, p.product_name, p.sku,
               s.supplier_name
        FROM stock_transactions t
        JOIN products p ON p.product_id = t.product_id
        LEFT JOIN suppliers s ON s.supplier_id = t.supplier_id
        ORDER BY t.transaction_date DESC, t.transaction_id DESC
        LIMIT 8
    """)
    records = df.replace({np.nan: None}).to_dict(orient="records")
    return {
        "products": records,
        "product_count": len(df),
        "total_units": int(df["current_stock"].sum()),
        "low_stock_count": len(low_stock),
        "inventory_value": float(df["stock_value"].sum()),
        "recent_transactions": recent,
        "movement_summary": movement_summary,
    }

def add_product(data):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO products (sku, product_name, category, opening_stock, reorder_level, unit_cost)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data["sku"].strip(), data["product_name"].strip(), data["category"].strip(),
            int(data["opening_stock"]), int(data["reorder_level"]), float(data["unit_cost"])
        ))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

def update_product(product_id, data):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE products
            SET sku=%s, product_name=%s, category=%s, opening_stock=%s,
                reorder_level=%s, unit_cost=%s
            WHERE product_id=%s
        """, (
            data["sku"].strip(), data["product_name"].strip(), data["category"].strip(),
            int(data["opening_stock"]), int(data["reorder_level"]), float(data["unit_cost"]),
            product_id
        ))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

def add_supplier(data):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO suppliers (supplier_name, phone, email)
            VALUES (%s, %s, %s)
        """, (data["supplier_name"].strip(), data.get("phone", "").strip(),
              data.get("email", "").strip()))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

def create_transaction(data):
    product_id = int(data["product_id"])
    quantity = int(data["quantity"])
    transaction_type = data["transaction_type"]
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")
    if transaction_type not in ("IN", "OUT"):
        raise ValueError("Choose Stock In or Stock Out.")

    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        # Lock the product row while checking stock and recording the transaction.
        cur.execute("SELECT product_id, opening_stock FROM products WHERE product_id=%s FOR UPDATE",
                    (product_id,))
        product = cur.fetchone()
        if not product:
            raise ValueError("The selected product does not exist.")

        cur.execute("""
            SELECT COALESCE(SUM(
                CASE
                  WHEN transaction_type IN ('IN', 'ADJUSTMENT_IN') THEN quantity
                  WHEN transaction_type IN ('OUT', 'ADJUSTMENT_OUT') THEN -quantity
                  ELSE 0
                END
            ), 0) AS movement
            FROM stock_transactions WHERE product_id=%s
        """, (product_id,))
        movement = int(cur.fetchone()["movement"])
        current_stock = int(product["opening_stock"]) + movement
        if transaction_type == "OUT" and quantity > current_stock:
            raise ValueError(
                f"Insufficient stock. Current stock is {current_stock}; "
                f"you cannot issue {quantity} units."
            )

        supplier_id = data.get("supplier_id") or None
        if supplier_id:
            supplier_id = int(supplier_id)
        notes = data.get("notes", "").strip() or None
        cur.execute("""
            INSERT INTO stock_transactions
              (product_id, transaction_type, quantity, supplier_id, notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (product_id, transaction_type, quantity, supplier_id, notes))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

def get_movement_report():
    rows = query_all("""
        SELECT p.product_id, p.sku, p.product_name,
               COALESCE(SUM(CASE WHEN t.transaction_type IN ('IN','ADJUSTMENT_IN')
                                 THEN t.quantity ELSE 0 END), 0) AS stock_in,
               COALESCE(SUM(CASE WHEN t.transaction_type IN ('OUT','ADJUSTMENT_OUT')
                                 THEN t.quantity ELSE 0 END), 0) AS stock_out
        FROM products p
        LEFT JOIN stock_transactions t ON t.product_id=p.product_id
        GROUP BY p.product_id, p.sku, p.product_name
        ORDER BY stock_out DESC, p.product_name
    """)
    df = pd.DataFrame(rows)
    if not df.empty:
        df["stock_in"] = pd.to_numeric(df["stock_in"])
        df["stock_out"] = pd.to_numeric(df["stock_out"])
        df["net_movement"] = df["stock_in"] - df["stock_out"]
        # NumPy calculation is used to demonstrate the data-analysis component.
        df["total_movement"] = np.abs(df["stock_in"]) + np.abs(df["stock_out"])
    return df.to_dict(orient="records") if not df.empty else []

def get_transactions():
    return query_all("""
        SELECT t.transaction_id, t.transaction_date, t.transaction_type,
               t.quantity, t.notes, p.product_name, p.sku, s.supplier_name
        FROM stock_transactions t
        JOIN products p ON p.product_id=t.product_id
        LEFT JOIN suppliers s ON s.supplier_id=t.supplier_id
        ORDER BY t.transaction_date DESC, t.transaction_id DESC
    """)

def get_suppliers():
    return query_all("SELECT * FROM suppliers ORDER BY supplier_name")

def get_products():
    return get_stock_rows()

def get_product(product_id):
    rows = query_all("SELECT * FROM products WHERE product_id=%s", (product_id,))
    return rows[0] if rows else None

def get_low_stock():
    return [p for p in get_stock_rows() if int(p["current_stock"]) <= int(p["reorder_level"])]
