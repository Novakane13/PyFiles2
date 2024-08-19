import sys
import sqlite3
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QTableWidgetItem, QMessageBox
from PySide6.QtCore import QEvent
from views.Test import Ui_CustomerAccount2
from controllers.customersearch import CustomerSearch
from controllers.quickticket import QuickTicketWindow
from controllers.detailedticket import DetailedTicketWindow
from PySide6.QtCore import Qt, QEvent, Signal
from views.Test import Ui_CustomerAccount2  # Ensure this import is correct

class CustomerAccountWindow(QMainWindow):
    convert_to_detailed_ticket = Signal(dict)

    def __init__(self, customer_data1=None, customer_data2=None, employee_id=None):
        super().__init__()
        self.ui = Ui_CustomerAccount2()
        self.ui.setupUi(self)

        self.customer_data1 = customer_data1 or {}
        self.customer_data2 = customer_data2 or {}
        self.employee_id = employee_id

        self.customer_id1 = self.customer_data1.get("id", None)
        self.customer_id2 = self.customer_data2.get("id", None)

        self.detailed_ticket_window = None

        self.load_customer_data_page1(self.customer_data1)
        self.load_customer_data_page2(self.customer_data2)

        self.populate_ticket_type_buttons()

        self.ui.tabWidget.setCurrentIndex(0)
        self.ui.pageswidget.setCurrentIndex(0)

        self.ui.pushButton_16.clicked.connect(self.show_page2)
        self.ui.pushButton_3.clicked.connect(self.show_page1)
        self.ui.pushButton.clicked.connect(self.open_search_window_page1)
        self.ui.pushButton_2.clicked.connect(self.open_search_window_page2)
        self.ui.qtbutton.clicked.connect(self.open_quick_ticket_page1)
        self.ui.qtbutton_2.clicked.connect(self.open_quick_ticket_page2)

        self.ui.FirstNameInput.editingFinished.connect(lambda: self.save_customer_data(1))
        self.ui.LastNameInput.editingFinished.connect(lambda: self.save_customer_data(1))
        self.ui.PhoneNumberInput.editingFinished.connect(lambda: self.save_customer_data(1))
        self.ui.NotesInput.focusOutEvent = self.create_save_event(self.ui.NotesInput, lambda: self.save_customer_data(1))

        self.ui.FirstNameInput_2.editingFinished.connect(lambda: self.save_customer_data(2))
        self.ui.LastNameInput_2.editingFinished.connect(lambda: self.save_customer_data(2))
        self.ui.PhoneNumberInput_2.editingFinished.connect(lambda: self.save_customer_data(2))
        self.ui.NotesInput_2.focusOutEvent = self.create_save_event(self.ui.NotesInput_2, lambda: self.save_customer_data(2))

        if self.customer_id1:
            self.load_tickets(self.customer_id1, self.ui.ctlist)
        if self.customer_id2:
            self.load_tickets(self.customer_id2, self.ui.ctlist_2)

        self.ui.ctlist.itemDoubleClicked.connect(
            lambda: self.convert_selected_quick_ticket(self.ui.ctlist, self.customer_id1)
        )
        self.ui.ctlist_2.itemDoubleClicked.connect(
            lambda: self.convert_selected_quick_ticket(self.ui.ctlist_2, self.customer_id2)
        )

        self.ui.changetodetailedticket_2.clicked.connect(
            lambda: self.convert_selected_quick_ticket(self.ui.ctlist, self.customer_id1)
        )
        self.ui.changetodetailedticket.clicked.connect(
            lambda: self.convert_selected_quick_ticket(self.ui.ctlist_2, self.customer_id2)
        )

    def load_tickets(self, customer_id, ctlist):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT t.ticket_number, tt.name as ticket_type, t.date_created, t.date_due, t.total_price, t.pieces
            FROM Tickets t
            JOIN TicketTypes tt ON t.ticket_type_id = tt.id
            WHERE t.customer_id = ?
        """, (customer_id,))

        detailed_tickets = cursor.fetchall()

        cursor.execute("""
            SELECT qt.ticket_number, tt.name as ticket_type, qt.due_date1, qt.pieces1, qt.notes1, qt.all_notes,
                qt.ticket_type_id1, qt.ticket_type_id2, qt.ticket_type_id3, qt.date_created
            FROM quick_tickets qt
            JOIN TicketTypes tt ON qt.ticket_type_id1 = tt.id
            WHERE qt.customer_id = ? AND qt.converted = 0
        """, (customer_id,))
        quick_tickets = cursor.fetchall()

        conn.close()

        ctlist.setRowCount(0)

        for ticket in detailed_tickets:
            ticket_number, ticket_type, date_created, date_due, total_price, pieces = ticket
            row_position = ctlist.rowCount()
            ctlist.insertRow(row_position)

            ctlist.setItem(row_position, 0, QTableWidgetItem(""))  
            ctlist.setItem(row_position, 1, QTableWidgetItem(ticket_type))  
            ctlist.setItem(row_position, 2, QTableWidgetItem(date_created))  
            ctlist.setItem(row_position, 3, QTableWidgetItem(date_due))  
            ctlist.setItem(row_position, 4, QTableWidgetItem(str(ticket_number))) 
            ctlist.setItem(row_position, 5, QTableWidgetItem("None"))  
            ctlist.setItem(row_position, 6, QTableWidgetItem(str(pieces))) 
            ctlist.setItem(row_position, 7, QTableWidgetItem(f"${total_price:.2f}"))  
        
        for ticket in quick_tickets:
            ticket_number, ticket_type, due_date1, pieces1, notes1, all_notes, ticket_type_id1, ticket_type_id2, ticket_type_id3, date_created = ticket
            row_position = ctlist.rowCount()
            ctlist.insertRow(row_position)

            ctlist.setItem(row_position, 0, QTableWidgetItem("")) 
            ctlist.setItem(row_position, 1, QTableWidgetItem("Quick Ticket")) 
            ctlist.setItem(row_position, 2, QTableWidgetItem(date_created))  
            ctlist.setItem(row_position, 3, QTableWidgetItem(due_date1)) 
            ctlist.setItem(row_position, 4, QTableWidgetItem(str(ticket_number))) 
            ctlist.setItem(row_position, 5, QTableWidgetItem("None"))  
            ctlist.setItem(row_position, 6, QTableWidgetItem(str(pieces1))) 
            ctlist.setItem(row_position, 7, QTableWidgetItem("N/A"))  

            ctlist.item(row_position, 0).setData(Qt.UserRole, {
                'ticket_type': 'quick',
                'ticket_number': ticket_number,
                'ticket_type_id1': ticket_type_id1,
                'ticket_type_id2': ticket_type_id2,
                'ticket_type_id3': ticket_type_id3,
                'pieces1': pieces1,
                'due_date1': due_date1,
                'notes1': notes1,
                'all_notes': all_notes,
                'date_created': date_created
            })

    def populate_ticket_type_buttons(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, name FROM TicketTypes")
        ticket_types = cursor.fetchall()

        layout1 = self.ui.tickettypebuttongrid
        layout2 = self.ui.tickettypebuttongrid_2

        row1, col1 = 0, 0
        row2, col2 = 0, 0

        for ticket_type_id, ticket_type_name in ticket_types:
            # Create and add button for page 1
            button1 = QPushButton(ticket_type_name)
            button1.clicked.connect(lambda checked, tt_name=ticket_type_name, tt_id=ticket_type_id: self.open_detailed_ticket_page1(tt_name, tt_id))
            layout1.addWidget(button1, row1, col1)
            col1 += 1
            if col1 > 2:
                col1 = 0
                row1 += 1

            # Create and add button for page 2
            button2 = QPushButton(ticket_type_name)
            button2.clicked.connect(lambda checked, tt_name=ticket_type_name, tt_id=ticket_type_id: self.open_detailed_ticket_page2(tt_name, tt_id))
            layout2.addWidget(button2, row2, col2)
            col2 += 1
            if col2 > 2:
                col2 = 0
                row2 += 1

        conn.close()

    def create_save_event(self, widget, save_function):
        original_focus_out_event = widget.focusOutEvent

        def save_event(event):
            if event.type() == QEvent.FocusOut:
                save_function()
            return original_focus_out_event(event)

        return save_event

    def load_customer_data_page1(self, customer_data):
        self.ui.FirstNameInput.setText(customer_data.get("first_name", ""))
        self.ui.LastNameInput.setText(customer_data.get("last_name", ""))
        self.ui.PhoneNumberInput.setText(customer_data.get("phone_number", ""))
        self.ui.NotesInput.setPlainText(customer_data.get("notes", ""))

    def load_customer_data_page2(self, customer_data):
        self.ui.FirstNameInput_2.setText(customer_data.get("first_name", ""))
        self.ui.LastNameInput_2.setText(customer_data.get("last_name", ""))
        self.ui.PhoneNumberInput_2.setText(customer_data.get("phone_number", ""))
        self.ui.NotesInput_2.setPlainText(customer_data.get("notes", ""))

    def clear_customer_data_page1(self):
        self.ui.FirstNameInput.clear()
        self.ui.LastNameInput.clear()
        self.ui.PhoneNumberInput.clear()
        self.ui.NotesInput.clear()
        self.customer_id1 = None
        self.customer_data1 = {}
        self.ui.ctlist.setRowCount(0)

    def clear_customer_data_page2(self):
        self.ui.FirstNameInput_2.clear()
        self.ui.LastNameInput_2.clear()
        self.ui.PhoneNumberInput_2.clear()
        self.ui.NotesInput_2.clear()
        self.customer_id2 = None
        self.customer_data2 = {}
        self.ui.ctlist_2.setRowCount(0)

    def save_customer_data(self, page):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        customer_id = getattr(self, f'customer_id{page}')

        if page == 1:
            first_name = self.ui.FirstNameInput.text()
            last_name = self.ui.LastNameInput.text()
            phone_number = self.ui.PhoneNumberInput.text()
            notes = self.ui.NotesInput.toPlainText()
        elif page == 2:
            first_name = self.ui.FirstNameInput_2.text()
            last_name = self.ui.LastNameInput_2.text()
            phone_number = self.ui.PhoneNumberInput_2.text()
            notes = self.ui.NotesInput_2.toPlainText()

        if customer_id:
            cursor.execute("""
                UPDATE customers
                SET first_name = ?, last_name = ?, phone_number = ?, notes = ?
                WHERE id = ?
            """, (
                first_name,
                last_name,
                phone_number,
                notes,
                customer_id
            ))
        else:
            cursor.execute("""
                INSERT INTO customers (first_name, last_name, phone_number, notes)
                VALUES (?, ?, ?, ?)
            """, (
                first_name,
                last_name,
                phone_number,
                notes
            ))
            setattr(self, f'customer_id{page}', cursor.lastrowid)

        conn.commit()
        conn.close()

    def show_page1(self):
        self.ui.pageswidget.setCurrentIndex(0)

    def show_page2(self):
        self.ui.pageswidget.setCurrentIndex(1)

    def open_search_window_page1(self):
        self.search_window = CustomerSearch(target_page=1)
        self.search_window.customer_selected.connect(self.load_customer_data_page1)
        self.search_window.show()

    def open_search_window_page2(self):
        self.search_window = CustomerSearch(target_page=2)
        self.search_window.customer_selected.connect(self.load_customer_data_page2)
        self.search_window.show()

    def open_quick_ticket_page1(self):
        self.quick_ticket_window = QuickTicketWindow(customer_id=self.customer_id1, employee_id=self.employee_id)
        self.quick_ticket_window.quick_ticket_created.connect(self.load_tickets_after_creation)
        self.quick_ticket_window.show()

    def open_quick_ticket_page2(self):
        self.quick_ticket_window = QuickTicketWindow(customer_id=self.customer_id2, employee_id=self.employee_id)
        self.quick_ticket_window.quick_ticket_created.connect(self.load_tickets_after_creation)
        self.quick_ticket_window.show()

    def open_detailed_ticket_page1(self, tt_name=None, ticket_type_id1=None, pieces1=1, due_date1=None, notes1=None, all_notes=None):
        self.detailed_ticket_window = DetailedTicketWindow(
            customer_id=self.customer_id1,
            ticket_type_id1=ticket_type_id1,
            tt_name=tt_name,
            pieces1=pieces1,
            due_date1=due_date1,
            notes1=notes1,
            all_notes=all_notes,
            employee_id=self.employee_id
        )
        self.detailed_ticket_window.ticket_completed.connect(self.on_ticket_completed)
        self.detailed_ticket_window.show()

    def open_detailed_ticket_page2(self, tt_name=None, ticket_type_id1=None, pieces1=1, due_date1=None, notes1=None, all_notes=None):
        self.detailed_ticket_window = DetailedTicketWindow(
            customer_id=self.customer_id2,
            ticket_type_id1=ticket_type_id1,
            tt_name=tt_name,
            pieces1=pieces1,
            due_date1=due_date1,
            notes1=notes1,
            all_notes=all_notes,
            employee_id=self.employee_id
        )
        self.detailed_ticket_window.ticket_completed.connect(self.on_ticket_completed)
        self.detailed_ticket_window.show()

    def load_tickets_after_creation(self, data):
        customer_id = data.get('customer_id')
        if customer_id == self.customer_id1:
            self.load_tickets(self.customer_id1, self.ui.ctlist)
        elif customer_id == self.customer_id2:
            self.load_tickets(self.customer_id2, self.ui.ctlist_2)

    def get_ticket_type_name(self, ticket_type_id):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT name FROM TicketTypes WHERE id = ?", (ticket_type_id,))
            result = cursor.fetchone()

            if result:
                return result[0]
            else:
                return None
        except Exception as e:
            print(f"Error retrieving ticket type name: {e}")
            return None
        finally:
            conn.close()

    def convert_selected_quick_ticket(self, ctlist, customer_id):
        selected_row = ctlist.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a quick ticket to convert.")
            return

        ticket_data = ctlist.item(selected_row, 0).data(Qt.UserRole)

        if not ticket_data:
            QMessageBox.warning(self, "Invalid Selection", "The selected item is not a valid quick ticket.")
            return
        
        quick_ticket_number = ticket_data.get('ticket_number')

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    UPDATE quick_tickets 
                    SET converted = 1
                    WHERE ticket_number = ?
                """, (quick_ticket_number,))
                conn.commit()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"An error occurred while marking the quick ticket as converted: {e}")
                return

        self.open_detailed_ticket_from_quick_ticket(ticket_data, customer_id)

    def open_detailed_ticket_from_quick_ticket(self, ticket_data, customer_id):
        try:
            self.detailed_ticket_window = DetailedTicketWindow(
                customer_id=customer_id,
                employee_id=self.employee_id,
                tt_name=self.get_ticket_type_name(ticket_data.get('ticket_type_id1')),
                ticket_type_id1=ticket_data.get('ticket_type_id1'),
                tt_name2=self.get_ticket_type_name(ticket_data.get('ticket_type_id2')),
                ticket_type_id2=ticket_data.get('ticket_type_id2'),
                tt_name3=self.get_ticket_type_name(ticket_data.get('ticket_type_id3')),
                ticket_type_id3=ticket_data.get('ticket_type_id3'),
                pieces1=ticket_data.get('pieces1', 1),
                pieces2=ticket_data.get('pieces2'),
                pieces3=ticket_data.get('pieces3'),
                due_date1=ticket_data.get('due_date1'),
                due_date2=ticket_data.get('due_date2'),
                due_date3=ticket_data.get('due_date3'),
                notes1=ticket_data.get('notes1'),
                notes2=ticket_data.get('notes2'),
                notes3=ticket_data.get('notes3'),
                all_notes=ticket_data.get('all_notes')
            )
            self.detailed_ticket_window.ticket_completed.connect(self.on_ticket_completed)
            self.detailed_ticket_window.show()

        except KeyError as e:
            print(f"KeyError: {e}")
            QMessageBox.warning(self, "Data Error", f"Missing key in ticket data: {e}")

    def get_ticket_type_id(self, ticket_type_name):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM TicketTypes WHERE name = ?", (ticket_type_name,))
        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def on_ticket_completed(self, customer_id):
        if customer_id == self.customer_id1:
            self.load_tickets(self.customer_id1, self.ui.ctlist)
        elif customer_id == self.customer_id2:
            self.load_tickets(self.customer_id2, self.ui.ctlist_2)