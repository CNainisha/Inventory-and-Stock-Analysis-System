"""Small unit tests for inventory calculation rules.

Run from the project root with:
    python -m unittest discover -s tests -v
"""
import unittest

def calculate_stock(opening_stock, transactions):
    """transactions is a list of (type, quantity) pairs."""
    stock = opening_stock
    for transaction_type, quantity in transactions:
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if transaction_type in ("IN", "ADJUSTMENT_IN"):
            stock += quantity
        elif transaction_type in ("OUT", "ADJUSTMENT_OUT"):
            if quantity > stock:
                raise ValueError("Stock cannot become negative.")
            stock -= quantity
        else:
            raise ValueError("Unknown transaction type.")
    return stock

class InventoryCalculationTests(unittest.TestCase):
    def test_opening_stock_and_movements(self):
        self.assertEqual(calculate_stock(10, [("IN", 5), ("OUT", 3)]), 12)

    def test_stock_cannot_become_negative(self):
        with self.assertRaises(ValueError):
            calculate_stock(2, [("OUT", 3)])

    def test_quantity_must_be_positive(self):
        with self.assertRaises(ValueError):
            calculate_stock(10, [("IN", 0)])

if __name__ == "__main__":
    unittest.main()
