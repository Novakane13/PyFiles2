import sqlite3
import os

def initialize_database():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path = os.path.join(project_root, 'models', 'pos_system.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create customers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create ticket types table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ticket_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        garments TEXT,
        patterns TEXT,
        textures TEXT,
        colors TEXT,
        upcharges TEXT,
        discounts TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create created garments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cgarments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        image TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
        # Create created garment variations table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cgarment_variations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cgarment_id INTEGER NOT NULL,
        variation TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (cgarment_id) REFERENCES cgarments(id)
    )
    ''')

    # Create colors table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS colors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        color TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create patterns table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        image TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create textures table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS textures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        image TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create upcharges table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS upcharges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        amount REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create discounts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS discounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        percent REAL,
        amount REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''    
    CREATE TABLE IF NOT EXISTS prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cgarment_id INTEGER,
        variation_id INTEGER,
        price REAL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create table for tracking ticket numbers
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ticket_numbers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_number INTEGER NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        ticket_number INTEGER,
        ticket_type TEXT,
        garments TEXT,
        colors TEXT,
        textures TEXT,
        patterns TEXT,
        upcharges TEXT,
        status TEXT,
        total_garments INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        date_created DATE,
        date_due DATE,
        total_price REAL,
        created_by TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    )
    ''')

    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")
