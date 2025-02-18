from PySide6.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, \
    QAbstractItemView, QHeaderView
from views.employeelistui import Ui_Employee_List
from controllers.employeecreation import EmployeeCreationDialog

import sqlite3
import os
from PySide6.QtGui import Qt

# Database path setup
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db_path = os.path.join(project_root, 'models', 'pos_system.db')


class EmployeeListWindow(QMainWindow):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.ui = Ui_Employee_List()
        self.ui.setupUi(self)
        self.setup_ui()

    def setup_ui(self):
        # Configure table behavior
        self.ui.EmployeeList.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.EmployeeList.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ui.EmployeeList.horizontalHeader().setStretchLastSection(True)
        self.ui.EmployeeList.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Connect buttons to functions
        self.ui.newempbutton.clicked.connect(self.open_create_employee_dialog)
        self.ui.editempbutton.clicked.connect(self.open_edit_employee_dialog)
        self.ui.deleteempbutton.clicked.connect(self.delete_employee)
        self.ui.backbutton.clicked.connect(self.go_back)

        # Load employee data into the table
        self.load_employees()

    def go_back(self):
        if self.main_window:
            self.main_window.show()
        self.close()

    def load_employees(self):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Clear the table before reloading data
            self.ui.EmployeeList.setRowCount(0)

            # SQL query to fetch employee details
            query = """
            SELECT e.employee_id, e.employee_name, e.display_name, e.phone_number,
                   e.email, COALESCE(r.name, 'Custom') AS role, e.date_created
            FROM Employees e
            LEFT JOIN employee_roles er ON e.employee_id = er.employee_id
            LEFT JOIN roles r ON er.role_id = r.id
            """
            cursor.execute(query)
            employees = cursor.fetchall()

            # Populate the table with data
            for row_idx, employee in enumerate(employees):
                self.ui.EmployeeList.insertRow(row_idx)

                # Set `employee_id` in a hidden column (column 0)
                employee_id_item = QTableWidgetItem(str(employee[0]))
                employee_id_item.setFlags(employee_id_item.flags() ^ Qt.ItemIsEditable)  # Read-only
                self.ui.EmployeeList.setItem(row_idx, 0, employee_id_item)
                self.ui.EmployeeList.setColumnHidden(0, True)  # Hide the employee_id column

                # Add remaining columns
                for col_idx, value in enumerate(employee[1:], start=1):
                    item = QTableWidgetItem(str(value) if value else "None")
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # Make cells read-only
                    self.ui.EmployeeList.setItem(row_idx, col_idx, item)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
        finally:
            if conn:
                conn.close()

    def open_create_employee_dialog(self):
        dialog = EmployeeCreationDialog()
        if dialog.exec():
            self.load_employees()

    def open_edit_employee_dialog(self):
        selected_row = self.ui.EmployeeList.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Warning", "Please select an employee to edit.")
            return

        try:
            # Fetch `employee_id` from the hidden column
            employee_id = int(self.ui.EmployeeList.item(selected_row, 0).text())
        except (ValueError, AttributeError):
            QMessageBox.warning(self, "Error", "Invalid employee data. Could not retrieve employee ID.")
            return

        # Open the EmployeeCreationDialog for editing
        dialog = EmployeeCreationDialog(employee_id=employee_id)
        if dialog.exec():
            self.load_employees()

    def delete_employee(self):
        selected_row = self.ui.EmployeeList.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Warning", "Please select an employee to delete.")
            return

        try:
            # Fetch the `employee_id` from the hidden column
            employee_id = int(self.ui.EmployeeList.item(selected_row, 0).text())
        except (ValueError, AttributeError):
            QMessageBox.warning(self, "Error", "Invalid employee data. Could not retrieve employee ID.")
            return

        confirm = QMessageBox.question(self, "Confirm", f"Are you sure you want to delete this employee?")
        if confirm == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # Delete the employee record
                cursor.execute("DELETE FROM Employees WHERE employee_id = ?", (employee_id,))
                conn.commit()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
            finally:
                if conn:
                    conn.close()

            self.load_employees()
