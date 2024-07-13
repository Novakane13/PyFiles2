from PySide6.QtWidgets import QMainWindow
from Test import Ui_DetailedTicketCreation

class DetailedTicketWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_DetailedTicketCreation()
        self.ui.setupUi(self)
        self.ui.canceltbutton.clicked.connect(self.close)  # using 'canceltbutton' for close functionality
        self.ui.ptandtbutton.clicked.connect(self.complete_ticket)  # using 'ptandtbutton' for complete ticket functionality

    def complete_ticket(self):
        # Functionality to complete the ticket
        pass
