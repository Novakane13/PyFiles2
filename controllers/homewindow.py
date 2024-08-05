import sys
import os
import sqlite3
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QApplication, QDialog, QMessageBox
from views.Test import Ui_Main
from controllers.customersearch import CustomerSearch
from controllers.tickettype import TicketTypeCreationWindow
from controllers.garmentscolors import GarmentsColorsWindow
from controllers.ticketoptions import TicketOptionsWindow
from controllers.customeraccount import CustomerAccountWindow
from garmentpricing import GarmentPricingWindow
from detailedticket import DetailedTicketWindow
from quickticket import QuickTicketWindow

class MainWindow(QMainWindow):
    def __init__(self, employee_id: int):
        super().__init__()
        self.ui = Ui_Main()  # Assume this is your main UI class generated from Qt Designer
        self.ui.setupUi(self)
        
        self.employee_id = employee_id

        # Connect buttons to their functions
        self.ui.ncbutton.clicked.connect(self.open_search_window)
        self.ui.ttcbutton.clicked.connect(self.open_ticket_type_creation_window)
        self.ui.gandccbutton.clicked.connect(self.open_garments_colors_window)
        self.ui.tocbutton.clicked.connect(self.open_ticket_options_window)
        self.ui.pushButton.clicked.connect(self.open_garment_pricing_window)


    def open_search_window(self):
        """Open the Customer Search window."""
        self.search_window = CustomerSearch()
        self.search_window.customer_selected.connect(self.open_customer_account_window)
        self.search_window.new_customer.connect(self.create_new_customer)
        self.search_window.show()

    def open_customer_account_window(self, customer_data1=None, customer_data2=None):
        """
        Open the Customer Account Window with provided customer data.
        
        Args:
            customer_data1 (dict): Customer data for the first customer.
            customer_data2 (dict): Customer data for the second customer (if applicable).
        """
        customer_data1 = customer_data1 or {
            'id': None,
            'first_name': '',
            'last_name': '',
            'phone_number': '',
            'notes': ''
        }

        customer_data2 = customer_data2 or {
            'id': None,
            'first_name': '',
            'last_name': '',
            'phone_number': '',
            'notes': ''
        }

        self.customer_account_window = CustomerAccountWindow(
            customer_data1=customer_data1,
            customer_data2=customer_data2,
            employee_id=self.employee_id
        )
        
        # Connect quick ticket creation to detailed ticket conversion
        self.customer_account_window.convert_to_detailed_ticket.connect(self.open_detailed_ticket_from_quick_ticket)
        
        self.customer_account_window.show()

    def create_new_customer(self):
        """Create a new customer and open the Customer Account window for them."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Insert a new customer into the database
        cursor.execute("""
            INSERT INTO customers (first_name, last_name, phone_number, notes)
            VALUES ('', '', '', '')
        """)
        new_customer_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Open the Customer Account Window for the new customer
        self.customer_account_window = CustomerAccountWindow(employee_id=self.employee_id)
        self.customer_account_window.load_customer_data_page1({
            'id': new_customer_id,
            'first_name': '',
            'last_name': '',
            'phone_number': '',
            'notes': ''
        })
        self.customer_account_window.show()

    def open_ticket_type_creation_window(self):
        """Open the Ticket Type Creation window."""
        self.ticket_type_creation_window = TicketTypeCreationWindow()
        self.ticket_type_creation_window.show()

    def open_garments_colors_window(self):
        """Open the Garments and Colors window."""
        self.garments_colors_window = GarmentsColorsWindow()
        self.garments_colors_window.show()

    def open_ticket_options_window(self):
        """Open the Ticket Options window."""
        self.ticket_options_window = TicketOptionsWindow()
        self.ticket_options_window.show()

    def open_garment_pricing_window(self):
        """Open the Garment Pricing window."""
        self.garment_pricing_window = GarmentPricingWindow()
        self.garment_pricing_window.show()

    def open_quick_ticket_window(self):
        """Open the Quick Ticket window."""
        # Assume you have a method to get the selected customer's ID
        customer_id = self.get_selected_customer_id()

        if customer_id is None:
            QMessageBox.warning(self, "Error", "Please select a customer before creating a ticket.")
            return

        self.quick_ticket_window = QuickTicketWindow(customer_id=customer_id, employee_id=self.employee_id)
        self.quick_ticket_window.quick_ticket_created.connect(self.open_detailed_ticket_from_quick_ticket)
        self.quick_ticket_window.show()

    def get_selected_customer_id(self):
        # Implement logic to retrieve the selected customer's ID from your UI
        # For example, using a table selection
        selected_row = self.ui.customerTable.currentRow()
        if selected_row != -1:
            return self.ui.customerTable.item(selected_row, 0).data(Qt.UserRole)
        return None

    def open_detailed_ticket_from_quick_ticket(self, quick_ticket_data):
        """
        Open a Detailed Ticket Window using data from a quick ticket.
        
        Args:
            quick_ticket_data (dict): The data from the quick ticket, including customer ID and ticket details.
        """
        for ticket in quick_ticket_data['tickets']:
            # Resolve the ticket type ID from the ticket type name
            ticket_type_id = self.get_ticket_type_id(ticket['ticket_type'])

            detailed_ticket_window = DetailedTicketWindow(
                customer_id=quick_ticket_data['customer_id'],
                ticket_type=ticket['ticket_type'],
                ticket_type_id=ticket_type_id,
                employee_id=self.employee_id,
                ticket_number=ticket['ticket_number'],
                pieces=ticket['pieces'],
                due_date=ticket['due_date'],
                notes=ticket['notes'],
                all_notes=ticket['all_notes']
            )
            detailed_ticket_window.ticket_completed.connect(self.on_ticket_completed)
            detailed_ticket_window.show()

    def get_ticket_type_id(self, ticket_type_name):
        """
        Resolve the ticket type name to its corresponding ID.
        
        Args:
            ticket_type_name (str): The name of the ticket type.
        
        Returns:
            int: The ID of the ticket type, or None if not found.
        """
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM TicketTypes WHERE name = ?", (ticket_type_name,))
        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def on_ticket_completed(self, customer_id):
        """
        Handle actions when a ticket is completed.
        
        Args:
            customer_id (int): The ID of the customer whose ticket was completed.
        """
        # Update UI or perform any necessary actions when a ticket is completed
        # For example, refresh the customer account window or reload tickets
        if self.customer_account_window:
            self.customer_account_window.load_tickets(customer_id, self.customer_account_window.ui.ctlist)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    main_window = MainWindow(employee_id=1)  # Pass a valid employee ID from login
    main_window.show()
    sys.exit(app.exec())