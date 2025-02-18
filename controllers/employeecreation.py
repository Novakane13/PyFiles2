from PySide6.QtWidgets import QDialog, QListWidgetItem, QMessageBox, QCheckBox
from PySide6.QtGui import Qt
from views.employeecreationui import Ui_Employee_Creation
from views.utils import hash_password, get_db_connection


class EmployeeCreationDialog(QDialog):
    def __init__(self, employee_id=None, parent=None):
        super().__init__(parent)
        self.ui = Ui_Employee_Creation()
        self.ui.setupUi(self)
        self.employee_id = employee_id

        # Connect buttons
        self.ui.roleselectbutton.clicked.connect(self.show_roles)
        self.ui.permissionselectbutton.clicked.connect(self.show_permissions)
        self.ui.saveemployeebutton.clicked.connect(self.save_employee)
        self.ui.backbutton.clicked.connect(self.close)
        self.ui.clearpermissionsbutton.clicked.connect(self.clear_permissions)

        # Load roles and permissions
        self.load_roles()
        self.load_permissions()

        if self.employee_id:
            self.load_employee_data()

    def show_roles(self):
        self.ui.rolesandpermissions.setCurrentIndex(0)

    def show_permissions(self):
        self.ui.rolesandpermissions.setCurrentIndex(1)

    def load_roles(self):
        self.ui.roleslist.clear()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM roles")
        roles = cursor.fetchall()
        for role in roles:
            item = QListWidgetItem(role[0])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.ui.roleslist.addItem(item)
        self.ui.roleslist.itemClicked.connect(self.update_permissions_based_on_role)
        conn.close()

    def load_permissions(self):
        while self.ui.permissions_layout.count():
            item = self.ui.permissions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM permissions")
        permissions = cursor.fetchall()
        for permission_id, permission_name in permissions:
            checkbox = QCheckBox(permission_name)
            checkbox.setProperty("permission_id", permission_id)
            checkbox.stateChanged.connect(self.handle_custom_role)
            self.ui.permissions_layout.addWidget(checkbox)
        conn.close()

    def update_permissions_based_on_role(self, item):
        """Auto-check permissions based on the selected role."""
        if item.checkState() == Qt.Checked:
            # Uncheck all other roles
            for i in range(self.ui.roleslist.count()):
                other_item = self.ui.roleslist.item(i)
                if other_item != item:
                    other_item.setCheckState(Qt.Unchecked)

            # Fetch permissions for the selected role
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id
                FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                JOIN roles r ON rp.role_id = r.id
                WHERE r.name = ?
            """, (item.text(),))
            role_permissions = {perm[0] for perm in cursor.fetchall()}
            conn.close()

            # Auto-check permissions for the role
            for i in range(self.ui.permissions_layout.count()):
                widget = self.ui.permissions_layout.itemAt(i).widget()
                if isinstance(widget, QCheckBox):
                    widget.setChecked(widget.property("permission_id") in role_permissions)
        else:
            self.clear_permissions()

    def clear_permissions(self):
        """Clear all selected permissions."""
        for i in range(self.ui.permissions_layout.count()):
            widget = self.ui.permissions_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox):
                widget.setChecked(False)

    def handle_custom_role(self):
        """Assign a 'custom' role if individual permissions are selected without a role."""
        selected_role = None
        for i in range(self.ui.roleslist.count()):
            role_item = self.ui.roleslist.item(i)
            if role_item.checkState() == Qt.Checked:
                selected_role = role_item.text()
                break

        if selected_role:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id
                FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                JOIN roles r ON rp.role_id = r.id
                WHERE r.name = ?
            """, (selected_role,))
            role_permissions = {perm[0] for perm in cursor.fetchall()}
            conn.close()

            for i in range(self.ui.permissions_layout.count()):
                widget = self.ui.permissions_layout.itemAt(i).widget()
                if isinstance(widget, QCheckBox) and widget.isChecked() and widget.property("permission_id") not in role_permissions:
                    # Clear role selection if additional permission is selected
                    for j in range(self.ui.roleslist.count()):
                        self.ui.roleslist.item(j).setCheckState(Qt.Unchecked)
                    break

    def load_employee_data(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT display_name, employee_name, phone_number, email
            FROM Employees
            WHERE employee_id = ?
        """, (self.employee_id,))
        employee = cursor.fetchone()

        if employee:
            self.ui.empdisplayname.setText(employee["display_name"])
            self.ui.employeename.setText(employee["employee_name"])
            self.ui.employeephone.setText(employee["phone_number"])
            self.ui.employeeemail.setText(employee["email"])

            cursor.execute("""
                SELECT r.name
                FROM roles r
                JOIN employee_roles er ON r.id = er.role_id
                WHERE er.employee_id = ?
            """, (self.employee_id,))
            roles = [role[0] for role in cursor.fetchall()]
            for i in range(self.ui.roleslist.count()):
                item = self.ui.roleslist.item(i)
                if item.text() in roles:
                    item.setCheckState(Qt.Checked)

            cursor.execute("""
                SELECT permission_id
                FROM employee_permissions
                WHERE employee_id = ?
            """, (self.employee_id,))
            permissions = [perm[0] for perm in cursor.fetchall()]
            for i in range(self.ui.permissions_layout.count()):
                widget = self.ui.permissions_layout.itemAt(i).widget()
                if isinstance(widget, QCheckBox):
                    widget.setChecked(widget.property("permission_id") in permissions)

        conn.close()

    def save_employee(self):
        display_name = self.ui.empdisplayname.text()
        employee_name = self.ui.employeename.text()
        phone = self.ui.employeephone.text()
        email = self.ui.employeeemail.text()
        pin = self.ui.employeepin.text()

        selected_roles = [self.ui.roleslist.item(i).text()
                          for i in range(self.ui.roleslist.count())
                          if self.ui.roleslist.item(i).checkState() == Qt.Checked]
        selected_permissions = [
            widget.property("permission_id")
            for i in range(self.ui.permissions_layout.count())
            if isinstance((widget := self.ui.permissions_layout.itemAt(i).widget()), QCheckBox) and widget.isChecked()
        ]

        if not display_name or not employee_name:
            QMessageBox.warning(self, "Error", "Display name and employee name cannot be empty.")
            return

        conn = get_db_connection()
        cursor = conn.cursor()

        if self.employee_id:
            # Update existing employee
            if pin.strip():
                hashed_password = hash_password(pin)
                cursor.execute("""
                    UPDATE Employees
                    SET display_name = ?, employee_name = ?, phone_number = ?, email = ?, password_hash = ?
                    WHERE employee_id = ?
                """, (display_name, employee_name, phone, email, hashed_password, self.employee_id))
            else:
                cursor.execute("""
                    UPDATE Employees
                    SET display_name = ?, employee_name = ?, phone_number = ?, email = ?
                    WHERE employee_id = ?
                """, (display_name, employee_name, phone, email, self.employee_id))

            # Clear existing roles and permissions
            cursor.execute("DELETE FROM employee_roles WHERE employee_id = ?", (self.employee_id,))
            cursor.execute("DELETE FROM employee_permissions WHERE employee_id = ?", (self.employee_id,))
        else:
            # Insert new employee
            if not pin.strip():
                QMessageBox.warning(self, "Error", "A password is required to create a new employee.")
                return

            hashed_password = hash_password(pin)
            cursor.execute("""
                INSERT INTO Employees (display_name, employee_name, phone_number, email, password_hash, date_created)
                VALUES (?, ?, ?, ?, ?, DATETIME('now'))
            """, (display_name, employee_name, phone, email, hashed_password))
            self.employee_id = cursor.lastrowid

        for role_name in selected_roles:
            cursor.execute("""
                INSERT INTO employee_roles (employee_id, role_id)
                VALUES (?, (SELECT id FROM roles WHERE name = ?))
            """, (self.employee_id, role_name))

        for permission_id in selected_permissions:
            cursor.execute("""
                INSERT INTO employee_permissions (employee_id, permission_id)
                VALUES (?, ?)
            """, (self.employee_id, permission_id))

        conn.commit()
        conn.close()

        QMessageBox.information(self, "Success", "Employee saved successfully!")
        self.accept()
