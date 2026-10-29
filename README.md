# Stock Inventory Analysis System

A beginner-friendly inventory web application built with Flask, MySQL, Pandas, NumPy, and Matplotlib.

## Features

- Manage products, opening stock, unit costs, and reorder levels.
- Maintain a supplier directory.
- Record stock-in and stock-out movements with date, quantity, supplier, and notes.
- Calculate current stock as opening stock + stock-in - stock-out.
- Reject stock-out transactions that exceed available stock.
- Keep transaction history for reconciliation.
- Identify items at or below the configured reorder level.
- Estimate inventory value from current stock × unit cost.
- Show Pandas movement summaries and Matplotlib charts.
- Search product and transaction tables.

## Folder overview

- `app.py`: Flask routes and chart generation.
- `database.py`: MySQL connection helpers.
- `config.py`: environment-based configuration.
- `database/schema.sql`: database and table definitions.
- `services/inventory_service.py`: inventory queries, validation, and analysis.
- `templates/`: HTML pages.
- `static/`: CSS, JavaScript, and generated charts.
- `tests/`: basic inventory calculation tests.

## Requirements

- Python 3.10 or newer
- MySQL Server (MySQL Workbench is optional)
- Git (optional until the GitHub step)

## Setup on Windows

### 1. Create the MySQL database

1. Start your MySQL server.
2. Open MySQL Workbench or the MySQL command-line client.
3. Open `database/schema.sql`.
4. Execute the entire script.

The script creates a database named `stock_inventory_db` and its three tables: `products`, `suppliers`, and `stock_transactions`.

### 2. Open the project in a terminal

Open Command Prompt in the `stock-inventory-analysis` folder. In File Explorer, you can open the folder, click the address bar, type `cmd`, and press Enter.

### 3. Create a virtual environment

```bat
py -m venv .venv
.venv\Scripts\activate
```

If `py` is not recognized, install Python from the official Python website and select the option to add Python to PATH during setup.

### 4. Install the Python packages

```bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure MySQL

1. Copy `.env.example` and rename the copy to `.env`.
2. Open `.env` in Notepad.
3. Enter your actual MySQL username and password.
4. Save the file.

Example for a local MySQL installation:

```text
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_actual_password
DB_NAME=stock_inventory_db
FLASK_SECRET_KEY=use-a-long-random-value
```

Do not commit `.env` to GitHub. It is ignored by `.gitignore`.

### 6. Start the website

```bat
python app.py
```

Wait until Flask prints a local address, usually `http://127.0.0.1:5000`.

Open that address in your browser. Keep the terminal open while using the application. Press `Ctrl+C` in the terminal to stop it.

## First-use order

1. Add one or more suppliers.
2. Add products and set each product's opening stock, unit cost, and reorder level.
3. Record stock-in or stock-out movements.
4. Open Dashboard to see totals and charts.
5. Open Reports & charts to review low-stock items, movement summaries, and estimated inventory value.

### Important stock rule

Opening stock is the starting balance entered when creating a product. Subsequent stock changes should be recorded through transactions. Avoid editing opening stock after movements have been recorded, because changing the starting balance changes the reconstructed stock history.

Stock-out requests are validated inside a database transaction while the product row is locked. This helps prevent concurrent requests from issuing more stock than is available.

## Run tests

The calculation tests do not require a live MySQL connection:

```bat
python -m unittest discover -s tests -v
```

## Push to GitHub

Install Git for Windows if `git` is not recognized. Close and reopen Command Prompt after installation, then verify:

```bat
git --version
```

From the project folder:

```bat
git init
git add .
git commit -m "Initial stock inventory analysis system"
```

Create an empty repository on GitHub. Do not initialize it with a README or license if you already have this project README. Then use the repository URL GitHub shows you:

```bat
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with your actual repository URL. Never push your `.env` file or real database password.

## Troubleshooting

- **Access denied for user**: confirm the MySQL username and password in `.env`.
- **Unknown database**: run `database/schema.sql` in MySQL.
- **Can't connect to MySQL server**: make sure the MySQL service is running and the port is correct.
- **ModuleNotFoundError**: activate `.venv` and run `pip install -r requirements.txt`.
- **Port 5000 is in use**: stop the other app using it, or change the final `app.run` line to `app.run(debug=True, port=5001)` and open `http://127.0.0.1:5001`.
- **Git is not recognized**: install Git for Windows, reopen the terminal, and run `git --version`.

## Project boundaries

This project produces reorder recommendations only. It does not place supplier orders or purchase stock automatically.
