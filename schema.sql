CREATE DATABASE IF NOT EXISTS stock_inventory_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE stock_inventory_db;

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_name VARCHAR(150) NOT NULL,
    phone VARCHAR(30),
    email VARCHAR(150),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(60) NOT NULL UNIQUE,
    product_name VARCHAR(180) NOT NULL,
    category VARCHAR(100) NOT NULL,
    opening_stock INT NOT NULL DEFAULT 0,
    reorder_level INT NOT NULL DEFAULT 0,
    unit_cost DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_opening_stock CHECK (opening_stock >= 0),
    CONSTRAINT chk_reorder_level CHECK (reorder_level >= 0),
    CONSTRAINT chk_unit_cost CHECK (unit_cost >= 0)
);

CREATE TABLE IF NOT EXISTS stock_transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    transaction_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    transaction_type ENUM('IN', 'OUT', 'ADJUSTMENT_IN', 'ADJUSTMENT_OUT') NOT NULL,
    quantity INT NOT NULL,
    supplier_id INT NULL,
    notes VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_transaction_quantity CHECK (quantity > 0),
    CONSTRAINT fk_transaction_product FOREIGN KEY (product_id)
      REFERENCES products(product_id),
    CONSTRAINT fk_transaction_supplier FOREIGN KEY (supplier_id)
      REFERENCES suppliers(supplier_id) ON DELETE SET NULL
);

CREATE INDEX idx_transactions_product_date
  ON stock_transactions(product_id, transaction_date);
CREATE INDEX idx_transactions_date
  ON stock_transactions(transaction_date);

-- Optional demo data. Uncomment and run only if you want sample records.
-- INSERT INTO suppliers (supplier_name, phone, email)
-- VALUES ('Demo Supplier', '9876543210', 'supplier@example.com');
-- INSERT INTO products (sku, product_name, category, opening_stock, reorder_level, unit_cost)
-- VALUES ('SKU-001', 'Notebook', 'Stationery', 100, 20, 45.00);
