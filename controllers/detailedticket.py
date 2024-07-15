import sqlite3
import os
from PySide6.QtWidgets import QMainWindow, QListWidgetItem, QSpinBox, QTreeWidgetItem
from PySide6.QtGui import QIcon, QPixmap
from views.Test import Ui_DetailedTicketCreation

class DetailedTicketWindow(QMainWindow):
    def __init__(self, customer_id=None):
        super().__init__()
        self.ui = Ui_DetailedTicketCreation()
        self.ui.setupUi(self)

        self.ticket_data = [{}, {}, {}]  # Initialize ticket data for three tabs
        self.ticket_assigned = [False, False, False]  # Track if a ticket number has been assigned to each tab

        self.ui.canceltbutton.clicked.connect(self.close)  # Close functionality
        self.ui.ptandtbutton.clicked.connect(self.complete_ticket)  # Complete ticket functionality
        self.ui.tctabs.currentChanged.connect(self.on_tab_change)  # Handle tab changes

        self.ui.pushButton_7.clicked.connect(lambda: self.create_ticket(0, "Dry Clean"))
        self.ui.pushButton_8.clicked.connect(lambda: self.create_ticket(1, "Laundry"))
        self.ui.pushButton_9.clicked.connect(lambda: self.create_ticket(2, "Household"))
        self.ui.pushButton_10.clicked.connect(lambda: self.create_ticket(3, "Alteration"))
        self.ui.ctbutton.clicked.connect(self.create_ticket_entry)
        self.populate_widgets()

    def on_tab_change(self, index):
        # When the tab changes, load the data for the current ticket tab
        self.load_ticket_data(index)

    def populate_widgets(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Populate garments
        cursor.execute("SELECT name FROM cgarments")
        garments = cursor.fetchall()
        for garment in garments:
            item = QListWidgetItem(garment[0])
            self.ui.glist.addItem(item)

        # Populate colors
        cursor.execute("SELECT name FROM colors")
        colors = cursor.fetchall()
        for color in colors:
            item = QListWidgetItem(color[0])
            self.ui.clist.addItem(item)

        # Populate patterns
        cursor.execute("SELECT name FROM patterns")
        patterns = cursor.fetchall()
        for pattern in patterns:
            item = QListWidgetItem(pattern[0])
            self.ui.plist.addItem(item)

        # Populate textures
        cursor.execute("SELECT name FROM textures")
        textures = cursor.fetchall()
        for texture in textures:
            item = QListWidgetItem(texture[0])
            self.ui.tlist.addItem(item)

        # Populate upcharges
        cursor.execute("SELECT name FROM upcharges")
        upcharges = cursor.fetchall()
        for upcharge in upcharges:
            item = QListWidgetItem(upcharge[0])
            self.ui.ulist.addItem(item)

        conn.close()

    def load_ticket_data(self, index):
        # Load the ticket data for the given tab index
        ticket_data = self.ticket_data[index]
        self.ui.sglist.clear()
        if 'items' in ticket_data:
            for item_data in ticket_data['items']:
                item = QTreeWidgetItem(self.ui.sglist)
                item.setText(1, item_data['garment'])
                item.setText(2, item_data['details'])
                item.setIcon(0, QIcon(QPixmap(item_data['icon'])))
                item.setText(0, str(item_data['quantity']))

    def create_ticket(self, index, ticket_type):
        if not self.ticket_assigned[index]:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            db_path = os.path.join(project_root, 'models', 'pos_system.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Fetch the next ticket number
            cursor.execute("SELECT MAX(ticket_number) FROM ticket_numbers")
            max_ticket_number = cursor.fetchone()[0]
            next_ticket_number = max_ticket_number + 1 if max_ticket_number else 1

            cursor.execute("INSERT INTO ticket_numbers (ticket_number) VALUES (?)", (next_ticket_number,))
            conn.commit()
            conn.close()

            self.ticket_data[index]['ticket_number'] = next_ticket_number
            self.ticket_data[index]['ticket_type'] = ticket_type
            self.ticket_assigned[index] = True
            self.ui.tctabs.setTabText(index, f"Ticket {next_ticket_number}")
            self.ui.ttname.setPlainText(ticket_type)

    def create_ticket_entry(self):
        current_index = self.ui.tctabs.currentIndex()
        ticket_data = self.ticket_data[current_index]

        selected_garment = self.ui.glist.currentItem().text() if self.ui.glist.currentItem() else ""
        selected_color = self.ui.clist.currentItem().text() if self.ui.clist.currentItem() else ""
        selected_pattern = self.ui.plist.currentItem().text() if self.ui.plist.currentItem() else ""
        selected_texture = self.ui.tlist.currentItem().text() if self.ui.tlist.currentItem() else ""
        selected_upcharges = [self.ui.ulist.item(i).text() for i in range(self.ui.ulist.count()) if self.ui.ulist.item(i).isSelected()]
        quantity = self.ui.piecesinput.value()

        details = f"{selected_color}, {selected_pattern}, {selected_texture}, {', '.join(selected_upcharges)}"
        icon_path = "path_to_default_image.png"  # Update with actual path if available

        item_data = {
            'garment': selected_garment,
            'details': details,
            'icon': icon_path,
            'quantity': quantity
        }

        if 'items' not in ticket_data:
            ticket_data['items'] = []

        ticket_data['items'].append(item_data)
        self.load_ticket_data(current_index)

    def complete_ticket(self):
        current_index = self.ui.tctabs.currentIndex()
        ticket_data = self.ticket_data[current_index]

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Save ticket data to database
        cursor.execute("INSERT INTO detailed_tickets (ticket_number, ticket_type) VALUES (?, ?)",
                       (ticket_data['ticket_number'], ticket_data['ticket_type']))
        detailed_ticket_id = cursor.lastrowid

        for item_data in ticket_data['items']:
            cursor.execute("""
                INSERT INTO detailed_ticket_items (detailed_ticket_id, garment, details, icon, quantity)
                VALUES (?, ?, ?, ?, ?)
            """, (detailed_ticket_id, item_data['garment'], item_data['details'], item_data['icon'], item_data['quantity']))

        conn.commit()
        conn.close()

        print(f"Completed ticket: {ticket_data}")
        self.close()

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = DetailedTicketWindow()
    window.show()
    sys.exit(app.exec())
