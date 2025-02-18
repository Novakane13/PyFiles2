from PySide6.QtCore import QCoreApplication, QMetaObject, QRect
from PySide6.QtWidgets import (
    QPushButton, QLabel, QLineEdit, QListWidget, QStackedWidget, QWidget, QScrollArea, QVBoxLayout
)

class Ui_Employee_Creation(object):
    def setupUi(self, Employee_Creation):
        if not Employee_Creation.objectName():
            Employee_Creation.setObjectName("Employee_Creation")
        Employee_Creation.resize(800, 500)

        # Employee Information Inputs
        self.empdisplayname = QLineEdit(Employee_Creation)
        self.empdisplayname.setObjectName("empdisplayname")
        self.empdisplayname.setGeometry(QRect(50, 40, 250, 30))

        self.employeename = QLineEdit(Employee_Creation)
        self.employeename.setObjectName("employeename")
        self.employeename.setGeometry(QRect(50, 90, 250, 30))

        self.employeephone = QLineEdit(Employee_Creation)
        self.employeephone.setObjectName("employeephone")
        self.employeephone.setGeometry(QRect(50, 140, 250, 30))

        self.employeepin = QLineEdit(Employee_Creation)
        self.employeepin.setObjectName("employeepin")
        self.employeepin.setGeometry(QRect(50, 190, 250, 30))
        self.employeepin.setEchoMode(QLineEdit.Password)

        self.employeeemail = QLineEdit(Employee_Creation)
        self.employeeemail.setObjectName("employeeemail")
        self.employeeemail.setGeometry(QRect(50, 240, 250, 30))

        # Labels for Inputs
        self.displayname_label = QLabel(Employee_Creation)
        self.displayname_label.setObjectName("displayname_label")
        self.displayname_label.setGeometry(QRect(50, 20, 120, 20))

        self.employeename_label = QLabel(Employee_Creation)
        self.employeename_label.setObjectName("employeename_label")
        self.employeename_label.setGeometry(QRect(50, 70, 120, 20))

        self.employeephone_label = QLabel(Employee_Creation)
        self.employeephone_label.setObjectName("employeephone_label")
        self.employeephone_label.setGeometry(QRect(50, 120, 120, 20))

        self.employeepin_label = QLabel(Employee_Creation)
        self.employeepin_label.setObjectName("employeepin_label")
        self.employeepin_label.setGeometry(QRect(50, 170, 120, 20))

        self.employeeemaillabel = QLabel(Employee_Creation)
        self.employeeemaillabel.setObjectName("employeeemaillabel")
        self.employeeemaillabel.setGeometry(QRect(50, 220, 120, 20))

        self.saveemployeebutton = QPushButton(Employee_Creation)
        self.saveemployeebutton.setObjectName("saveemployeebutton")
        self.saveemployeebutton.setGeometry(QRect(300, 400, 120, 40))

        self.backbutton = QPushButton(Employee_Creation)
        self.backbutton.setObjectName("backbutton")
        self.backbutton.setGeometry(QRect(450, 400, 120, 40))

        self.clearpermissionsbutton = QPushButton(Employee_Creation)
        self.clearpermissionsbutton.setObjectName("clearpermissionsbutton")
        self.clearpermissionsbutton.setGeometry(QRect(50, 340, 250, 40))

       
        self.rolesandpermissions = QStackedWidget(Employee_Creation)
        self.rolesandpermissions.setObjectName("rolesandpermissions")
        self.rolesandpermissions.setGeometry(QRect(350, 40, 400, 300))

        
        self.roles_page = QWidget()
        self.roles_page.setObjectName("roles_page")
        self.roleslist = QListWidget(self.roles_page)
        self.roleslist.setObjectName("roleslist")
        self.roleslist.setGeometry(QRect(10, 10, 380, 280))
        self.rolesandpermissions.addWidget(self.roles_page)

      
        self.permissions_page = QWidget()
        self.permissions_page.setObjectName("permissions_page")
        self.permissionsscroll = QScrollArea(self.permissions_page)
        self.permissionsscroll.setObjectName("permissionsscroll")
        self.permissionsscroll.setGeometry(QRect(10, 10, 380, 280))
        self.permissionsscroll.setWidgetResizable(True)
        self.permissions_content = QWidget()
        self.permissions_content.setGeometry(0, 0, 360, 270)
        self.permissions_content.setObjectName("permissions_content")
        self.permissions_layout = QVBoxLayout(self.permissions_content)
        self.permissions_layout.setContentsMargins(0, 0, 0, 0)
        self.permissionsscroll.setWidget(self.permissions_content)
        self.rolesandpermissions.addWidget(self.permissions_page)

        
        self.roleselectbutton = QPushButton(Employee_Creation)
        self.roleselectbutton.setObjectName("roleselectbutton")
        self.roleselectbutton.setGeometry(QRect(50, 290, 120, 40))

        self.permissionselectbutton = QPushButton(Employee_Creation)
        self.permissionselectbutton.setObjectName("permissionselectbutton")
        self.permissionselectbutton.setGeometry(QRect(180, 290, 120, 40))

        self.retranslateUi(Employee_Creation)
        QMetaObject.connectSlotsByName(Employee_Creation)

    def retranslateUi(self, Employee_Creation):
        Employee_Creation.setWindowTitle(QCoreApplication.translate("Employee_Creation", "Employee Creation", None))
        self.displayname_label.setText(QCoreApplication.translate("Employee_Creation", "Display Name:", None))
        self.employeename_label.setText(QCoreApplication.translate("Employee_Creation", "Employee Name:", None))
        self.employeephone_label.setText(QCoreApplication.translate("Employee_Creation", "Phone Number:", None))
        self.employeepin_label.setText(QCoreApplication.translate("Employee_Creation", "Pin:", None))
        self.employeeemaillabel.setText(QCoreApplication.translate("Employee_Creation", "Email:", None))
        self.saveemployeebutton.setText(QCoreApplication.translate("Employee_Creation", "Save Employee", None))
        self.backbutton.setText(QCoreApplication.translate("Employee_Creation", "Back", None))
        self.roleselectbutton.setText(QCoreApplication.translate("Employee_Creation", "Select Roles", None))
        self.permissionselectbutton.setText(QCoreApplication.translate("Employee_Creation", "Select Permissions", None))
        self.clearpermissionsbutton.setText(QCoreApplication.translate("Employee_Creation", "Clear Permissions", None))
