import sys
import sqlite3
import bcrypt
import os
from PySide6.QtWidgets import QDialog, QMessageBox
from views.Test import Ui_EmployeeLogin  # Import the EmployeeLogin UI

# Database connection
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db_path = os.path.join(project_root, 'models', 'pos_system.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

class EmployeeLogin(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_EmployeeLogin()
        self.ui.setupUi(self)
        
        # Connect buttons to their functions
        self.ui.LoginButton.clicked.connect(self.login)
        self.ui.LogOutButton.clicked.connect(self.logout)
        self.ui.CreateEmployeeButton.clicked.connect(self.create_employee)

        self.logged_in_employee_id = None  # Store the logged-in employee ID

    def login(self):
        employee_name = self.ui.EmployeeNameLogin.text()
        password = self.ui.EmployeePassword.text()
        
        # Retrieve employee ID and hashed password
        cursor.execute("SELECT employee_id, password_hash FROM Employees WHERE employee_name=?", (employee_name))
        result = cursor.fetchone()

        if result and check_password(password, result[1]):
            self.logged_in_employee_id = result[0]  # Store employee ID
            QMessageBox.information(self, "Login Successful", f"Welcome, {employee_name}!")
            self.accept()  # Proceed to next step, e.g., open main window
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid employee name or password.")

    def logout(self):
        if self.logged_in_employee_id is not None:
            QMessageBox.information(self, "Logout Successful", f"Goodbye, {self.ui.EmployeeNameLogin.text()}!")
            self.logged_in_employee_id = None
            self.reject()  # Close the login dialog or reset state
        else:
            QMessageBox.warning(self, "Logout Failed", "No employee is currently logged in.")

    def create_employee(self):
        employee_name = self.ui.EmployeeNameLogin.text()
        password = self.ui.EmployeePassword.text()

        if not employee_name or not password:
            QMessageBox.warning(self, "Error", "Employee name and password cannot be empty.")
            return

        password_hash = hash_password(password)
        try:
            cursor.execute("INSERT INTO employees (employee_name, password_hash) VALUES (?, ?)", (employee_name, password_hash))
            conn.commit()
            QMessageBox.information(self, "Employee Created", f"Employee {employee_name} created successfully!")
            self.ui.EmployeeNameLogin.clear()
            self.ui.EmployeePassword.clear()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "Employee name already exists.")

# Example usage: Integrating with the main application
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from customeraccount import CustomerAccountWindow

    app = QApplication(sys.argv)
    login_dialog = EmployeeLogin()

    if login_dialog.exec() == QDialog.Accepted:
        employee_id = login_dialog.logged_in_employee_id
        if employee_id is not None:
            # Proceed to open the main application window with the logged-in employee_id
            account_window = CustomerAccountWindow(employee_id=employee_id)
            account_window.show()
    
    sys.exit(app.exec())
