import sqlite3
import os
from PySide6.QtWidgets import QMainWindow, QColorDialog, QFileDialog, QListWidgetItem, QMessageBox
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt
from views.Test import Ui_TicketOptionsCreation

class TicketOptionsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_TicketOptionsCreation()
        self.ui.setupUi(self)
        
        # Connect buttons to functions
        self.ui.savetbutton.clicked.connect(self.save_texture)
        self.ui.savepbutton.clicked.connect(self.save_pattern)
        self.ui.saveubutton.clicked.connect(self.save_upcharge)
        self.ui.savedbutton.clicked.connect(self.save_discount)
        self.ui.sibutton.clicked.connect(self.select_image)
        self.ui.deletebutton.clicked.connect(self.delete_option)

        self.selected_image = None

        # Load saved options when the window is opened
        self.load_saved_options()

    def select_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Image Files (*.png *.jpg *.bmp)")
        if file_name:
            self.selected_image = file_name
            pixmap = QPixmap(file_name)
            scaled_pixmap = pixmap.scaled(self.ui.ImageLabel.size(), Qt.KeepAspectRatio)
            self.ui.ImageLabel.setPixmap(scaled_pixmap)
            self.ui.sibutton.setText("Image Selected")

    def save_texture(self):
        name = self.ui.tandpinput.text().strip()
        if name:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            db_path = os.path.join(project_root, 'models', 'pos_system.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO textures (name, image_path) VALUES (?, ?)", (name, self.selected_image))
            texture_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, texture_id)
            if self.selected_image:
                item.setIcon(QIcon(QPixmap(self.selected_image)))
            self.ui.tlist.addItem(item)
            self.ui.tandpinput.clear()
            self.selected_image = None
            self.ui.sibutton.setText("Select Image")
            self.ui.ImageLabel.clear()
        else:
            self.show_error_message("Please enter a name for the texture.")

    def save_pattern(self):
        name = self.ui.tandpinput.text().strip()
        if name:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            db_path = os.path.join(project_root, 'models', 'pos_system.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO patterns (name, image_path) VALUES (?, ?)", (name, self.selected_image))
            pattern_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, pattern_id)
            if self.selected_image:
                item.setIcon(QIcon(QPixmap(self.selected_image)))
            self.ui.plist.addItem(item)
            self.ui.tandpinput.clear()
            self.selected_image = None
            self.ui.sibutton.setText("Select Image")
            self.ui.ImageLabel.clear()
        else:
            self.show_error_message("Please enter a name for the pattern.")

    def save_upcharge(self):
        description = self.ui.uinput.text().strip()
        price = self.ui.uamountinput.text().strip()
        if description and price:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            db_path = os.path.join(project_root, 'models', 'pos_system.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO upcharges (description, price) VALUES (?, ?)", (description, price))
            upcharge_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            item = QListWidgetItem(f"{description} - ${price}")
            item.setData(Qt.UserRole, upcharge_id)
            self.ui.ulist.addItem(item)
            self.ui.uinput.clear()
            self.ui.uamountinput.clear()
        else:
            self.show_error_message("Please enter both a name and an amount for the upcharge.")

    def save_discount(self):
        name = self.ui.dinput.text().strip()
        percent = self.ui.dpercentinput.text().strip()
        amount = self.ui.damountinput.text().strip()
        if name:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            db_path = os.path.join(project_root, 'models', 'pos_system.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            if percent:
                cursor.execute("INSERT INTO discounts (name, percent) VALUES (?, ?)", (name, percent))
                discount_id = cursor.lastrowid
                self.ui.dlist.addItem(f"{name} - {percent}% off")
            elif amount:
                cursor.execute("INSERT INTO discounts (name, amount) VALUES (?, ?)", (name, amount))
                discount_id = cursor.lastrowid
                self.ui.dlist.addItem(f"{name} - ${amount} off")
            else:
                self.show_error_message("Please enter either a percentage or an amount for the discount.")
                return
            cursor.execute("INSERT INTO discounts (name, percent, amount) VALUES (?, ?, ?)",
                           (name, percent if percent else None, amount if amount else None))
            discount_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            if percent:
                item = QListWidgetItem(f"{name} - {percent}% off")
            else:
                item = QListWidgetItem(f"{name} - ${amount} off")
            item.setData(Qt.UserRole, discount_id)
            self.ui.dlist.addItem(item)
            self.ui.dinput.clear()
            self.ui.dpercentinput.clear()
            self.ui.damountinput.clear()
        else:
            self.show_error_message("Please enter a name for the discount.")

    def load_saved_options(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Load saved textures
        cursor.execute("SELECT id, name, image_path FROM textures")
        textures = cursor.fetchall()
        for texture_id, texture_name, image_path in textures:
            item = QListWidgetItem(texture_name)
            item.setData(Qt.UserRole, texture_id)
            if image_path:
                item.setIcon(QIcon(QPixmap(image_path)))
            self.ui.tlist.addItem(item)

        # Load saved patterns
        cursor.execute("SELECT id, name, image_path FROM patterns")
        patterns = cursor.fetchall()
        for pattern_id, pattern_name, image_path in patterns:
            item = QListWidgetItem(pattern_name)
            item.setData(Qt.UserRole, pattern_id)
            if image_path:
                item.setIcon(QIcon(QPixmap(image_path)))
            self.ui.plist.addItem(item)

        # Load saved upcharges
        cursor.execute("SELECT id, description, price FROM upcharges")
        upcharges = cursor.fetchall()
        for upcharge_id, upcharge_name, upcharge_amount in upcharges:
            item = QListWidgetItem(f"{upcharge_name} - ${upcharge_amount}")
            item.setData(Qt.UserRole, upcharge_id)
            self.ui.ulist.addItem(item)

        # Load saved discounts
        cursor.execute("SELECT id, name, percent, amount FROM discounts")
        discounts = cursor.fetchall()
        for discount_id, discount_name, discount_percent, discount_amount in discounts:
            if discount_percent:
                item = QListWidgetItem(f"{discount_name} - {discount_percent}% off")
            else:
                item = QListWidgetItem(f"{discount_name} - ${discount_amount} off")
            item.setData(Qt.UserRole, discount_id)
            self.ui.dlist.addItem(item)

        conn.close()

    def delete_option(self):
        current_list = None
        if self.ui.tlist.currentItem():
            current_list = self.ui.tlist
            table_name = 'textures'
        elif self.ui.plist.currentItem():
            current_list = self.ui.plist
            table_name = 'patterns'
        elif self.ui.ulist.currentItem():
            current_list = self.ui.ulist
            table_name = 'upcharges'
        elif self.ui.dlist.currentItem():
            current_list = self.ui.dlist
            table_name = 'discounts'
        
        if current_list is None:
            QMessageBox.warning(self, "Selection Error", "Please select an option to delete.")
            return
        
        selected_item = current_list.currentItem()
        option_id = selected_item.data(Qt.UserRole)

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (option_id,))
        conn.commit()
        conn.close()

        current_list.takeItem(current_list.row(selected_item))

    def show_error_message(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setText(message)
        msg_box.setWindowTitle("Input Error")
        msg_box.exec()

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = TicketOptionsWindow()
    window.show()
    sys.exit(app.exec())
