import sys
import sqlite3
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QPlainTextEdit, QLineEdit
from PySide6.QtCore import Qt, QEvent
from views.Test import Ui_CustomerAccount2
from controllers.customersearch import CustomerSearch
from controllers.quickticket import QuickTicketWindow  # Corrected import

class CustomerAccountWindow(QMainWindow, Ui_CustomerAccount2):
    def __init__(self, customer_data1=None, customer_data2=None):
        super().__init__()
        self.setupUi(self)
        
        if customer_data1:
            self.load_customer_data_page1(customer_data1)
        else:
            self.clear_page1()
        
        if customer_data2:
            self.load_customer_data_page2(customer_data2)
        else:
            self.clear_page2()
        
        self.tabWidget.setCurrentIndex(0)  # Ensure Tab 1 is selected
        self.stackedWidget.setCurrentIndex(0)  # Ensure Page 1 is selected

        # Customer data
        self.customer_id1 = customer_data1.get("id", None) if customer_data1 else None
        self.customer_data1 = customer_data1 if customer_data1 else {}
        self.customer_id2 = customer_data2.get("id", None) if customer_data2 else None
        self.customer_data2 = customer_data2 if customer_data2 else {}

        # Connect the buttons to their functions
        self.pushButton_16.clicked.connect(self.show_page2)
        self.pushButton_3.clicked.connect(self.show_page1)
        self.pushButton.clicked.connect(self.open_search_window_page1)
        self.pushButton_2.clicked.connect(self.open_search_window_page2)
        self.qtbutton.clicked.connect(self.open_quick_ticket_page1)  # Connect to quick ticket creation
        self.qtbutton_2.clicked.connect(self.open_quick_ticket_page2)  # Connect to quick ticket creation
        
        # Connect the editingFinished signals to save the data
        self.FirstNameInput.editingFinished.connect(self.save_customer_data_page1)
        self.LastNameInput.editingFinished.connect(self.save_customer_data_page1)
        self.PhoneNumberInput.editingFinished.connect(self.save_customer_data_page1)
        self.NotesInput.focusOutEvent = self.create_save_event(self.NotesInput, self.save_customer_data_page1)

        self.FirstNameInput_2.editingFinished.connect(self.save_customer_data_page2)
        self.LastNameInput_2.editingFinished.connect(self.save_customer_data_page2)
        self.PhoneNumberInput_2.editingFinished.connect(self.save_customer_data_page2)
        self.NotesInput_2.focusOutEvent = self.create_save_event(self.NotesInput_2, self.save_customer_data_page2)

        # Ensure QLineEdit widgets also save on focus out
        self.FirstNameInput.focusOutEvent = self.create_save_event(self.FirstNameInput, self.save_customer_data_page1)
        self.LastNameInput.focusOutEvent = self.create_save_event(self.LastNameInput, self.save_customer_data_page1)
        self.PhoneNumberInput.focusOutEvent = self.create_save_event(self.PhoneNumberInput, self.save_customer_data_page1)

        self.FirstNameInput_2.focusOutEvent = self.create_save_event(self.FirstNameInput_2, self.save_customer_data_page2)
        self.LastNameInput_2.focusOutEvent = self.create_save_event(self.LastNameInput_2, self.save_customer_data_page2)
        self.PhoneNumberInput_2.focusOutEvent = self.create_save_event(self.PhoneNumberInput_2, self.save_customer_data_page2)

    def create_save_event(self, widget, save_function):
        original_focus_out_event = widget.focusOutEvent

        def save_event(event):
            if event.type() == QEvent.FocusOut:
                save_function()
            return original_focus_out_event(event)
        return save_event

    def load_customer_data_page1(self, customer_data):
        self.FirstNameInput.setText(customer_data.get("first_name", ""))
        self.LastNameInput.setText(customer_data.get("last_name", ""))
        self.PhoneNumberInput.setText(customer_data.get("phone_number", ""))
        self.NotesInput.setPlainText(customer_data.get("notes", ""))
        self.customer_id1 = customer_data.get("id", None)

    def load_customer_data_page2(self, customer_data):
        self.FirstNameInput_2.setText(customer_data.get("first_name", ""))
        self.LastNameInput_2.setText(customer_data.get("last_name", ""))
        self.PhoneNumberInput_2.setText(customer_data.get("phone_number", ""))
        self.NotesInput_2.setPlainText(customer_data.get("notes", ""))
        self.customer_id2 = customer_data.get("id", None)

    def clear_page1(self):
        self.FirstNameInput.clear()
        self.LastNameInput.clear()
        self.PhoneNumberInput.clear()
        self.NotesInput.clear()
        self.customer_id1 = None

    def clear_page2(self):
        self.FirstNameInput_2.clear()
        self.LastNameInput_2.clear()
        self.PhoneNumberInput_2.clear()
        self.NotesInput_2.clear()
        self.customer_id2 = None

    def save_customer_data_page1(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if self.customer_id1:
            cursor.execute("""
                UPDATE customers
                SET first_name = ?, last_name = ?, phone_number = ?, notes = ?
                WHERE id = ?
            """, (
                self.FirstNameInput.text(),
                self.LastNameInput.text(),
                self.PhoneNumberInput.text(),
                self.NotesInput.toPlainText(),
                self.customer_id1
            ))
        else:
            cursor.execute("""
                INSERT INTO customers (first_name, last_name, phone_number, notes)
                VALUES (?, ?, ?, ?)
            """, (
                self.FirstNameInput.text(),
                self.LastNameInput.text(),
                self.PhoneNumberInput.text(),
                self.NotesInput.toPlainText()
            ))
            self.customer_id1 = cursor.lastrowid
        
        conn.commit()
        conn.close()

    def save_customer_data_page2(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if self.customer_id2:
            cursor.execute("""
                UPDATE customers
                SET first_name = ?, last_name = ?, phone_number = ?, notes = ?
                WHERE id = ?
            """, (
                self.FirstNameInput_2.text(),
                self.LastNameInput_2.text(),
                self.PhoneNumberInput_2.text(),
                self.NotesInput_2.toPlainText(),
                self.customer_id2
            ))
        else:
            cursor.execute("""
                INSERT INTO customers (first_name, last_name, phone_number, notes)
                VALUES (?, ?, ?, ?)
            """, (
                self.FirstNameInput_2.text(),
                self.LastNameInput_2.text(),
                self.PhoneNumberInput_2.text(),
                self.NotesInput_2.toPlainText()
            ))
            self.customer_id2 = cursor.lastrowid
        
        conn.commit()
        conn.close()

    def show_page1(self):
        self.stackedWidget.setCurrentIndex(0)

    def show_page2(self):
        self.stackedWidget.setCurrentIndex(1)

    def open_search_window_page1(self):
        self.search_window = CustomerSearch(target_page=1)
        self.search_window.customer_selected.connect(self.load_customer_data_page1)
        self.search_window.show()

    def open_search_window_page2(self):
        self.search_window = CustomerSearch(target_page=2)
        self.search_window.customer_selected.connect(self.load_customer_data_page2)
        self.search_window.show()

    def open_quick_ticket_page1(self):
        print(f"Opening Quick Ticket for customer_id1: {self.customer_id1}")
        self.quick_ticket_window = QuickTicketWindow(customer_id=self.customer_id1)
        self.quick_ticket_window.show()

    def open_quick_ticket_page2(self):
        print(f"Opening Quick Ticket for customer_id2: {self.customer_id2}")
        self.quick_ticket_window = QuickTicketWindow(customer_id=self.customer_id2)
        self.quick_ticket_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    customer_data1 = {
        "id": 1,
        "first_name": "Sample",
        "last_name": "Customer",
        "phone_number": "0000000000",
        "notes": "Sample notes"
    }
    customer_data2 = {
        "id": 2,
        "first_name": "Another",
        "last_name": "Customer",
        "phone_number": "1111111111",
        "notes": "Other sample notes"
    }
    account_window = CustomerAccountWindow(customer_data1, customer_data2)
    account_window.show()
    sys.exit(app.exec())
