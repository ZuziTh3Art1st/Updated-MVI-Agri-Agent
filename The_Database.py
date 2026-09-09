import sqlite3
from datetime import datetime

DB_NAME = "the_farm_agent.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Master inventory table with agronomic parameters
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            stock_qty INTEGER NOT NULL CHECK(stock_qty >= 0),
            unit_price REAL NOT NULL,
            dosage_guideline TEXT NOT NULL,
            ecocert_certified INTEGER DEFAULT 1
        )
    """)

    # POPIA Compliance isolated client table (PII isolation)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS popia_encrypted_clients (
            farmer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone_contact TEXT NOT NULL,
            delivery_location TEXT NOT NULL,
            consent_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Transactional order commitment table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders_commitment (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            total_cost REAL NOT NULL,
            order_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            order_status TEXT DEFAULT 'Reserved',
            FOREIGN KEY (farmer_id) REFERENCES popia_encrypted_clients(farmer_id)
        )
    """)

    # Seed baseline inventory if empty
    cursor.execute("SELECT COUNT(*) FROM inventory_master")
    if cursor.fetchone()[0] == 0:
        seed_inventory = [
            ("BioBoost 250ml", "Organic Fertilizer", 120, 185.00, "5ml per 1L of water weekly", 1),
            ("BioBoost 1L", "Organic Fertilizer", 65, 520.00, "20ml per 5L of water bi-weekly", 1),
            ("HydroCache Granules 500g", "Soil Enhancer", 80, 240.00, "15g per planting hole", 1),
            ("Carbon+ Soil Activator 5L", "Microbial Soil Treatment", 40, 780.00, "50ml per 10L of water", 1),
            ("BioShield Pest Repel 500ml", "Biological Pest Protection", 55, 310.00, "10ml per 1L spray solution", 1),
            ("NitroGrow Pellets 10kg", "Soil Nutrition", 30, 450.00, "100g per square meter", 1)
        ]
        cursor.executemany("""
            INSERT INTO inventory_master 
            (product_name, category, stock_qty, unit_price, dosage_guideline, ecocert_certified)
            VALUES (?, ?, ?, ?, ?, ?)
        """, seed_inventory)
    
    conn.commit()
    conn.close()

def fetch_inventory():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, category, stock_qty, unit_price, dosage_guideline FROM inventory_master")
    rows = cursor.fetchall()
    conn.close()
    return rows

def process_order_transaction(farmer_name, phone, location, product_name, quantity):
    """
    Executes an atomic ACID transaction locking stock and persisting buyer records.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE")
        
        # 1. Verify stock availability
        cursor.execute("SELECT stock_qty, unit_price FROM inventory_master WHERE product_name = ?", (product_name,))
        item = cursor.fetchone()
        if not item:
            conn.rollback()
            return False, f"Product '{product_name}' does not exist in inventory."
        
        stock_qty, unit_price = item
        if stock_qty < quantity:
            conn.rollback()
            return False, f"Insufficient stock: {stock_qty} units available, {quantity} requested."

        # 2. Record POPIA client details
        cursor.execute("""
            INSERT INTO popia_encrypted_clients (full_name, phone_contact, delivery_location)
            VALUES (?, ?, ?)
        """, (farmer_name, phone, location))
        farmer_id = cursor.lastrowid

        # 3. Deduct stock atomically
        new_stock = stock_qty - quantity
        cursor.execute("UPDATE inventory_master SET stock_qty = ? WHERE product_name = ?", (new_stock, product_name))

        # 4. Insert binding order commitment
        total_cost = unit_price * quantity
        cursor.execute("""
            INSERT INTO orders_commitment (farmer_id, product_name, quantity, total_cost)
            VALUES (?, ?, ?, ?)
        """, (farmer_id, product_name, quantity, total_cost))
        order_id = cursor.lastrowid

        conn.commit()
        return True, {
            "order_id": order_id,
            "product": product_name,
            "quantity": quantity,
            "total_cost": total_cost,
            "remaining_stock": new_stock
        }
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")