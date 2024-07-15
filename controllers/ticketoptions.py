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

        self.selected_image = None

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
            cursor.execute("INSERT INTO textures (name, image) VALUES (?, ?)", (name, self.selected_image))
            conn.commit()
            conn.close()
            
            item = QListWidgetItem(name)
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
            cursor.execute("INSERT INTO patterns (name, image) VALUES (?, ?)", (name, self.selected_image))
            conn.commit()
            conn.close()
            
            item = QListWidgetItem(name)
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
        name = self.ui.uinput.text().strip()
        amount = self.ui.uamountinput.text().strip()
        if name and amount:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            db_path = os.path.join(project_root, 'models', 'pos_system.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO upcharges (name, amount) VALUES (?, ?)", (name, amount))
            conn.commit()
            conn.close()
            
            self.ui.ulist.addItem(f"{name} - ${amount}")
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
                self.ui.dlist.addItem(f"{name} - {percent}% off")
            elif amount:
                cursor.execute("INSERT INTO discounts (name, amount) VALUES (?, ?)", (name, amount))
                self.ui.dlist.addItem(f"{name} - ${amount} off")
            else:
                self.show_error_message("Please enter either a percentage or an amount for the discount.")
                return
            conn.commit()
            conn.close()
            
            self.ui.dinput.clear()
            self.ui.dpercentinput.clear()
            self.ui.damountinput.clear()
        else:
            self.show_error_message("Please enter a name for the discount.")

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
