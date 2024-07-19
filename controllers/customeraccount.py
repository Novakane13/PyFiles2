import sys
import sqlite3
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QGridLayout, QTreeWidgetItem
from PySide6.QtCore import Qt, QEvent
from views.Test import Ui_CustomerAccount2
from controllers.customersearch import CustomerSearch
from controllers.quickticket import QuickTicketWindow
from controllers.detailedticket import DetailedTicketWindow

class CustomerAccountWindow(QMainWindow):
    def __init__(self, customer_data1, customer_data2):
        super().__init__()
        self.ui = Ui_CustomerAccount2()
        self.ui.setupUi(self)

        self.customer_data1 = customer_data1
        self.customer_data2 = customer_data2

        self.populate_ticket_type_buttons()

        if customer_data1:
            self.load_customer_data_page1(customer_data1)
        else:
            self.clear_page1()

        if customer_data2:
            self.load_customer_data_page2(customer_data2)
        else:
            self.clear_page2()

        self.ui.tabWidget.setCurrentIndex(0)  # Ensure Tab 1 is selected
        self.ui.pageswidget.setCurrentIndex(0)  # Ensure Page 1 is selected

        # Customer data
        self.customer_id1 = customer_data1.get("id", None) if customer_data1 else None
        self.customer_data1 = customer_data1 if customer_data1 else {}
        self.customer_id2 = customer_data2.get("id", None) if customer_data2 else None
        self.customer_data2 = customer_data2 if customer_data2 else {}

        # Connect the buttons to their functions
        self.ui.pushButton_16.clicked.connect(self.show_page2)
        self.ui.pushButton_3.clicked.connect(self.show_page1)
        self.ui.pushButton.clicked.connect(self.open_search_window_page1)
        self.ui.pushButton_2.clicked.connect(self.open_search_window_page2)
        self.ui.qtbutton.clicked.connect(self.open_quick_ticket_page1)  # Connect to quick ticket creation
        self.ui.qtbutton_2.clicked.connect(self.open_quick_ticket_page2)  # Connect to quick ticket creation

        self.populate_ticket_type_buttons()

        # Connect the editingFinished signals to save the data
        self.ui.FirstNameInput.editingFinished.connect(self.save_customer_data_page1)
        self.ui.LastNameInput.editingFinished.connect(self.save_customer_data_page1)
        self.ui.PhoneNumberInput.editingFinished.connect(self.save_customer_data_page1)
        self.ui.NotesInput.focusOutEvent = self.create_save_event(self.ui.NotesInput, self.save_customer_data_page1)

        self.ui.FirstNameInput_2.editingFinished.connect(self.save_customer_data_page2)
        self.ui.LastNameInput_2.editingFinished.connect(self.save_customer_data_page2)
        self.ui.PhoneNumberInput_2.editingFinished.connect(self.save_customer_data_page2)
        self.ui.NotesInput_2.focusOutEvent = self.create_save_event(self.ui.NotesInput_2, self.save_customer_data_page2)

        # Ensure QLineEdit widgets also save on focus out
        self.ui.FirstNameInput.focusOutEvent = self.create_save_event(self.ui.FirstNameInput, self.save_customer_data_page1)
        self.ui.LastNameInput.focusOutEvent = self.create_save_event(self.ui.LastNameInput, self.save_customer_data_page1)
        self.ui.PhoneNumberInput.focusOutEvent = self.create_save_event(self.ui.PhoneNumberInput, self.save_customer_data_page1)

        self.ui.FirstNameInput_2.focusOutEvent = self.create_save_event(self.ui.FirstNameInput_2, self.save_customer_data_page2)
        self.ui.LastNameInput_2.focusOutEvent = self.create_save_event(self.ui.LastNameInput_2, self.save_customer_data_page2)
        self.ui.PhoneNumberInput_2.focusOutEvent = self.create_save_event(self.ui.PhoneNumberInput_2, self.save_customer_data_page2)

    def create_save_event(self, widget, save_function):
        original_focus_out_event = widget.focusOutEvent

        def save_event(event):
            if event.type() == QEvent.FocusOut:
                save_function()
            return original_focus_out_event(event)
        return save_event

    def load_customer_data_page1(self, customer_data):
        self.ui.FirstNameInput.setText(customer_data.get("first_name", ""))
        self.ui.LastNameInput.setText(customer_data.get("last_name", ""))
        self.ui.PhoneNumberInput.setText(customer_data.get("phone_number", ""))
        self.ui.NotesInput.setPlainText(customer_data.get("notes", ""))
        self.customer_id1 = customer_data.get("id", None)

    def load_customer_data_page2(self, customer_data):
        self.ui.FirstNameInput_2.setText(customer_data.get("first_name", ""))
        self.ui.LastNameInput_2.setText(customer_data.get("last_name", ""))
        self.ui.PhoneNumberInput_2.setText(customer_data.get("phone_number", ""))
        self.ui.NotesInput_2.setPlainText(customer_data.get("notes", ""))
        self.customer_id2 = customer_data.get("id", None)

    def clear_page1(self):
        self.ui.FirstNameInput.clear()
        self.ui.LastNameInput.clear()
        self.ui.PhoneNumberInput.clear()
        self.ui.NotesInput.clear()
        self.customer_id1 = None

    def clear_page2(self):
        self.ui.FirstNameInput_2.clear()
        self.ui.LastNameInput_2.clear()
        self.ui.PhoneNumberInput_2.clear()
        self.ui.NotesInput_2.clear()
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
                self.ui.FirstNameInput.text(),
                self.ui.LastNameInput.text(),
                self.ui.PhoneNumberInput.text(),
                self.ui.NotesInput.toPlainText(),
                self.customer_id1
            ))
        else:
            cursor.execute("""
                INSERT INTO customers (first_name, last_name, phone_number, notes)
                VALUES (?, ?, ?, ?)
            """, (
                self.ui.FirstNameInput.text(),
                self.ui.LastNameInput.text(),
                self.ui.PhoneNumberInput.text(),
                self.ui.NotesInput.toPlainText()
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
                self.ui.FirstNameInput_2.text(),
                self.ui.LastNameInput_2.text(),
                self.ui.PhoneNumberInput_2.text(),
                self.ui.NotesInput_2.toPlainText(),
                self.customer_id2
            ))
        else:
            cursor.execute("""
                INSERT INTO customers (first_name, last_name, phone_number, notes)
                VALUES (?, ?, ?, ?)
            """, (
                self.ui.FirstNameInput_2.text(),
                self.ui.LastNameInput_2.text(),
                self.ui.PhoneNumberInput_2.text(),
                self.ui.NotesInput_2.toPlainText()
            ))
            self.customer_id2 = cursor.lastrowid

        conn.commit()
        conn.close()

    def show_page1(self):
        self.ui.pageswidget.setCurrentIndex(0)

    def show_page2(self):
        self.ui.pageswidget.setCurrentIndex(1)

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

    def open_detailed_ticket_page(self, customer_id, ticket_type):
        print(f"Opening Detailed Ticket for customer_id: {customer_id}, ticket_type: {ticket_type}")
        self.detailed_ticket_window = DetailedTicketWindow(customer_id=customer_id, ticket_type=ticket_type)
        self.detailed_ticket_window.show()

    def open_detailed_ticket_page1(self, ticket_type):
        self.open_detailed_ticket_page(self.customer_id1, ticket_type)

    def open_detailed_ticket_page2(self, ticket_type):
        self.open_detailed_ticket_page(self.customer_id2, ticket_type)

    def populate_ticket_type_buttons(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, ticket_type_name FROM ticket_types")
        ticket_types = cursor.fetchall()

        layout1 = self.ui.tickettypebuttongrid  # Using QGridLayout for page 1
        layout2 = self.ui.tickettypebuttongrid_2  # Using QGridLayout for page 2

        row1, col1 = 0, 0
        row2, col2 = 0, 0

        for idx, (ticket_type_id, ticket_type_name) in enumerate(ticket_types):
            button1 = QPushButton(ticket_type_name)
            button1.clicked.connect(lambda checked, tt_id=ticket_type_id: self.open_detailed_ticket_page1(tt_id))
            layout1.addWidget(button1, row1, col1)
            col1 += 1
            if col1 > 2:  # Move to next row after 3 columns
                col1 = 0
                row1 += 1

            button2 = QPushButton(ticket_type_name)
            button2.clicked.connect(lambda checked, tt_id=ticket_type_id: self.open_detailed_ticket_page2(tt_id))
            layout2.addWidget(button2, row2, col2)
            col2 += 1
            if col2 > 2:  # Move to next row after 3 columns
                col2 = 0
                row2 += 1

        conn.close()

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
