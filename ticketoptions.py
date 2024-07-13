import sqlite3
from PySide6.QtWidgets import QMainWindow, QWidget, QLineEdit, QLabel, QPushButton, QListWidget, QMenuBar, QStatusBar, QVBoxLayout, QMessageBox
from Test import Ui_TicketOptionsCreation

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

    def save_texture(self):
        name = self.ui.tandpinput.text().strip()
        if name:
            conn = sqlite3.connect('pos_system.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO textures (name) VALUES (?)", (name,))
            conn.commit()
            conn.close()
            
            self.ui.tlist.addItem(name)
            self.ui.tandpinput.clear()
        else:
            self.show_error_message("Please enter a name for the texture.")

    def save_pattern(self):
        name = self.ui.tandpinput.text().strip()
        if name:
            conn = sqlite3.connect('pos_system.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO patterns (name) VALUES (?)", (name,))
            conn.commit()
            conn.close()
            
            self.ui.plist.addItem(name)
            self.ui.tandpinput.clear()
        else:
            self.show_error_message("Please enter a name for the pattern.")

    def save_upcharge(self):
        name = self.ui.uinput.text().strip()
        amount = self.ui.uamountinput.text().strip()
        if name and amount:
            conn = sqlite3.connect('pos_system.db')
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
            conn = sqlite3.connect('pos_system.db')
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
