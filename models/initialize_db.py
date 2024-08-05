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


# Create Garments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Garments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        image_path TEXT NOT NULL
    )
    """)

# Create Garment Variants Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS GarmentVariants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        garment_id INTEGER,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY (garment_id) REFERENCES Garments(id)
    )
    """)

# Create Colors Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Colors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        value TEXT NOT NULL
    )
    """)

# Create Patterns Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        image_path TEXT NOT NULL
    )
    """)

# Create Textures Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Textures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        image_path TEXT NOT NULL
    )
    """)

# Create Upcharges Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Upcharges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        price REAL NOT NULL
    )
    """)

# Create Ticket Types Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TicketTypes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """)

# Create Ticket Type Garments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TicketTypeGarments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_type_id INTEGER,
        garment_variant_id INTEGER,
        FOREIGN KEY (ticket_type_id) REFERENCES TicketTypes(id),
        FOREIGN KEY (garment_variant_id) REFERENCES GarmentVariants(id)
    )
    """)

# Create Ticket Type Colors Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ticket_type_colors (
        ticket_type_id INTEGER,
        color_id INTEGER,
        FOREIGN KEY (ticket_type_id) REFERENCES TicketTypes(id),
        FOREIGN KEY (color_id) REFERENCES Colors(id)
    )
    """)

# Create Ticket Type Textures Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ticket_type_textures (
        ticket_type_id INTEGER,
        texture_id INTEGER,
        FOREIGN KEY (ticket_type_id) REFERENCES TicketTypes(id),
        FOREIGN KEY (texture_id) REFERENCES Textures(id)
    )
    """)

# Create Ticket Type Patterns Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ticket_type_patterns (
        ticket_type_id INTEGER,
        pattern_id INTEGER,
        FOREIGN KEY (ticket_type_id) REFERENCES TicketTypes(id),
        FOREIGN KEY (pattern_id) REFERENCES Patterns(id)
    )
    """)

# Create Ticket Type Upcharges Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ticket_type_upcharges (
        ticket_type_id INTEGER,
        upcharge_id INTEGER,
        FOREIGN KEY (ticket_type_id) REFERENCES TicketTypes(id),
        FOREIGN KEY (upcharge_id) REFERENCES Upcharges(id)
    )
    """)

# Create Tickets Table
    cursor.execute("""
    CREATE TABLE "Tickets" (
	    "id"	INTEGER,
	    "customer_id"	INTEGER,
	    "ticket_type_id"	INTEGER,
	    "employee_id" INTEGER,
	    "ticket_number"	INTEGER NOT NULL,
	    "total_price"	REAL NOT NULL,
	    "date_created"	TEXT NOT NULL,
	    "date_due"	TEXT NOT NULL,
	    "status"	TEXT,
	    FOREIGN KEY("ticket_type_id") REFERENCES "TicketTypes"("id"),
	    FOREIGN KEY("customer_id") REFERENCES "Customers"("id"),
	    FOREIGN KEY("employee_id") REFERENCES "Employees"("id"),
	    PRIMARY KEY("id" AUTOINCREMENT)
)
    """)

# Create Ticket Garments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TicketGarments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER,
        garment_variant_id INTEGER,
        color_id INTEGER,
        pattern_id INTEGER,
        texture_id INTEGER,
        upcharge_id INTEGER,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY (ticket_id) REFERENCES Tickets(id),
        FOREIGN KEY (garment_variant_id) REFERENCES GarmentVariants(id),
        FOREIGN KEY (color_id) REFERENCES Colors(id),
        FOREIGN KEY (pattern_id) REFERENCES Patterns(id),
        FOREIGN KEY (texture_id) REFERENCES Textures(id),
        FOREIGN KEY (upcharge_id) REFERENCES Upcharges(id)
    )
    """)

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
