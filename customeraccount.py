from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton, QLineEdit, QTextEdit, QTreeWidgetItem
from Test import Ui_CustomerAccount
import sqlite3

from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton, QLineEdit, QTextEdit, QApplication
from Test import Ui_CustomerAccount
import sqlite3
import sys
from customersearchnewtab import SearchWindowForNewTab

class CustomerAccountWindow(QMainWindow):
    def __init__(self, customer_id=None):
        super().__init__()

        self.ui = Ui_CustomerAccount()
        self.ui.setupUi(self)
        self.customer_tabs = self.ui.catabs
        self.search_window_for_new_tab = None

        if customer_id is not None:
            self.load_customer_tab(customer_id, 0)
        else:
            self.add_new_tab_button()

        self.customer_tabs.tabBarDoubleClicked.connect(self.open_search_window_for_new_tab)
        self.customer_tabs.currentChanged.connect(self.on_tab_change)

    def add_new_tab_button(self):
        new_tab_button = QPushButton("New Customer")
        new_tab_button.clicked.connect(self.open_search_window_for_new_tab)
        new_tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(new_tab_button)
        new_tab.setLayout(layout)
        self.customer_tabs.addTab(new_tab, "New Customer")

    def open_search_window_for_new_tab(self):
        from customersearch import SearchWindowForNewTab  # Import here to avoid circular dependency
        if not self.search_window_for_new_tab:
            self.search_window_for_new_tab = SearchWindowForNewTab()
            self.search_window_for_new_tab.customer_selected.connect(self.load_customer_tab_for_new_tab)
        self.search_window_for_new_tab.show()

    def on_tab_change(self, index):
        # Ensure the search window only opens for the second tab (index 1)
        if index == 1:
            self.open_search_window_for_new_tab()

    def load_customer_tab(self, customer_id, tab_index):
        customer_info = self.get_customer_info(customer_id)
        tab = self.customer_tabs.widget(tab_index)
        if tab is None or isinstance(tab.layout(), QVBoxLayout):
            tab = QWidget()
            self.customer_tabs.insertTab(tab_index, tab, customer_info['name'])
        self.populate_customer_tab(tab, customer_info, customer_id)
        self.customer_tabs.setTabText(tab_index, customer_info['name'])
        self.customer_tabs.setCurrentWidget(tab)

    def load_customer_tab_for_new_tab(self, customer_id):
        customer_info = self.get_customer_info(customer_id)
        tab_index = 1  # Ensure we are targeting the second tab
        tab = self.customer_tabs.widget(tab_index)
        if tab is None or isinstance(tab.layout(), QVBoxLayout):
            tab = QWidget()
            self.customer_tabs.insertTab(tab_index, tab, customer_info['name'])
        self.populate_customer_tab(tab, customer_info, customer_id)
        self.customer_tabs.setTabText(tab_index, customer_info['name'])
        self.customer_tabs.setCurrentWidget(tab)

    def populate_customer_tab(self, tab, customer_info, customer_id):
        lninput = tab.findChild(QLineEdit, "lninput")
        fninput = tab.findChild(QLineEdit, "fninput")
        pninput = tab.findChild(QLineEdit, "pninput")
        ninput = tab.findChild(QTextEdit, "ninput")

        if lninput:
            lninput.setText(customer_info['last_name'])
            lninput.focusOutEvent = lambda event: self.save_customer_info(customer_id, tab, event)
        if fninput:
            fninput.setText(customer_info['first_name'])
            fninput.focusOutEvent = lambda event: self.save_customer_info(customer_id, tab, event)
        if pninput:
            pninput.setText(customer_info['phone_number'])
            pninput.focusOutEvent = lambda event: self.save_customer_info(customer_id, tab, event)
        if ninput:
            ninput.setPlainText(customer_info['notes'])
            ninput.focusOutEvent = lambda event: self.save_customer_info(customer_id, tab, event)

    def save_customer_info(self, customer_id, tab, event):
        lninput = tab.findChild(QLineEdit, "lninput")
        fninput = tab.findChild(QLineEdit, "fninput")
        pninput = tab.findChild(QLineEdit, "pninput")
        ninput = tab.findChild(QTextEdit, "ninput")

        conn = sqlite3.connect("pos_system.db")
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE customers SET first_name = ?, last_name = ?, phone_number = ?, notes = ? WHERE id = ?
        """, (fninput.text(), lninput.text(), pninput.text(), ninput.toPlainText(), customer_id))
        conn.commit()
        conn.close()

        # Call the original focusOutEvent
        if isinstance(event, QLineEdit):
            QLineEdit.focusOutEvent(event, event)
        elif isinstance(event, QTextEdit):
            QTextEdit.focusOutEvent(event, event)

    def get_customer_info(self, customer_id):
        conn = sqlite3.connect("pos_system.db")
        cursor = conn.cursor()
        query = "SELECT first_name, last_name, phone_number, notes FROM customers WHERE id = ?"
        cursor.execute(query, (customer_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {
                'first_name': result[0],
                'last_name': result[1],
                'phone_number': result[2],
                'notes': result[3],
                'name': f"{result[0]} {result[1]}"
            }
        return {}