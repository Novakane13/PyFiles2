from PySide6.QtWidgets import QMainWindow, QTreeWidgetItem
from PySide6.QtCore import Signal, Qt
from Test import Ui_CustomerSearch
import sqlite3

class SearchWindowForNewTab(QMainWindow):
    customer_selected = Signal(int)

    def __init__(self):
        super().__init__()
        self.ui = Ui_CustomerSearch()
        self.ui.setupUi(self)
        self.ui.ncbutton.clicked.connect(self.open_new_customer_account_window)
        self.ui.searchbutton.clicked.connect(self.search_customers)
        self.ui.closebutton.clicked.connect(self.close)
        self.customer_windows = []

    def open_new_customer_account_window(self):
        from customeraccount import CustomerAccountWindow
        customer_account_window = CustomerAccountWindow()
        customer_account_window.show()
        self.customer_windows.append(customer_account_window)

    def search_customers(self):
        last_name = self.ui.lnsearch.text()
        first_name = self.ui.fnsearch.text()
        phone_number = self.ui.pnsearch.text()

        conn = sqlite3.connect("pos_system.db")
        cursor = conn.cursor()

        query = """
        SELECT id, first_name, last_name, phone_number FROM customers 
        WHERE last_name LIKE ? OR first_name LIKE ? OR phone_number LIKE ?
        """
        cursor.execute(query, ('%' + last_name + '%', '%' + first_name + '%', '%' + phone_number + '%'))
        results = cursor.fetchall()
        conn.close()

        self.ui.resultslist.clear()
        for result in results:
            item = QTreeWidgetItem(self.ui.resultslist)
            item.setText(0, f"{result[1]} {result[2]}")
            item.setText(1, result[3])
            item.setData(0, Qt.UserRole, result[0])
            self.ui.resultslist.addTopLevelItem(item)

        self.ui.resultslist.itemDoubleClicked.connect(self.select_customer)

    def select_customer(self, item):
        customer_id = item.data(0, Qt.UserRole)
        self.customer_selected.emit(customer_id)
        self.close()
