import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from Test import Ui_Main
from customersearch import CustomerSearch
from tickettype import TicketTypeCreationWindow
from garmentscolors import GarmentsColorsWindow
from ticketoptions import TicketOptionsWindow
from customeraccount import CustomerAccountWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Main()
        self.ui.setupUi(self)

        # Connect buttons to their functions
        self.ui.ncbutton.clicked.connect(self.open_search_window)
        self.ui.ttcbutton.clicked.connect(self.open_ticket_type_creation_window)
        self.ui.gandccbutton.clicked.connect(self.open_garments_colors_window)
        self.ui.tocbutton.clicked.connect(self.open_ticket_options_window)

    def open_search_window(self):
        self.search_window = CustomerSearch()
        self.search_window.customer_selected.connect(self.open_customer_account_window)
        self.search_window.new_customer.connect(self.create_new_customer)
        self.search_window.show()

    def open_customer_account_window(self, customer_data):
        customer_data2 = {
            "id": None,
            "first_name": "",
            "last_name": "",
            "phone_number": "",
            "notes": ""
        }
        self.customer_account_window = CustomerAccountWindow(customer_data, customer_data2)
        self.customer_account_window.show()

    def create_new_customer(self):
        customer_data1 = {
            "id": None,
            "first_name": "",
            "last_name": "",
            "phone_number": "",
            "notes": ""
        }
        customer_data2 = {
            "id": None,
            "first_name": "",
            "last_name": "",
            "phone_number": "",
            "notes": ""
        }
        self.customer_account_window = CustomerAccountWindow(customer_data1, customer_data2)
        self.customer_account_window.show()

    def open_ticket_type_creation_window(self):
        self.ticket_type_creation_window = TicketTypeCreationWindow()
        self.ticket_type_creation_window.show()

    def open_garments_colors_window(self):
        self.garments_colors_window = GarmentsColorsWindow()
        self.garments_colors_window.show()

    def open_ticket_options_window(self):
        self.ticket_options_window = TicketOptionsWindow()
        self.ticket_options_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
