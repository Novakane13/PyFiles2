import sqlite3
import os
from PySide6.QtWidgets import QMainWindow, QListWidgetItem, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from views.tickettypeui import Ui_TicketTypeCreation

class TicketTypeCreationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_TicketTypeCreation()
        self.ui.setupUi(self)

        # Connecting buttons to functions
        self.ui.deletettbutton.clicked.connect(self.delete_ticket_type)
        self.ui.savettbutton.clicked.connect(self.save_ticket_type)

        # Double-click events to add items to chosen lists
        self.ui.clist.itemDoubleClicked.connect(lambda item: self.add_to_list(item, self.ui.cclist))
        self.ui.plist.itemDoubleClicked.connect(lambda item: self.add_to_list(item, self.ui.cpatterns))
        self.ui.tlist.itemDoubleClicked.connect(lambda item: self.add_to_list(item, self.ui.ctextures))
        self.ui.ulist.itemDoubleClicked.connect(lambda item: self.add_to_list(item, self.ui.cupcharges))
        self.ui.dlist.itemDoubleClicked.connect(lambda item: self.add_to_list(item, self.ui.cdiscounts))
        self.ui.glist.itemDoubleClicked.connect(lambda item: self.add_to_list(item, self.ui.cglist))

        self.load_options()
        self.load_ticket_types()

    def load_options(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, value FROM Colors")
        colors = cursor.fetchall()
        for color_id, name, value in colors:
            item = QListWidgetItem(name)
            item.setBackground(QColor(value))
            item.setData(Qt.UserRole, (color_id, value))
            self.ui.clist.addItem(item)

        cursor.execute("SELECT id, name FROM Patterns")
        patterns = cursor.fetchall()
        for pattern_id, pattern in patterns:
            item = QListWidgetItem(pattern)
            item.setData(Qt.UserRole, pattern_id)
            self.ui.plist.addItem(item)

        cursor.execute("SELECT id, name FROM Textures")
        textures = cursor.fetchall()
        for texture_id, texture in textures:
            item = QListWidgetItem(texture)
            item.setData(Qt.UserRole, texture_id)
            self.ui.tlist.addItem(item)

        cursor.execute("SELECT id, name, price FROM Upcharges")
        upcharges = cursor.fetchall()
        for upcharge_id, description, price in upcharges:
            item = QListWidgetItem(f"{description} - ${price:.2f}")
            item.setData(Qt.UserRole, upcharge_id)
            self.ui.ulist.addItem(item)

        cursor.execute("SELECT id, name FROM Discounts")
        discounts = cursor.fetchall()
        for discount_id, name in discounts:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, discount_id)
            self.ui.dlist.addItem(item)

        cursor.execute("SELECT id, name FROM Garments")
        garments = cursor.fetchall()
        for garment_id, garment in garments:
            item = QListWidgetItem(garment)
            item.setData(Qt.UserRole, garment_id)
            self.ui.glist.addItem(item)

        conn.close()

    def load_ticket_types(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, name FROM TicketTypes")
        ticket_types = cursor.fetchall()
        conn.close()

        for ticket_type_id, ticket_type_name in ticket_types:
            item = QListWidgetItem(ticket_type_name)
            item.setData(Qt.UserRole, ticket_type_id)
            self.ui.sttlist.addItem(item)

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

        def get_item_ids(widget):
            return [widget.item(i).data(Qt.UserRole)[0] if isinstance(widget.item(i).data(Qt.UserRole), tuple) else widget.item(i).data(Qt.UserRole) for i in range(widget.count())]

        chosen_garments = get_item_ids(self.ui.cglist)
        chosen_patterns = get_item_ids(self.ui.cpatterns)
        chosen_textures = get_item_ids(self.ui.ctextures)
        chosen_colors = get_item_ids(self.ui.cclist)
        chosen_upcharges = get_item_ids(self.ui.cupcharges)
        chosen_discounts = get_item_ids(self.ui.cdiscounts)

        if not (chosen_garments or chosen_patterns or chosen_textures or chosen_colors or chosen_upcharges or chosen_discounts):
            QMessageBox.warning(self, "Input Error", "Please select at least one option.")
            return

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO TicketTypes (name) VALUES (?)", (ticket_type_name,))
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

            # Add the new ticket type to the list and clear inputs
            self.ui.sttlist.addItem(QListWidgetItem(ticket_type_name))
            self.ui.ttinput.clear()
            self.ui.cglist.clear()
            self.ui.cpatterns.clear()
            self.ui.ctextures.clear()
            self.ui.cclist.clear()
            self.ui.cupcharges.clear()
            self.ui.cdiscounts.clear()
            self.ui.sttlist.clear()  # Clear the list to prevent duplicates
            self.load_ticket_types()  # Reload the list to reflect the new ticket type

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
            conn.rollback()
        finally:
            conn.close()

    def delete_ticket_type(self):
        selected_item = self.ui.sttlist.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Selection Error", "Please select a ticket type to delete.")
            return

        ticket_type_id = selected_item.data(Qt.UserRole)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM TicketTypes WHERE id = ?", (ticket_type_id,))
            cursor.execute("DELETE FROM ticket_type_garments WHERE ticket_type_id = ?", (ticket_type_id,))
            cursor.execute("DELETE FROM ticket_type_patterns WHERE ticket_type_id = ?", (ticket_type_id,))
            cursor.execute("DELETE FROM ticket_type_textures WHERE ticket_type_id = ?", (ticket_type_id,))
            cursor.execute("DELETE FROM ticket_type_colors WHERE ticket_type_id = ?", (ticket_type_id,))
            cursor.execute("DELETE FROM ticket_type_upcharges WHERE ticket_type_id = ?", (ticket_type_id,))
            cursor.execute("DELETE FROM ticket_type_discounts WHERE ticket_type_id = ?", (ticket_type_id,))

            conn.commit()

            self.ui.sttlist.takeItem(self.ui.sttlist.row(selected_item))

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = TicketTypeCreationWindow()
    window.show()
    sys.exit(app.exec())
