import sys
import sqlite3
import os
from PySide6.QtWidgets import QApplication, QDialog, QTreeWidgetItem, QAbstractItemView, QPushButton, QLineEdit
from PySide6.QtCore import Signal, Slot, Qt
from views.Test import Ui_CustomerSearch

class CustomerSearch(QDialog, Ui_CustomerSearch):
    customer_selected = Signal(dict)
    new_customer = Signal()

    def __init__(self, target_page=1):
        super().__init__()
        self.setupUi(self)
        self.target_page = target_page

        # Hide the last name and phone number input fields
        self.lnsearch.setVisible(False)
        self.lnlabel.setVisible(False)
        self.pnsearch.setVisible(False)
        self.pnlabel.setVisible(False)
        
        # Change the label of the first name input to a general search label
        self.fnlabel.setText("Search:")

        self.searchbutton.clicked.connect(self.search_customers)
        self.ncbutton.clicked.connect(self.create_new_customer)
        self.resultslist.itemDoubleClicked.connect(self.select_customer)
        
        # Connect Enter key press for the search input and result selection
        self.fnsearch.returnPressed.connect(self.search_customers)
        self.resultslist.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.resultslist.setSelectionMode(QAbstractItemView.SingleSelection)
        self.resultslist.keyPressEvent = self.resultslist_key_press_event

        # Set focus to the search input field when the dialog opens
        self.fnsearch.setFocus()

        # Remove default status from the "New Customer" button
        self.ncbutton.setAutoDefault(False)
        self.ncbutton.setDefault(False)

    @Slot()
    def search_customers(self):
        # Fetch search results from the database
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        query = """
        SELECT id, first_name, last_name, phone_number, notes
        FROM customers
        WHERE first_name LIKE ? OR last_name LIKE ? OR phone_number LIKE ?
        """
        
        search_term = f"%{self.fnsearch.text()}%"
        cursor.execute(query, (search_term, search_term, search_term))
        search_results = cursor.fetchall()
        
        self.resultslist.clear()
        for result in search_results:
            item = QTreeWidgetItem([f"{result[1]} {result[2]}", result[3]])
            item.setData(0, 1, {
                "id": result[0],
                "first_name": result[1],
                "last_name": result[2],
                "phone_number": result[3],
                "notes": result[4]
            })
            self.resultslist.addTopLevelItem(item)
        
        conn.close()

    @Slot(QTreeWidgetItem, int)
    def select_customer(self, item, column):
        customer_data = item.data(0, 1)
        self.customer_selected.emit(customer_data)
        self.close()

    def resultslist_key_press_event(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            selected_items = self.resultslist.selectedItems()
            if selected_items:
                self.select_customer(selected_items[0], 0)
        else:
            QAbstractItemView.keyPressEvent(self.resultslist, event)

    def create_new_customer(self):
        self.new_customer.emit()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    search_window = CustomerSearch()
    search_window.show()
    sys.exit(app.exec())
