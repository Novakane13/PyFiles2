import sqlite3
from PySide6.QtWidgets import QMainWindow, QListWidgetItem, QTreeWidgetItem, QMessageBox
from Test import Ui_TicketTypeCreation

class TicketTypeCreationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_TicketTypeCreation()
        self.ui.setupUi(self)
        
        # Connecting buttons to functions
        self.ui.deletettbutton.clicked.connect(self.close)  # using 'deletettbutton' for close functionality
        self.ui.savettbutton.clicked.connect(self.save_ticket_type)
        
        self.load_options()
        
    def load_options(self):
        conn = sqlite3.connect('pos_system.db')
        cursor = conn.cursor()

        cursor.execute("SELECT name, color FROM colors")
        colors = cursor.fetchall()
        for name, color in colors:
            item = QListWidgetItem(name)
            item.setBackground(color)
            self.ui.clist.addItem(item)

        cursor.execute("SELECT name FROM patterns")
        patterns = cursor.fetchall()
        for pattern in patterns:
            self.ui.plist.addItem(QListWidgetItem(pattern[0]))

        cursor.execute("SELECT name FROM textures")
        textures = cursor.fetchall()
        for texture in textures:
            self.ui.tlist.addItem(QListWidgetItem(texture[0]))

        cursor.execute("SELECT name, amount FROM upcharges")
        upcharges = cursor.fetchall()
        for name, amount in upcharges:
            self.ui.ulist.addItem(QListWidgetItem(f"{name} - ${amount}"))

        cursor.execute("SELECT name, percent, amount FROM discounts")
        discounts = cursor.fetchall()
        for discount in discounts:
            if discount[1] is not None:
                self.ui.dlist.addItem(QListWidgetItem(f"{discount[0]} - {discount[1]}% off"))
            elif discount[2] is not None:
                self.ui.dlist.addItem(QListWidgetItem(f"{discount[0]} - ${discount[2]} off"))

        cursor.execute("SELECT name FROM garments")
        garments = cursor.fetchall()
        for garment in garments:
            self.ui.glist.addItem(QListWidgetItem(garment[0]))

        cursor.execute("SELECT name FROM ticket_types")
        ticket_types = cursor.fetchall()
        for ticket_type in ticket_types:
            self.ui.sttlist.addItem(ticket_type[0])

        conn.close()

    def save_ticket_type(self):
        ticket_type_name = self.ui.ttinput.text().strip()
        if not ticket_type_name:
            QMessageBox.warning(self, "Input Error", "Please enter a ticket type name.")
            return

        chosen_garments = [self.ui.glist.item(i).text() for i in range(self.ui.glist.count())]
        chosen_patterns = [self.ui.plist.item(i).text() for i in range(self.ui.plist.count())]
        chosen_textures = [self.ui.tlist.item(i).text() for i in range(self.ui.tlist.count())]
        chosen_colors = [self.ui.clist.item(i).text() for i in range(self.ui.clist.count())]
        chosen_upcharges = [self.ui.ulist.item(i).text() for i in range(self.ui.ulist.count())]
        chosen_discounts = [self.ui.dlist.item(i).text() for i in range(self.ui.dlist.count())]
        
        if not (chosen_garments or chosen_patterns or chosen_textures or chosen_colors or chosen_upcharges or chosen_discounts):
            QMessageBox.warning(self, "Input Error", "Please select at least one option.")
            return

        ticket_type = {
            "name": ticket_type_name,
            "garments": ','.join(chosen_garments),
            "patterns": ','.join(chosen_patterns),
            "textures": ','.join(chosen_textures),
            "colors": ','.join(chosen_colors),
            "upcharges": ','.join(chosen_upcharges),
            "discounts": ','.join(chosen_discounts)
        }

        conn = sqlite3.connect('pos_system.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO ticket_options (name, garments, patterns, textures, colors, upcharges, discounts) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (ticket_type["name"], ticket_type["garments"], ticket_type["patterns"], ticket_type["textures"], ticket_type["colors"], ticket_type["upcharges"], ticket_type["discounts"]))
        conn.commit()
        conn.close()

        self.ui.sttlist.addItem(ticket_type_name)
        self.ui.ttinput.clear()
        self.ui.glist.clear()
        self.ui.plist.clear()
        self.ui.tlist.clear()
        self.ui.clist.clear()
        self.ui.ulist.clear()
        self.ui.dlist.clear()
        self.load_options()

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = TicketTypeCreationWindow()
    window.show()
    sys.exit(app.exec())
