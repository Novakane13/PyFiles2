import sqlite3
import os
from PySide6.QtWidgets import QMainWindow, QMessageBox
from PySide6.QtCore import QDateTime, Signal
from views.quickticketui import Ui_QuickTicketCreation
from views.utils import get_next_ticket_number





class QuickTicketWindow(QMainWindow):
    quick_ticket_created = Signal(dict)

    def __init__(self, customer_id=None, employee_id=None, ticket_id=None):
        super().__init__()
        self.ui = Ui_QuickTicketCreation()
        self.ui.setupUi(self)

        # Debug: Print initial IDs
        print(f"Initializing QuickTicketWindow with customer_id: {customer_id}, employee_id: {employee_id}, ticket_id: {ticket_id}")

        self.customer_id = customer_id
        self.employee_id = employee_id
        self.ticket_data = {}
        self.ticket_id = ticket_id
        if self.ticket_id:
            self.load_existing_ticket_data()

        # Connect button signals
        self.ui.qtclosebutton.clicked.connect(self.close)
        self.ui.qtsandpbutton.clicked.connect(self.save_and_print_ticket)
        self.ui.createdetailedticket.clicked.connect(self.create_detailed_tickets)

        # Set up dials so that each represents -48 to +48 hours (a total of 96 hours or 4 days)
        for dial in [self.ui.dial_1, self.ui.dial_2, self.ui.dial_3]:
            dial.setRange(-48, 48)
            dial.setSingleStep(1)
            dial.setValue(0)

        # Initialize QDateTimeEdits to current date/time and store them as the "base" datetimes.
        self.ui.dateTimeEdit_1.setDateTime(QDateTime.currentDateTime())
        self.ui.dateTimeEdit_2.setDateTime(QDateTime.currentDateTime())
        self.ui.dateTimeEdit_3.setDateTime(QDateTime.currentDateTime())
        self.base_datetime1 = self.ui.dateTimeEdit_1.dateTime()
        self.base_datetime2 = self.ui.dateTimeEdit_2.dateTime()
        self.base_datetime3 = self.ui.dateTimeEdit_3.dateTime()

        # Connect dial changes to update the corresponding QDateTimeEdit
        self.ui.dial_1.valueChanged.connect(self.update_due_date_or_time1)
        self.ui.dial_2.valueChanged.connect(self.update_due_date_or_time2)
        self.ui.dial_3.valueChanged.connect(self.update_due_date_or_time3)

        # When the user manually changes the QDateTimeEdit, update the base datetime and reset the dial.
        self.ui.dateTimeEdit_1.dateTimeChanged.connect(self.update_base_datetime1)
        self.ui.dateTimeEdit_2.dateTimeChanged.connect(self.update_base_datetime2)
        self.ui.dateTimeEdit_3.dateTimeChanged.connect(self.update_base_datetime3)

        self.populate_ticket_types()

    def update_due_date_or_time1(self, offset_hours):
        """
        Update dateTimeEdit_1 based on the dial's offset (in hours) added to the base datetime.
        """
        new_dt = self.base_datetime1.addSecs(offset_hours * 3600)
        self.ui.dateTimeEdit_1.setDateTime(new_dt)

    def update_due_date_or_time2(self, offset_hours):
        new_dt = self.base_datetime2.addSecs(offset_hours * 3600)
        self.ui.dateTimeEdit_2.setDateTime(new_dt)

    def update_due_date_or_time3(self, offset_hours):
        new_dt = self.base_datetime3.addSecs(offset_hours * 3600)
        self.ui.dateTimeEdit_3.setDateTime(new_dt)

    def update_base_datetime1(self, new_datetime):
        """
        When the user manually updates dateTimeEdit_1, update the stored base datetime and reset dial_1.
        """
        self.base_datetime1 = new_datetime
        self.ui.dial_1.blockSignals(True)
        self.ui.dial_1.setValue(0)
        self.ui.dial_1.blockSignals(False)

    def update_base_datetime2(self, new_datetime):
        self.base_datetime2 = new_datetime
        self.ui.dial_2.blockSignals(True)
        self.ui.dial_2.setValue(0)
        self.ui.dial_2.blockSignals(False)

    def update_base_datetime3(self, new_datetime):
        self.base_datetime3 = new_datetime
        self.ui.dial_3.blockSignals(True)
        self.ui.dial_3.setValue(0)
        self.ui.dial_3.blockSignals(False)

    def populate_ticket_types(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, name FROM TicketTypes")
        ticket_types = cursor.fetchall()
        conn.close()

        self.ui.ttselection.clear()
        self.ui.ttselection_2.clear()
        self.ui.ttselection_3.clear()

        for ticket_type in ticket_types:
            ticket_type_id, ticket_type_name = ticket_type
            self.ui.ttselection.addItem(ticket_type_name, ticket_type_id)
            self.ui.ttselection_2.addItem(ticket_type_name, ticket_type_id)
            self.ui.ttselection_3.addItem(ticket_type_name, ticket_type_id)

    def populate_ticket_data(self):
        self.ticket_data = {
            'customer_id': self.customer_id,
            'employee_id': self.employee_id,
        }

    def construct_quick_ticket_details(self, ticket_number, ticket_data):
        quick_ticket_details = {
            'ticket_number': ticket_number,
            'customer_id': self.customer_id,
            'employee_id': self.employee_id,
            'ticket_type_1': {
                'ticket_type_id': ticket_data[0][0],
                'pieces': ticket_data[0][1],
                'due_date': ticket_data[0][2],
                'notes': ticket_data[0][3]
            } if ticket_data[0][0] else None,
            'ticket_type_2': {
                'ticket_type_id': ticket_data[1][0],
                'pieces': ticket_data[1][1],
                'due_date': ticket_data[1][2],
                'notes': ticket_data[1][3]
            } if ticket_data[1][0] else None,
            'ticket_type_3': {
                'ticket_type_id': ticket_data[2][0],
                'pieces': ticket_data[2][1],
                'due_date': ticket_data[2][2],
                'notes': ticket_data[2][3]
            } if ticket_data[2][0] else None,
            'all_notes': self.ui.atninput.toPlainText()
        }
        return quick_ticket_details

    def save_and_print_ticket(self):
        self.populate_ticket_data()
        if self.customer_id is None or self.employee_id is None:
            QMessageBox.warning(self, "Input Error", "Customer ID or Employee ID is missing.")
            return

        next_ticket_number = get_next_ticket_number() if self.ticket_id is None else self.ticket_id
        ticket_data = [self.get_ticket_data(i) for i in range(1, 4)]
        if not any(data[0] for data in ticket_data):
            QMessageBox.warning(self, "Input Error", "Please select at least one ticket type.")
            return

        try:
            self.insert_quick_ticket(next_ticket_number, ticket_data)
            quick_ticket_details = self.construct_quick_ticket_details(next_ticket_number, ticket_data)
            self.quick_ticket_created.emit({'customer_id': self.customer_id, 'quick_ticket': quick_ticket_details})
            QMessageBox.information(self, "Success", "Quick ticket created and saved successfully.")
            self.print_ticket()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"An unexpected error occurred: {e}")

    def print_ticket(self):
        QMessageBox.information(self, "Print", "Print functionality is not implemented yet.")

    def insert_quick_ticket(self, ticket_number, ticket_data):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        date_created = QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')
        cursor.execute('''
            INSERT INTO quick_tickets (
                ticket_number, customer_id, employee_id,
                ticket_type_id1, ticket_type_id2, ticket_type_id3,
                due_date1, due_date2, due_date3,
                pieces1, pieces2, pieces3,
                notes1, notes2, notes3, all_notes, date_created
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ticket_number, self.customer_id, self.employee_id,
            ticket_data[0][0], ticket_data[1][0], ticket_data[2][0],
            ticket_data[0][2], ticket_data[1][2], ticket_data[2][2],
            ticket_data[0][1], ticket_data[1][1], ticket_data[2][1],
            ticket_data[0][3], ticket_data[1][3], ticket_data[2][3],
            self.ui.atninput.toPlainText(), date_created
        ))
        conn.commit()
        conn.close()

    def create_detailed_tickets(self):
        try:
            quick_ticket_details = []
            for i in range(1, 4):
                ticket_type_id = getattr(self.ui, f'ttselection_{i}').currentData()
                if ticket_type_id:
                    if i == 1:
                        pieces = self.ui.qtpselection.value()
                        due_date = self.ui.dateTimeEdit_1.date().toString('yyyy-MM-dd') + ' ' + self.ui.dateTimeEdit_1.time().toString('HH:mm')
                        notes = self.ui.qtninput.toPlainText()
                    elif i == 2:
                        pieces = self.ui.qtpselection_2.value()
                        due_date = self.ui.dateTimeEdit_2.date().toString('yyyy-MM-dd') + ' ' + self.ui.dateTimeEdit_2.time().toString('HH:mm')
                        notes = self.ui.qtninput_2.toPlainText()
                    elif i == 3:
                        pieces = self.ui.qtpselection_3.value()
                        due_date = self.ui.dateTimeEdit_3.date().toString('yyyy-MM-dd') + ' ' + self.ui.dateTimeEdit_3.time().toString('HH:mm')
                        notes = self.ui.qtninput_3.toPlainText()

                    combined_notes = notes
                    all_notes = self.ui.atninput.toPlainText()
                    if all_notes:
                        combined_notes += f"\n{all_notes}"

                    quick_ticket_details.append({
                        'ticket_type_id': ticket_type_id,
                        'pieces': pieces,
                        'due_date': due_date,
                        'notes': combined_notes
                    })

            for index, ticket_detail in enumerate(quick_ticket_details):
                self.populate_tab(index + 1, ticket_detail['ticket_type_id'], ticket_detail['pieces'], ticket_detail['due_date'], ticket_detail['notes'])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"An error occurred while creating detailed tickets: {e}")

    def get_ticket_data(self, index):
        if index == 1:
            return (
                self.ui.ttselection.currentData(),    # Ticket Type ID for first ticket type
                self.ui.qtpselection.value(),           # Pieces for first ticket type
                self.ui.dateTimeEdit_1.dateTime().toString('yyyy-MM-dd HH:mm'),  # Due date for first ticket type
                self.ui.qtninput.toPlainText()           # Notes for first ticket type
            )
        elif index == 2:
            return (
                self.ui.ttselection_2.currentData(),    # Ticket Type ID for second ticket type
                self.ui.qtpselection_2.value(),           # Pieces for second ticket type
                self.ui.dateTimeEdit_2.dateTime().toString('yyyy-MM-dd HH:mm'),  # Due date for second ticket type
                self.ui.qtninput_2.toPlainText()          # Notes for second ticket type
            )
        elif index == 3:
            return (
                self.ui.ttselection_3.currentData(),    # Ticket Type ID for third ticket type
                self.ui.qtpselection_3.value(),           # Pieces for third ticket type
                self.ui.dateTimeEdit_3.dateTime().toString('yyyy-MM-dd HH:mm'),  # Due date for third ticket type
                self.ui.qtninput_3.toPlainText()          # Notes for third ticket type
            )
        else:
            return None

    def get_ticket_type_name(self, ticket_type_id):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM TicketTypes WHERE id = ?", (ticket_type_id,))
        ticket_type_name = cursor.fetchone()[0]
        conn.close()
        return ticket_type_name
