from PySide6.QtWidgets import QMainWindow
from Test import Ui_Main
from customersearch import CustomerSearchWindow
from tickettype import TicketTypeCreationWindow
from garmentscolors import GarmentsColorsWindow
from ticketoptions import TicketOptionsWindow

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
        self.search_window = CustomerSearchWindow()
        self.search_window.show()

    def open_ticket_type_creation_window(self):
        self.ticket_type_creation_window = TicketTypeCreationWindow()
        self.ticket_type_creation_window.show()

    def open_garments_colors_window(self):
        self.garments_colors_window = GarmentsColorsWindow()
        self.garments_colors_window.show()

    def open_ticket_options_window(self):
        self.ticket_options_window = TicketOptionsWindow()
        self.ticket_options_window.show()
