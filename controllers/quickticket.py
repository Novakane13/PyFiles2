from datetime import datetime
import sqlite3
import os
import sys
from PySide6.QtWidgets import QMainWindow, QMessageBox, QWidget, QVBoxLayout, QDial, QPushButton, QDateEdit, QTimeEdit, QApplication
from PySide6.QtCore import QDateTime, Signal, QEvent, QDate, QTime
#from PySide6.QtGui import 
from views.Test import Ui_QuickTicketCreation


class QuickTicketWindow(QMainWindow):
    quick_ticket_created = Signal(dict)  # Signal to indicate quick ticket creation with details

    DATE_MODE = 0
    TIME_MODE = 1

    def __init__(self, customer_id=None, employee_id=None, ticket_id=None):
        super().__init__()
        self.ui = Ui_QuickTicketCreation()
        self.ui.setupUi(self)

        # Debug: Print initial IDs
        print(f"Initializing QuickTicketWindow with customer_id: {customer_id}, employee_id: {employee_id}, ticket_id: {ticket_id}")

        self.customer_id = customer_id
        self.employee_id = employee_id  # Store the employee ID who is creating the ticket
        self.ticket_id = ticket_id
        if self.ticket_id:
            self.load_existing_ticket_data()

        # Initial mode is DATE_MODE
        self.current_mode = QuickTicketWindow.DATE_MODE

        # Connect buttons
        self.ui.qtclosebutton.clicked.connect(self.close)
        self.ui.qtsandpbutton.clicked.connect(self.save_and_print_ticket)
        self.ui.createdetailedticket.clicked.connect(self.create_detailed_tickets)

        # Connect dials to update functions and handle double-click for mode switching
        self.ui.dial.installEventFilter(self)
        self.ui.dial_2.installEventFilter(self)
        self.ui.dial_3.installEventFilter(self)

        self.ui.dial.valueChanged.connect(self.update_due_date_or_time1)
        self.ui.dial_2.valueChanged.connect(self.update_due_date_or_time2)
        self.ui.dial_3.valueChanged.connect(self.update_due_date_or_time3)

        self.set_dial_ranges()

        self.ui.dateTimeEdit.setDate(QDate.currentDate())
        self.ui.dateTimeEdit_2.setDate(QDate.currentDate())
        self.ui.dateTimeEdit_3.setDate(QDate.currentDate())
        self.ui.dateTimeEdit.setTime(QTime.currentTime())
        self.ui.dateTimeEdit_2.setTime(QTime.currentTime())
        self.ui.dateTimeEdit_3.setTime(QTime.currentTime())

        self.populate_ticket_types()

    def set_dial_ranges(self):
        if self.current_mode == QuickTicketWindow.DATE_MODE:
            self.ui.dial.setRange(-365, 365)  # Slower speed for date adjustment (days)
            self.ui.dial_2.setRange(-365, 365)
            self.ui.dial_3.setRange(-365, 365)
        elif self.current_mode == QuickTicketWindow.TIME_MODE:
            self.ui.dial.setRange(-1440, 1440)  # Faster speed for time adjustment (minutes)
            self.ui.dial_2.setRange(-1440, 1440)
            self.ui.dial_3.setRange(-1440, 1440)

    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseButtonDblClick:
            if source in [self.ui.dial, self.ui.dial_2, self.ui.dial_3]:
                self.switch_mode()
        return super().eventFilter(source, event)

    def switch_mode(self):
        self.current_mode = QuickTicketWindow.TIME_MODE if self.current_mode == QuickTicketWindow.DATE_MODE else QuickTicketWindow.DATE_MODE
        self.set_dial_ranges()

    def update_due_date_or_time1(self, value):
        if self.current_mode == QuickTicketWindow.DATE_MODE:
            new_date = QDate.currentDate().addDays(value)
            self.ui.dateTimeEdit.setDate(new_date)
        elif self.current_mode == QuickTicketWindow.TIME_MODE:
            new_time = QTime.currentTime().addSecs(value * 60)
            self.ui.dateTimeEdit.setTime(new_time)

    def update_due_date_or_time2(self, value):
        if self.current_mode == QuickTicketWindow.DATE_MODE:
            new_date = QDate.currentDate().addDays(value)
            self.ui.dateTimeEdit_2.setDate(new_date)
        elif self.current_mode == QuickTicketWindow.TIME_MODE:
            new_time = QTime.currentTime().addSecs(value * 60)
            self.ui.dateTimeEdit_2.setTime(new_time)

    def update_due_date_or_time3(self, value):
        if self.current_mode == QuickTicketWindow.DATE_MODE:
            new_date = QDate.currentDate().addDays(value)
            self.ui.dateTimeEdit_3.setDate(new_date)
        elif self.current_mode == QuickTicketWindow.TIME_MODE:
            new_time = QTime.currentTime().addSecs(value * 60)
            self.ui.dateTimeEdit_3.setTime(new_time)

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

    def save_and_print_ticket(self):
        if self.customer_id is None or self.employee_id is None:
            QMessageBox.warning(self, "Input Error", "Customer ID or Employee ID is missing.")
            return

        ticket_type_id1 = self.ui.ttselection.currentData()
        ticket_type_id2 = self.ui.ttselection_2.currentData()
        ticket_type_id3 = self.ui.ttselection_3.currentData()

        pieces1 = self.ui.qtpselection.value()
        pieces2 = self.ui.qtpselection_2.value()
        pieces3 = self.ui.qtpselection_3.value()

        due_date1 = self.ui.dateTimeEdit.date().toString('yyyy-MM-dd') + ' ' + self.ui.dateTimeEdit.time().toString('HH:mm')
        due_date2 = self.ui.dateTimeEdit_2.date().toString('yyyy-MM-dd') + ' ' + self.ui.dateTimeEdit_2.time().toString('HH:mm')
        due_date3 = self.ui.dateTimeEdit_3.date().toString('yyyy-MM-dd') + ' ' + self.ui.dateTimeEdit_3.time().toString('HH:mm')

        notes1 = self.ui.qtninput.toPlainText()
        notes2 = self.ui.qtninput_2.toPlainText()
        notes3 = self.ui.qtninput_3.toPlainText()
        notes_all = self.ui.atninput.toPlainText()

        if not any([ticket_type_id1, ticket_type_id2, ticket_type_id3]):
            QMessageBox.warning(self, "Input Error", "Please select at least one ticket type.")
            return

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # Fetch next ticket number
            cursor.execute("SELECT MAX(ticket_number) FROM ticket_numbers")
            max_ticket_number = cursor.fetchone()[0]
            next_ticket_number = max_ticket_number + 1 if max_ticket_number else 1

            cursor.execute('INSERT INTO ticket_numbers (ticket_number) VALUES (?)', (next_ticket_number,))
            conn.commit()

            quick_ticket_details = []

            if ticket_type_id1:
                cursor.execute('''
                    INSERT INTO quick_tickets (customer_id, employee_id, ticket_number, ticket_type_id, pieces, due_date, notes, all_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (self.customer_id, self.employee_id, next_ticket_number, ticket_type_id1, pieces1, due_date1, notes1, notes_all))
                quick_ticket_details.append({
                    'ticket_number': next_ticket_number,
                    'ticket_type': self.ui.ttselection.currentText(),
                    'pieces': pieces1,
                    'due_date': due_date1,
                    'notes': notes1,
                    'all_notes': notes_all,
                    'ticket_id': cursor.lastrowid
                })
                next_ticket_number += 1

            if ticket_type_id2:
                cursor.execute('''
                    INSERT INTO quick_tickets (customer_id, employee_id, ticket_number, ticket_type_id, pieces, due_date, notes, all_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (self.customer_id, self.employee_id, next_ticket_number, ticket_type_id2, pieces2, due_date2, notes2, notes_all))
                quick_ticket_details.append({
                    'ticket_number': next_ticket_number,
                    'ticket_type': self.ui.ttselection_2.currentText(),
                    'pieces': pieces2,
                    'due_date': due_date2,
                    'notes': notes2,
                    'all_notes': notes_all,
                    'ticket_id': cursor.lastrowid
                })
                next_ticket_number += 1

            if ticket_type_id3:
                cursor.execute('''
                    INSERT INTO quick_tickets (customer_id, employee_id, ticket_number, ticket_type_id, pieces, due_date, notes, all_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (self.customer_id, self.employee_id, next_ticket_number, ticket_type_id3, pieces3, due_date3, notes3, notes_all))
                quick_ticket_details.append({
                    'ticket_number': next_ticket_number,
                    'ticket_type': self.ui.ttselection_3.currentText(),
                    'pieces': pieces3,
                    'due_date': due_date3,
                    'notes': notes3,
                    'all_notes': notes_all,
                    'ticket_id': cursor.lastrowid
                })

            conn.commit()
            self.quick_ticket_created.emit({'customer_id': self.customer_id, 'tickets': quick_ticket_details})
            self.print_ticket()
            QMessageBox.information(self, "Success", "Quick tickets created and saved successfully.")

        except sqlite3.IntegrityError as e:
            QMessageBox.warning(self, "Database Error", f"Integrity error: {e}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"An unexpected error occurred: {e}")
        finally:
            conn.close()

    def print_ticket(self):
        QMessageBox.information(self, "Print", "Print functionality is not implemented yet.")

    def create_detailed_tickets(self):
        QMessageBox.information(self, "Convert", "Convert to Detailed Tickets functionality is not implemented yet.")

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Assuming employee_id is passed from a login system
    employee_id = 1  # Use real employee_id here
    customer_id = 123  # Example customer_id, replace with actual customer data
    ticket_id = 456
    quick_ticket_window = QuickTicketWindow(customer_id=customer_id, employee_id=employee_id, ticket_id=ticket_id)
    quick_ticket_window.show()

    sys.exit(app.exec_())
