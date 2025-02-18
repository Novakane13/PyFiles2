from PySide6.QtCore import (QCoreApplication, QMetaObject, QRect)
from PySide6.QtGui import (QFont)
from PySide6.QtWidgets import (QLabel, QPushButton, 
    QFrame, 
    QTableWidget, QHeaderView)


class Ui_Employee_List(object):
    def setupUi(self, Employee_List):
        if not Employee_List.objectName():
            Employee_List.setObjectName(u"Employee_List")
        Employee_List.resize(978, 596)

        self.newempbutton = QPushButton(Employee_List)
        self.newempbutton.setObjectName(u"newempbutton")
        self.newempbutton.setGeometry(QRect(862, 446, 100, 24))

        self.editempbutton = QPushButton(Employee_List)
        self.editempbutton.setObjectName(u"editempbutton")
        self.editempbutton.setGeometry(QRect(862, 471, 99, 24))

        self.backbutton = QPushButton(Employee_List)
        self.backbutton.setObjectName(u"backbutton")
        self.backbutton.setGeometry(QRect(862, 522, 98, 25))

        self.deleteempbutton = QPushButton(Employee_List)
        self.deleteempbutton.setObjectName(u"deleteempbutton")
        self.deleteempbutton.setGeometry(QRect(862, 496, 99, 25))

        self.EmployeeList = QTableWidget(Employee_List)
        self.EmployeeList.setObjectName(u"EmployeeList")
        self.EmployeeList.setGeometry(QRect(93, 103, 755, 444))
        self.EmployeeList.setColumnCount(7)
        self.EmployeeList.setHorizontalHeaderLabels([
            "ID", "Name", "Display Name", "Phone #", "Email", "Position/Role", "Date Hired"
])

        # Set header properties to make columns fill the width
        self.EmployeeList.horizontalHeader().setStretchLastSection(True)
        self.EmployeeList.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Make the table non-editable
        self.EmployeeList.setEditTriggers(QTableWidget.NoEditTriggers)

        self.label = QLabel(Employee_List)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(340, 63, 134, 38))
        font = QFont()
        font.setPointSize(20)
        self.label.setFont(font)

        self.line = QFrame(Employee_List)
        self.line.setObjectName(u"line")
        self.line.setGeometry(QRect(95, 56, 753, 16))
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.line_2 = QFrame(Employee_List)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setGeometry(QRect(836, 64, 20, 42))
        self.line_2.setFrameShape(QFrame.Shape.VLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.line_3 = QFrame(Employee_List)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setGeometry(QRect(85, 63, 20, 41))
        self.line_3.setFrameShape(QFrame.Shape.VLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.retranslateUi(Employee_List)
        QMetaObject.connectSlotsByName(Employee_List)

    def retranslateUi(self, Employee_List):
        Employee_List.setWindowTitle(QCoreApplication.translate("Employee_List", u"Employee List", None))
        self.newempbutton.setText(QCoreApplication.translate("Employee_List", u"New Employee", None))
        self.editempbutton.setText(QCoreApplication.translate("Employee_List", u"Edit Employee", None))
        self.backbutton.setText(QCoreApplication.translate("Employee_List", u"Back", None))
        self.deleteempbutton.setText(QCoreApplication.translate("Employee_List", u"Delete Employee", None))
        self.label.setText(QCoreApplication.translate("Employee_List", u"Employees", None))