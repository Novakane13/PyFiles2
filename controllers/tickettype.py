import sqlite3
import os
from PySide6.QtWidgets import QMainWindow, QListWidgetItem, QTreeWidgetItem, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from views.Test import Ui_TicketTypeCreation

class TicketTypeCreationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_TicketTypeCreation()
        self.ui.setupUi(self)

        # Connecting buttons to functions
        self.ui.deletettbutton.clicked.connect(self.close)
        self.ui.savettbutton.clicked.connect(self.save_ticket_type)

        # Double-click events to add items to chosen lists
        self.ui.clist.itemDoubleClicked.connect(lambda item: self.add_to_list(item, self.ui.cclist))
        self.ui.plist.itemDoubleClicked.connect(lambda item: self.add_to_list(item, self.ui.cpatterns))
        self.ui.tlist.itemDoubleClicked.connect(lambda item: self.add_to_list(item, self.ui.ctextures))
        self.ui.ulist.itemDoubleClicked.connect(lambda item: self.add_to_list(item, self.ui.cupcharges))
        self.ui.dlist.itemDoubleClicked.connect(lambda item: self.add_to_list(item, self.ui.cdiscounts))
        self.ui.glist.itemDoubleClicked.connect(lambda item: self.add_to_list(item, self.ui.cglist))

        self.load_options()

    def load_options(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, color FROM colors")
        colors = cursor.fetchall()
        for color_id, name, color in colors:
            item = QListWidgetItem(name)
            item.setBackground(QColor(color))
            item.setData(Qt.UserRole, color_id)
            self.ui.clist.addItem(item)

        cursor.execute("SELECT id, name FROM patterns")
        patterns = cursor.fetchall()
        for pattern_id, pattern in patterns:
            item = QListWidgetItem(pattern)
            item.setData(Qt.UserRole, pattern_id)
            self.ui.plist.addItem(item)

        cursor.execute("SELECT id, name FROM textures")
        textures = cursor.fetchall()
        for texture_id, texture in textures:
            item = QListWidgetItem(texture)
            item.setData(Qt.UserRole, texture_id)
            self.ui.tlist.addItem(item)

        cursor.execute("SELECT id, name, amount FROM upcharges")
        upcharges = cursor.fetchall()
        for upcharge_id, name, amount in upcharges:
            item = QListWidgetItem(f"{name} - ${amount}")
            item.setData(Qt.UserRole, upcharge_id)
            self.ui.ulist.addItem(item)

        cursor.execute("SELECT id, name, percent, amount FROM discounts")
        discounts = cursor.fetchall()
        for discount_id, name, percent, amount in discounts:
            if percent is not None:
                item = QListWidgetItem(f"{name} - {percent}% off")
            else:
                item = QListWidgetItem(f"{name} - ${amount} off")
            item.setData(Qt.UserRole, discount_id)
            self.ui.dlist.addItem(item)

        cursor.execute("SELECT id, name FROM cgarments")
        garments = cursor.fetchall()
        for garment_id, garment in garments:
            item = QListWidgetItem(garment)
            item.setData(Qt.UserRole, garment_id)
            self.ui.glist.addItem(item)

        cursor.execute("SELECT id, ticket_type_name FROM ticket_types")
        ticket_types = cursor.fetchall()
        for ticket_type_id, ticket_type_name in ticket_types:
            item = QListWidgetItem(ticket_type_name)
            item.setData(Qt.UserRole, ticket_type_id)
            self.ui.sttlist.addItem(item)

        conn.close()

    def add_to_list(self, item, target_list):
        existing_items = [target_list.item(i).text() for i in range(target_list.count())]
        if item.text() in existing_items:
            return
        new_item = QListWidgetItem(item.text())
        new_item.setData(Qt.UserRole, item.data(Qt.UserRole))
        target_list.addItem(new_item)

    def save_ticket_type(self):
        ticket_type_name = self.ui.ttinput.text().strip()
        if not ticket_type_name:
            QMessageBox.warning(self, "Input Error", "Please enter a ticket type name.")
            return

        chosen_garments = [self.ui.cglist.item(i).data(Qt.UserRole) for i in range(self.ui.cglist.count())]
        chosen_patterns = [self.ui.cpatterns.item(i).data(Qt.UserRole) for i in range(self.ui.cpatterns.count())]
        chosen_textures = [self.ui.ctextures.item(i).data(Qt.UserRole) for i in range(self.ui.ctextures.count())]
        chosen_colors = [self.ui.cclist.item(i).data(Qt.UserRole) for i in range(self.ui.cclist.count())]
        chosen_upcharges = [self.ui.cupcharges.item(i).data(Qt.UserRole) for i in range(self.ui.cupcharges.count())]
        chosen_discounts = [self.ui.cdiscounts.item(i).data(Qt.UserRole) for i in range(self.ui.cdiscounts.count())]

        if not (chosen_garments or chosen_patterns or chosen_textures or chosen_colors or chosen_upcharges or chosen_discounts):
            QMessageBox.warning(self, "Input Error", "Please select at least one option.")
            return

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO ticket_types (ticket_type_name) VALUES (?)", (ticket_type_name,))
        ticket_type_id = cursor.lastrowid

        def insert_into_table(table_name, ticket_type_id, item_ids):
            for item_id in item_ids:
                cursor.execute(f"INSERT INTO {table_name} (ticket_type_id, {table_name.split('_')[-1]}_id) VALUES (?, ?)", (ticket_type_id, item_id))

        insert_into_table("ticket_type_garments", ticket_type_id, chosen_garments)
        insert_into_table("ticket_type_patterns", ticket_type_id, chosen_patterns)
        insert_into_table("ticket_type_textures", ticket_type_id, chosen_textures)
        insert_into_table("ticket_type_colors", ticket_type_id, chosen_colors)
        insert_into_table("ticket_type_upcharges", ticket_type_id, chosen_upcharges)
        insert_into_table("ticket_type_discounts", ticket_type_id, chosen_discounts)

        conn.commit()
        conn.close()

        self.ui.sttlist.addItem(ticket_type_name)
        self.ui.ttinput.clear()
        self.ui.cglist.clear()
        self.ui.cpatterns.clear()
        self.ui.ctextures.clear()
        self.ui.cclist.clear()
        self.ui.cupcharges.clear()
        self.ui.cdiscounts.clear()
        self.load_options()

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = TicketTypeCreationWindow()
    window.show()
    sys.exit(app.exec())