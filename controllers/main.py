import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QDialog
from PySide6.QtCore import Qt

# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from controllers.homewindow import MainWindow
from employeelogin import EmployeeLogin  # Import the EmployeeLogin

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Initialize and show the employee login window
    login_window = EmployeeLogin()
    if login_window.exec() == QDialog.Accepted:
        employee_id = login_window.logged_in_employee_id  # Retrieve the employee ID
        main_window = MainWindow(employee_id=employee_id)  # Pass the employee ID to MainWindow
        main_window.show()
        sys.exit(app.exec())
