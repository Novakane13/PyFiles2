import sys
import sqlite3
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QTableWidgetItem, QMessageBox
from PySide6.QtCore import QEvent
from views.Test import Ui_CustomerAccount2
from controllers.customersearch import CustomerSearch
from controllers.quickticket import QuickTicketWindow
from controllers.detailedticket import DetailedTicketWindow
from PySide6.QtCore import Qt, QEvent, Signal
from views.Test import Ui_CustomerAccount2  # Ensure this import is correct

class CustomerAccountWindow(QMainWindow):
    # Signal to indicate a quick ticket conversion request
    convert_to_detailed_ticket = Signal(dict)

    def __init__(self, customer_data1=None, customer_data2=None, employee_id=None):
        super().__init__()
        self.ui = Ui_CustomerAccount2()
        self.ui.setupUi(self)

        self.customer_data1 = customer_data1 or {}
        self.customer_data2 = customer_data2 or {}
        self.employee_id = employee_id
        self.ticket_id = None

        # Customer IDs
        self.customer_id1 = self.customer_data1.get("id", None)
        self.customer_id2 = self.customer_data2.get("id", None)

        # Load initial customer data
        self.load_customer_data_page1(self.customer_data1)
        self.load_customer_data_page2(self.customer_data2)

        # Populate ticket type buttons for both pages
        self.populate_ticket_type_buttons()

        # Set initial UI states
        self.ui.tabWidget.setCurrentIndex(0)  # Ensure Tab 1 is selected
        self.ui.pageswidget.setCurrentIndex(0)  # Ensure Page 1 is selected

        # Connect buttons to their functions
        self.ui.pushButton_16.clicked.connect(self.show_page2)
        self.ui.pushButton_3.clicked.connect(self.show_page1)
        self.ui.pushButton.clicked.connect(self.open_search_window_page1)
        self.ui.pushButton_2.clicked.connect(self.open_search_window_page2)
        self.ui.qtbutton.clicked.connect(self.open_quick_ticket_page1)
        self.ui.qtbutton_2.clicked.connect(self.open_quick_ticket_page2)

        # Connect the editingFinished signals to save the data
        self.ui.FirstNameInput.editingFinished.connect(self.save_customer_data_page1)
        self.ui.LastNameInput.editingFinished.connect(self.save_customer_data_page1)
        self.ui.PhoneNumberInput.editingFinished.connect(self.save_customer_data_page1)
        self.ui.NotesInput.focusOutEvent = self.create_save_event(self.ui.NotesInput, self.save_customer_data_page1)

        self.ui.FirstNameInput_2.editingFinished.connect(self.save_customer_data_page2)
        self.ui.LastNameInput_2.editingFinished.connect(self.save_customer_data_page2)
        self.ui.PhoneNumberInput_2.editingFinished.connect(self.save_customer_data_page2)
        self.ui.NotesInput_2.focusOutEvent = self.create_save_event(self.ui.NotesInput_2, self.save_customer_data_page2)

        # Load tickets for the existing customers
        if self.customer_id1:
            self.load_tickets(self.customer_id1, self.ui.ctlist)
        if self.customer_id2:
            self.load_tickets(self.customer_id2, self.ui.ctlist_2)

        # Connect the list widgets for quick ticket conversion
        self.ui.ctlist.itemDoubleClicked.connect(
            lambda: self.convert_selected_quick_ticket(self.ui.ctlist, self.customer_id1)
        )
        self.ui.ctlist_2.itemDoubleClicked.connect(
            lambda: self.convert_selected_quick_ticket(self.ui.ctlist_2, self.customer_id2)
        )

    def populate_ticket_type_buttons(self):
        """Dynamically add ticket type buttons for both customer pages."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Retrieve all ticket types
        cursor.execute("SELECT id, name FROM TicketTypes")
        ticket_types = cursor.fetchall()

        # Layouts for buttons
        layout1 = self.ui.tickettypebuttongrid
        layout2 = self.ui.tickettypebuttongrid_2

        # Add buttons dynamically for ticket types
        row1, col1 = 0, 0
        row2, col2 = 0, 0

        for ticket_type_id, ticket_type_name in ticket_types:
            # Button for Page 1
            button1 = QPushButton(ticket_type_name)
            button1.clicked.connect(lambda checked, tt_name=ticket_type_name, tt_id=ticket_type_id: self.open_detailed_ticket_page1(tt_name, tt_id))
            layout1.addWidget(button1, row1, col1)
            col1 += 1
            if col1 > 2:
                col1 = 0
                row1 += 1

            # Button for Page 2
            button2 = QPushButton(ticket_type_name)
            button2.clicked.connect(lambda checked, tt_name=ticket_type_name, tt_id=ticket_type_id: self.open_detailed_ticket_page2(tt_name, tt_id))
            layout2.addWidget(button2, row2, col2)
            col2 += 1
            if col2 > 2:
                col2 = 0
                row2 += 1

        conn.close()

    def create_save_event(self, widget, save_function):
        """Create a focus out event for saving customer data."""
        original_focus_out_event = widget.focusOutEvent

        def save_event(event):
            if event.type() == QEvent.FocusOut:
                save_function()
            return original_focus_out_event(event)

        return save_event

    def load_customer_data_page1(self, customer_data):
        """Load customer data into UI elements for Page 1."""
        self.ui.FirstNameInput.setText(customer_data.get("first_name", ""))
        self.ui.LastNameInput.setText(customer_data.get("last_name", ""))
        self.ui.PhoneNumberInput.setText(customer_data.get("phone_number", ""))
        self.ui.NotesInput.setPlainText(customer_data.get("notes", ""))

    def load_customer_data_page2(self, customer_data):
        """Load customer data into UI elements for Page 2."""
        self.ui.FirstNameInput_2.setText(customer_data.get("first_name", ""))
        self.ui.LastNameInput_2.setText(customer_data.get("last_name", ""))
        self.ui.PhoneNumberInput_2.setText(customer_data.get("phone_number", ""))
        self.ui.NotesInput_2.setPlainText(customer_data.get("notes", ""))

    def clear_customer_data_page1(self):
        """Clear customer data in UI elements for Page 1."""
        self.ui.FirstNameInput.clear()
        self.ui.LastNameInput.clear()
        self.ui.PhoneNumberInput.clear()
        self.ui.NotesInput.clear()
        self.customer_id1 = None
        self.customer_data1 = {}
        self.ui.ctlist.setRowCount(0)

    def clear_customer_data_page2(self):
        """Clear customer data in UI elements for Page 2."""
        self.ui.FirstNameInput_2.clear()
        self.ui.LastNameInput_2.clear()
        self.ui.PhoneNumberInput_2.clear()
        self.ui.NotesInput_2.clear()
        self.customer_id2 = None
        self.customer_data2 = {}
        self.ui.ctlist_2.setRowCount(0)

    def save_customer_data_page1(self):
        """Save customer data for Page 1 to the database."""
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
        """Save customer data for Page 2 to the database."""
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
        """Switch to Page 1."""
        self.ui.pageswidget.setCurrentIndex(0)

    def show_page2(self):
        """Switch to Page 2."""
        self.ui.pageswidget.setCurrentIndex(1)

    def open_search_window_page1(self):
        """Open search window for Page 1."""
        self.search_window = CustomerSearch(target_page=1)
        self.search_window.customer_selected.connect(self.load_customer_data_page1)
        self.search_window.show()

    def open_search_window_page2(self):
        """Open search window for Page 2."""
        self.search_window = CustomerSearch(target_page=2)
        self.search_window.customer_selected.connect(self.load_customer_data_page2)
        self.search_window.show()

    def open_quick_ticket_page1(self):
        """Open quick ticket window for Page 1."""
        print(f"Opening Quick Ticket for customer_id: {self.customer_id1}")
        ticket_id = self.fetch_ticket_id(self.ticket_id)
        self.quick_ticket_window = QuickTicketWindow(customer_id=self.customer_id1, employee_id=self.employee_id, ticket_id=self.ticket_id)
        self.quick_ticket_window.quick_ticket_created.connect(self.load_tickets_after_creation)
        self.quick_ticket_window.show()

    def open_quick_ticket_page2(self):
        """Open quick ticket window for Page 2."""
        print(f"Opening Quick Ticket for customer_id: {self.customer_id2}")
        ticket_id = self.fetch_ticket_id(self.customer_id2)
        self.quick_ticket_window = QuickTicketWindow(customer_id=self.customer_id2, employee_id=self.employee_id)
        self.quick_ticket_window.quick_ticket_created.connect(self.load_tickets_after_creation)
        self.quick_ticket_window.show()

    def open_detailed_ticket_page1(self, ticket_type_id):
        """Open detailed ticket window for Page 1."""
        self.detailed_ticket_window = DetailedTicketWindow(
            customer_id=self.customer_id1,
            ticket_type_id=ticket_type_id,
            employee_id=self.employee_id
        )
        self.detailed_ticket_window.ticket_completed.connect(self.on_ticket_completed)
        self.detailed_ticket_window.show()

    def open_detailed_ticket_page2(self, ticket_type_id):
        """Open detailed ticket window for Page 2."""
        self.detailed_ticket_window = DetailedTicketWindow(
            customer_id=self.customer_id2,
            ticket_type_id=ticket_type_id,
            employee_id=self.employee_id
        )
        self.detailed_ticket_window.ticket_completed.connect(self.on_ticket_completed)
        self.detailed_ticket_window.show()

    def load_tickets(self, customer_id, ctlist):
        """Load tickets from the database for a given customer ID and populate the UI table."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Retrieve detailed ticket data
        cursor.execute("""
            SELECT t.ticket_number, tt.name as ticket_type, t.date_created, t.date_due, t.total_price, t.status
            FROM Tickets t
            JOIN TicketTypes tt ON t.ticket_type_id = tt.id
            WHERE t.customer_id = ?
        """, (customer_id,))

        detailed_tickets = cursor.fetchall()

        # Retrieve quick ticket data
        cursor.execute("""
            SELECT qt.ticket_number, qt.ticket_type_id, qt.due_date, qt.pieces, qt.notes, qt.all_notes
            FROM quick_tickets qt
            WHERE qt.customer_id = ?
        """, (customer_id,))

        quick_tickets = cursor.fetchall()

        conn.close()

        ctlist.setRowCount(0)  # Clear existing rows

        # Populate detailed tickets
        for ticket in detailed_tickets:
            ticket_number, ticket_type, date_created, date_due, total_price, status = ticket
            row_position = ctlist.rowCount()
            ctlist.insertRow(row_position)

            # Create placeholders for the 'Picked Up', 'Location', and 'Due Date' columns
            picked_up_placeholder = "N/A"  # Placeholder for 'Picked Up' status
            location_placeholder = "N/A"  # Placeholder for 'Location'
            due_date_placeholder = date_due or "N/A"  # Placeholder or actual 'Due Date'

            # Fill the table row with the appropriate data
            ctlist.setItem(row_position, 0, QTableWidgetItem(str(ticket_number)))
            ctlist.setItem(row_position, 1, QTableWidgetItem(ticket_type))
            ctlist.setItem(row_position, 2, QTableWidgetItem(date_created))
            ctlist.setItem(row_position, 3, QTableWidgetItem(due_date_placeholder))  # Due Date placeholder
            ctlist.setItem(row_position, 4, QTableWidgetItem(location_placeholder))  # Location placeholder
            ctlist.setItem(row_position, 5, QTableWidgetItem(picked_up_placeholder))  # Picked Up placeholder
            ctlist.setItem(row_position, 6, QTableWidgetItem(f"{total_price:.2f}"))
            ctlist.setItem(row_position, 7, QTableWidgetItem(status))

        # Populate quick tickets
        for ticket in quick_tickets:
            ticket_number, ticket_type, due_date, pieces, notes, all_notes = ticket
            row_position = ctlist.rowCount()
            ctlist.insertRow(row_position)

            # Create placeholders for detailed tickets not available for quick tickets
            status_placeholder = "Quick Ticket"
            total_price_placeholder = "N/A"  # Quick tickets don't have a total price yet

            # Fill the table row with the appropriate data
            ctlist.setItem(row_position, 0, QTableWidgetItem(str(ticket_number)))
            ctlist.setItem(row_position, 1, QTableWidgetItem(ticket_type))
            ctlist.setItem(row_position, 2, QTableWidgetItem("N/A"))  # Date created not applicable
            ctlist.setItem(row_position, 3, QTableWidgetItem(due_date or "N/A"))
            ctlist.setItem(row_position, 4, QTableWidgetItem(str(pieces)))
            ctlist.setItem(row_position, 5, QTableWidgetItem(notes))
            ctlist.setItem(row_position, 6, QTableWidgetItem(total_price_placeholder))
            ctlist.setItem(row_position, 7, QTableWidgetItem(status_placeholder))

    def load_tickets_after_creation(self, data):
        """Callback to reload tickets after quick ticket creation."""
        customer_id = data.get('customer_id')
        if customer_id == self.customer_id1:
            self.load_tickets(self.customer_id1, self.ui.ctlist)
        elif customer_id == self.customer_id2:
            self.load_tickets(self.customer_id2, self.ui.ctlist_2)

    def convert_selected_quick_ticket(self, ctlist, customer_id):
        """Convert the selected quick ticket to a detailed ticket."""
        selected_row = ctlist.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a quick ticket to convert.")
            return

        # Retrieve the ticket details from the selected row
        ticket_number_item = ctlist.item(selected_row, 0)
        ticket_type_item = ctlist.item(selected_row, 1)
        due_date_item = ctlist.item(selected_row, 3)
        pieces_item = ctlist.item(selected_row, 4)
        notes_item = ctlist.item(selected_row, 5)

        if not ticket_number_item or not ticket_type_item:
            QMessageBox.warning(self, "Invalid Selection", "The selected item is not a valid quick ticket.")
            return

        ticket_number = int(ticket_number_item.text())
        ticket_type = ticket_type_item.text()
        due_date = due_date_item.text()
        pieces = int(pieces_item.text()) if pieces_item.text().isdigit() else 0
        notes = notes_item.text() if notes_item else ""

        # Prepare quick ticket data for conversion
        quick_ticket_data = {
            'customer_id': customer_id,
            'ticket_number': ticket_number,
            'ticket_type': ticket_type,
            'pieces': pieces,
            'due_date': due_date,
            'notes': notes,
            'all_notes': notes
        }

        # Emit the signal to convert the quick ticket to a detailed ticket
        self.convert_to_detailed_ticket.emit(quick_ticket_data)

        # Open the detailed ticket window with the quick ticket data
        detailed_ticket_window = DetailedTicketWindow(
            customer_id=customer_id,
            ticket_number=ticket_number,
            ticket_type_id=self.get_ticket_type_id(ticket_type),
            employee_id=self.employee_id,
            pieces=pieces,
            due_date=due_date,
            notes=notes,
            all_notes=notes
        )
        detailed_ticket_window.ticket_completed.connect(self.on_ticket_completed)
        detailed_ticket_window.show()

    def fetch_ticket_id(self, customer_id):
        """Fetch the latest ticket ID for the current customer."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM Tickets WHERE customer_id = ? ORDER BY id DESC LIMIT 1", (customer_id,))
        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def get_ticket_type_id(self, ticket_type_name):
        """Retrieve the ticket type ID based on the ticket type name."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM TicketTypes WHERE name = ?", (ticket_type_name,))
        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def on_ticket_completed(self, customer_id):
        """Reload tickets when a ticket is completed."""
        if customer_id == self.customer_id1:
            self.load_tickets(self.customer_id1, self.ui.ctlist)
        elif customer_id == self.customer_id2:
            self.load_tickets(self.customer_id2, self.ui.ctlist_2)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Pass the employee_id to the account window, assuming you have it after login
    account_window = CustomerAccountWindow(employee_id=1)  # Replace 1 with the actual employee_id
    account_window.show()
    sys.exit(app.exec())