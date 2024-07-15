import sqlite3
import os
from PySide6.QtWidgets import QMainWindow, QMessageBox
from PySide6.QtCore import QDateTime
from views.Test import Ui_QuickTicketCreation

class QuickTicketWindow(QMainWindow):
    def __init__(self, customer_id=None):
        super().__init__()
        self.ui = Ui_QuickTicketCreation()
        self.ui.setupUi(self)
        self.customer_id = customer_id
        self.ui.qtclosebutton.clicked.connect(self.close)
        self.ui.qtsandpbutton.clicked.connect(self.save_and_print_ticket)
        self.populate_ticket_types()

    def populate_ticket_types(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT ticket_type_name FROM ticket_types")
        ticket_types = cursor.fetchall()
        conn.close()

        for ticket_type in ticket_types:
            self.ui.ttselection.addItem(ticket_type[0])
            self.ui.ttselection_2.addItem(ticket_type[0])
            self.ui.ttselection_3.addItem(ticket_type[0])

    def save_and_print_ticket(self):
        ticket_type1 = self.ui.ttselection.currentText()
        ticket_type2 = self.ui.ttselection_2.currentText()
        ticket_type3 = self.ui.ttselection_3.currentText()

        pieces1 = self.ui.qtpselection.value()
        pieces2 = self.ui.qtpselection_2.value()
        pieces3 = self.ui.qtpselection_3.value()

        due_date1 = self.ui.qtdselection.date().toString('yyyy-MM-dd')
        due_date2 = self.ui.qtdselection_2.date().toString('yyyy-MM-dd')
        due_date3 = self.ui.qtdselection_3.date().toString('yyyy-MM-dd')

        notes1 = self.ui.qtninput.toPlainText()
        notes2 = self.ui.qtninput_2.toPlainText()
        notes3 = self.ui.qtninput_3.toPlainText()
        notes_all = self.ui.atninput.toPlainText()

        if not ticket_type1 and not ticket_type2 and not ticket_type3:
            QMessageBox.warning(self, "Input Error", "Please select at least one ticket type.")
            return

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Fetch next ticket number
        cursor.execute("SELECT MAX(ticket_number) FROM ticket_numbers")
        max_ticket_number = cursor.fetchone()[0]
        next_ticket_number = max_ticket_number + 1 if max_ticket_number else 1
        
        cursor.execute('INSERT INTO ticket_numbers (ticket_number) VALUES (?)', (next_ticket_number,))
        conn.commit()
        
        if ticket_type1:
            cursor.execute('''
                INSERT INTO quick_tickets (customer_id, ticket_id, ticket_type, pieces, due_date, notes, all_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (self.customer_id, next_ticket_number, ticket_type1, pieces1, due_date1, notes1, notes_all))
            next_ticket_number += 1
            cursor.execute("INSERT INTO ticket_numbers (ticket_number) VALUES (?)", (next_ticket_number,))
        
        if ticket_type2:
            cursor.execute('''
                INSERT INTO quick_tickets (customer_id, ticket_id, ticket_type, pieces, due_date, notes, all_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (self.customer_id, next_ticket_number, ticket_type2, pieces2, due_date2, notes2, notes_all))
            next_ticket_number += 1
            cursor.execute("INSERT INTO ticket_numbers (ticket_number) VALUES (?)", (next_ticket_number,))
        
        if ticket_type3:
            cursor.execute('''
                INSERT INTO quick_tickets (customer_id, ticket_id, ticket_type, pieces, due_date, notes, all_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (self.customer_id, next_ticket_number, ticket_type3, pieces3, due_date3, notes3, notes_all))
            cursor.execute("INSERT INTO ticket_numbers (ticket_number) VALUES (?)", (next_ticket_number,))
            
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Success", "Quick ticket created and saved successfully.")
        
        # Placeholder for print functionality
        self.print_ticket()

    def print_ticket(self):
        # Placeholder for print functionality
        QMessageBox.information(self, "Print", "Print functionality is not implemented yet.")
