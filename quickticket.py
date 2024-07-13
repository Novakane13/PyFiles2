from PySide6.QtWidgets import QMainWindow
from Test import Ui_QuickTicketCreation

class QuickTicketWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_QuickTicketCreation()
        self.ui.setupUi(self)
        self.ui.qtclosebutton.clicked.connect(self.close)  # correct widget name 'qtclosebutton'
