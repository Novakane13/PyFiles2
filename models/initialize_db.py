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

    # Create tickets table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        ticket_type_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(id),
        FOREIGN KEY (ticket_type_id) REFERENCES ticket_types(id)
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
    
    # Create quick tickets table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quick_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER NOT NULL,
        ticket_number INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        ticket_type TEXT NOT NULL,
        due_date TEXT NOT NULL,
        pieces INTEGER NOT NULL,
        notes TEXT,
        all_notes TEXT,
        FOREIGN KEY (ticket_id) REFERENCES tickets(id),
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    )
    ''')
    
    # Create table for tracking ticket numbers
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ticket_numbers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_number INTEGER NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")
