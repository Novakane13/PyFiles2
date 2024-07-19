import sqlite3
import os
from datetime import datetime, timedelta
from PySide6.QtWidgets import QMainWindow, QListWidgetItem, QTreeWidgetItem, QVBoxLayout, QWidget, QComboBox, QPushButton, QApplication
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt
from views.Test import Ui_DetailedTicketCreation

class DetailedTicketWindow(QMainWindow):
    def __init__(self, customer_id=None, ticket_type=None):
        super().__init__()
        self.ui = Ui_DetailedTicketCreation()
        self.ui.setupUi(self)

        self.customer_id = customer_id
        self.ticket_type = ticket_type
        self.ticket_data = [{}, {}, {}]  # Initialize ticket data for three tabs
        self.ticket_assigned = [False, False, False]  # Track if a ticket number has been assigned to each tab

        self.ui.canceltbutton.clicked.connect(self.close)  # Close functionality
        self.ui.ptandtbutton.clicked.connect(self.complete_ticket)  # Complete ticket functionality
        self.ui.tctabs.currentChanged.connect(self.on_tab_change)  # Handle tab changes

        self.populate_widgets()
        self.populate_ticket_type_buttons()

        # Connect double click events for lists
        self.ui.glist.itemDoubleClicked.connect(lambda item: self.add_garment(item))
        
        # Connect single click events to select a garment
        self.ui.sglist.itemClicked.connect(self.select_garment)
        self.ui.sglist_2.itemClicked.connect(self.select_garment)
        self.ui.sglist_3.itemClicked.connect(self.select_garment)
        
        # Connect the "Add to Garment" button
        self.ui.addtogarmentbutton.clicked.connect(self.add_selected_options_to_garment)
        
        self.selected_garment_item = None

    def on_tab_change(self, index):
        # When the tab changes, load the data for the current ticket tab
        self.load_ticket_data(index)

    def populate_widgets(self):
        if not self.ticket_type:
            return

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Populate garments and their variations
        cursor.execute("""
            SELECT g.id, g.name, g.image, v.id, v.variation, COALESCE(p.price, 0) as price
            FROM cgarments g
            JOIN ticket_type_garments ttg ON g.id = ttg.garments_id
            LEFT JOIN cgarment_variations v ON g.id = v.cgarment_id
            LEFT JOIN prices p ON g.id = p.cgarment_id AND (v.id = p.variation_id OR p.variation_id IS NULL)
            WHERE ttg.ticket_type_id = ?
        """, (self.ticket_type,))
    
        garments = {}
        for row in cursor.fetchall():
            garment_id, garment_name, garment_image, variation_id, variation_name, price = row
            if garment_id not in garments:
                garments[garment_id] = {
                    'name': garment_name,
                    'image': garment_image,
                    'variations': [],
                    'price': price  # Add price here
                }
            if variation_id:
                garments[garment_id]['variations'].append((variation_name, price))  # Add variation price

        for garment_id, garment_info in garments.items():
            garment_item = QListWidgetItem(QIcon(garment_info['image']), f"{garment_info['name']} - ${garment_info['price']:.2f}")
            self.ui.glist.addItem(garment_item)

            for variation_name, variation_price in garment_info['variations']:
                variation_item = QListWidgetItem(f" - {variation_name} - ${variation_price:.2f}")
                self.ui.glist.addItem(variation_item)

        # Populate colors
        cursor.execute("""
            SELECT c.name
            FROM colors c
            JOIN ticket_type_colors ttc ON c.id = ttc.colors_id
            WHERE ttc.ticket_type_id = ?
        """, (self.ticket_type,))
        colors = cursor.fetchall()
        for color in colors:
            item = QListWidgetItem(color[0])
            item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.ui.clist.addItem(item)

        # Populate patterns
        cursor.execute("""
            SELECT p.name
            FROM patterns p
            JOIN ticket_type_patterns ttp ON p.id = ttp.patterns_id
            WHERE ttp.ticket_type_id = ?
        """, (self.ticket_type,))
        patterns = cursor.fetchall()
        for pattern in patterns:
            item = QListWidgetItem(pattern[0])
            item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.ui.plist.addItem(item)

        # Populate textures
        cursor.execute("""
            SELECT t.name
            FROM textures t
            JOIN ticket_type_textures ttt ON t.id = ttt.textures_id
            WHERE ttt.ticket_type_id = ?
        """, (self.ticket_type,))
        textures = cursor.fetchall()
        for texture in textures:
            item = QListWidgetItem(texture[0])
            item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.ui.tlist.addItem(item)

        # Populate upcharges
        cursor.execute("""
            SELECT u.name
            FROM upcharges u
            JOIN ticket_type_upcharges ttu ON u.id = ttu.upcharges_id
            WHERE ttu.ticket_type_id = ?
        """, (self.ticket_type,))
        upcharges = cursor.fetchall()
        for upcharge in upcharges:
            item = QListWidgetItem(upcharge[0])
            item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.ui.ulist.addItem(item)

        conn.close()

    def populate_ticket_type_buttons(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, ticket_type_name FROM ticket_types")
        ticket_types = cursor.fetchall()

        layout = QVBoxLayout(self.ui.tickettypebuttonwidget)  # Assuming tickettypebuttonwidget is a placeholder widget in your UI

        for ticket_type_id, ticket_type_name in ticket_types:
            button = QPushButton(ticket_type_name)
            button.clicked.connect(lambda checked, tt_id=ticket_type_id: self.load_ticket_type(tt_id))
            layout.addWidget(button)

        conn.close()

    def load_ticket_type(self, ticket_type):
        self.ticket_type = ticket_type
        self.populate_widgets()

    def load_ticket_data(self, index):
        # Load the ticket data for the given tab index
        ticket_data = self.ticket_data[index]
        self.get_current_garment_list().clear()
        if 'items' in ticket_data:
            for item_data in ticket_data['items']:
                item = QTreeWidgetItem(self.get_current_garment_list())
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

        garments = [item['garment'] for item in ticket_data['items']]
        colors = [option for item in ticket_data['items'] for option in item.get('colors', [])]
        textures = [option for item in ticket_data['items'] for option in item.get('textures', [])]
        patterns = [option for item in ticket_data['items'] for option in item.get('patterns', [])]
        upcharges = [option for item in ticket_data['items'] for option in item.get('upcharges', [])]
        total_garments = sum(item['quantity'] for item in ticket_data['items'])
        total_price = sum(float(item.get('price', 0)) for item in ticket_data['items'])  # Adjust based on actual pricing logic

        cursor.execute("""
            INSERT INTO tickets (customer_id, ticket_number, ticket_type, garments, colors, textures, patterns, upcharges, total_garments, date_created, date_due, total_price, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.customer_id,
            ticket_data['ticket_number'],
            ticket_data['ticket_type'],
            ', '.join(garments),
            ', '.join(colors),
            ', '.join(textures),
            ', '.join(patterns),
            ', '.join(upcharges),
            total_garments,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S'),  # Example due date logic
            total_price,
            self.created_by
        ))

        conn.commit()
        conn.close()

        print(f"Completed ticket: {ticket_data}")
        self.close()

    def add_garment(self, item):
        garment_name = item.text()
        quantity = self.ui.piecesinput.value()
        icon_path = "path_to_default_image.png"  # Update with actual path if available

        garment_item = QTreeWidgetItem()
        garment_item.setText(0, garment_name)
        garment_item.setText(1, str(quantity))
        garment_item.setIcon(0, QIcon(QPixmap(icon_path)))

        garment_data = {
            'garment_name': garment_name,
            'quantity': quantity,
            'colors': [],
            'textures': [],
            'patterns': [],
            'upcharges': [],
            'icon': icon_path
        }

        garment_item.setData(0, Qt.UserRole, garment_data)

        self.get_current_garment_list().addTopLevelItem(garment_item)
        self.selected_garment_item = garment_item

    def select_garment(self, item):
        self.selected_garment_item = item

    def add_option_to_garment(self, item, option_type):
        if self.selected_garment_item is None:
            return

        option_name = item.text()
        garment_data = self.selected_garment_item.data(0, Qt.UserRole)

        if option_type == 'colors' and len(garment_data['colors']) >= 3:
            return
        if option_type == 'textures' and len(garment_data['textures']) >= 2:
            return
        if option_type == 'patterns' and len(garment_data['patterns']) >= 2:
            return
        if option_type == 'upcharges' and len(garment_data['upcharges']) >= 3:
            return

        garment_data[option_type].append(option_name)
        self.selected_garment_item.setData(0, Qt.UserRole, garment_data)
        self.update_garment_details(self.selected_garment_item)

    def add_selected_options_to_garment(self):
        if self.selected_garment_item is None:
            return

        for option_list in [self.ui.clist, self.ui.plist, self.ui.tlist, self.ui.ulist]:
            for i in range(option_list.count()):
                item = option_list.item(i)
                if item.isSelected():
                    option_type = self.get_option_type(option_list)
                    self.add_option_to_garment(item, option_type)
                    item.setSelected(False)  # Deselect after adding

    def get_option_type(self, option_list):
        if option_list == self.ui.clist:
            return 'colors'
        elif option_list == self.ui.plist:
            return 'patterns'
        elif option_list == self.ui.tlist:
            return 'textures'
        elif option_list == self.ui.ulist:
            return 'upcharges'
        return None

    def update_garment_details(self, garment_item):
        garment_data = garment_item.data(0, Qt.UserRole)
        details = (
            f"Colors: {', '.join(garment_data['colors'])}\n"
            f"Textures: {', '.join(garment_data['textures'])}\n"
            f"Patterns: {', '.join(garment_data['patterns'])}\n"
            f"Upcharges: {', '.join(garment_data['upcharges'])}"
        )
        garment_item.setText(2, details)

    def get_current_garment_list(self):
        current_index = self.ui.tctabs.currentIndex()
        if current_index == 0:
            return self.ui.sglist
        elif current_index == 1:
            return self.ui.sglist_2
        elif current_index == 2:
            return self.ui.sglist_3
        return None

if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    window = DetailedTicketWindow()
    window.show()
    sys.exit(app.exec())
