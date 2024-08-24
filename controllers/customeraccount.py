import sys
import sqlite3
import os
from PySide6.QtGui import QBrush, QColor   
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QTableWidgetItem, QMessageBox
from PySide6.QtCore import QEvent
from views.Test import Ui_CustomerAccount2
from controllers.customersearch import CustomerSearch
from controllers.quickticket import QuickTicketWindow
from controllers.detailedticket import DetailedTicketWindow
from PySide6.QtCore import Qt, QEvent, Signal
from views.Test import Ui_CustomerAccount2  # Ensure this import is correct
from controllers.payment import PaymentWindow


class CustomerAccountWindow(QMainWindow):
    convert_to_detailed_ticket = Signal(dict)

    def __init__(self, customer_data1=None, customer_data2=None, employee_id=None):
        super().__init__()
        self.ui = Ui_CustomerAccount2()
        self.ui.setupUi(self)
        
        self.customer_data1 = customer_data1 or {}
        self.customer_data2 = customer_data2 or {}
        self.customer_id1 = self.customer_data1.get("id", None)
        self.customer_id2 = self.customer_data2.get("id", None)
        
        self.employee_id = employee_id
        
        self.update_total_owed()
        
        self.selected_tickets = set()

        self.detailed_ticket_window = None

        self.load_customer_data_page1(self.customer_data1)
        self.load_customer_data_page2(self.customer_data2)
        

        self.populate_ticket_type_buttons()

        self.ui.tabWidget.setCurrentIndex(0)
        self.ui.pageswidget.setCurrentIndex(0)

        self.ui.pushButton_16.clicked.connect(self.show_page2)
        self.ui.pushButton_3.clicked.connect(self.show_page1)
        self.ui.ncbutton.clicked.connect(self.open_search_window_page1)
        self.ui.ncbutton_2.clicked.connect(self.open_search_window_page2)
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
            
        self.ui.ctlist.itemClicked.connect(lambda item: self.toggle_ticket_selection(item, 1))
        self.ui.ctlist_2.itemClicked.connect(lambda item: self.toggle_ticket_selection(item, 2))

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
        
        self.ui.paybutton.clicked.connect(self.initiate_payment)
        self.ui.puandpbutton.clicked.connect(self.process_pickup_and_payment)
        self.ui.puandpbutton_2.clicked.connect(self.process_pickup_and_payment)
        
        if self.customer_id1:
            self.load_tickets(self.customer_id1, self.ui.ctlist)
            self.update_total_owed()
        if self.customer_id2:
            self.load_tickets(self.customer_id2, self.ui.ctlist_2)
            self.update_total_owed()
            
            
    def update_ticket_status(self, ticket_number):
        # Find the ticket in ctlist (Page 1) and ctlist_2 (Page 2)
        for ctlist in [self.ui.ctlist, self.ui.ctlist_2]:
            for row in range(ctlist.rowCount()):
                if ctlist.item(row, 4).text() == ticket_number:  # Assuming ticket number is in column 4
                    # Mark payment as complete by coloring the row
                    for col in range(ctlist.columnCount()):
                        ctlist.item(row, col).setBackground(QBrush(QColor("#00002b")))  # Dark blue for paid
                    break
                
    def mark_tickets_as_paid_in_ui(self):
        """ Mark the paid tickets as unselectable and change their color to #00002b. """
        for page, ticket_number in self.selected_tickets:
            ctlist = self.ui.ctlist if page == 1 else self.ui.ctlist_2
            for row in range(ctlist.rowCount()):
                if ctlist.item(row, 4).text() == ticket_number:
                    for column in range(ctlist.columnCount()):
                        ctlist.item(row, column).setBackground(QBrush(QColor(0, 0, 43)))  # Mark as paid
        self.selected_tickets.clear()
        self.update_total_owed()

        
        
    def update_total_owed(self):
        """ Retrieve the total amount owed for all unpaid tickets directly from the database and display it on both pages. """
        total_owed_page1 = 0.0
        total_owed_page2 = 0.0

        # Connect to the database
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Retrieve total amount owed for unpaid tickets for customer 1 (Page 1)
        if self.customer_id1:
            cursor.execute("""
                SELECT SUM(total_price) 
                FROM Tickets 
                WHERE customer_id = ? AND payment = 0 AND pickedup = 0
            """, (self.customer_id1,))
            result = cursor.fetchone()
            if result and result[0] is not None:
                total_owed_page1 = result[0]

        # Retrieve total amount owed for unpaid tickets for customer 2 (Page 2)
        if self.customer_id2:
            cursor.execute("""
                SELECT SUM(total_price) 
                FROM Tickets 
                WHERE customer_id = ? AND payment = 0 AND pickedup = 0
            """, (self.customer_id2,))
            result = cursor.fetchone()
            if result and result[0] is not None:
                total_owed_page2 = result[0]

        conn.close()

        # Display the total owed in the QLabel widgets
        self.ui.totalowed.setText(f"${total_owed_page1:.2f}")
        self.ui.totalowed_2.setText(f"${total_owed_page2:.2f}")





    def process_payment(self):
        if not self.selected_tickets:
            QMessageBox.warning(self, "No Tickets Selected", "Please select at least one ticket for payment.")
            return

        # Retrieve payment method
        payment_method = self.get_selected_payment_method()
        if not payment_method:
            QMessageBox.warning(self, "No Payment Method", "Please select a payment method.")
            return

        # Mark tickets as paid
        for page, ticket_number in self.selected_tickets:
            # Update the database to mark the ticket as paid (setting the payment status to 1)
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            db_path = os.path.join(project_root, 'models', 'pos_system.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("UPDATE Tickets SET payment = 1 WHERE ticket_number = ?", (ticket_number,))
            
            conn.commit()
            conn.close()

            # Update the ctlist to reflect the payment (Page 1 or Page 2)
            ctlist = self.ui.ctlist if page == 1 else self.ui.ctlist_2
            for row in range(ctlist.rowCount()):
                if ctlist.item(row, 4).text() == ticket_number:  # Assuming column 4 has the ticket number
                    # Mark payment as complete by coloring the row
                    for col in range(ctlist.columnCount()):
                        ctlist.item(row, col).setBackground(QBrush(QColor("#00002b")))  # Dark blue for paid
                    # Set payment status to 1 (or some visual confirmation)
                    ctlist.setItem(row, 8, QTableWidgetItem('1'))  # Assuming column 8 holds payment status
                    break

       
        self.clear_selected_tickets()

        
        self.update_total_owed()

        QMessageBox.information(self, "Payment", "Payment has been processed successfully!")
        

    def process_pickup_and_payment(self):
        if not self.selected_tickets:
            QMessageBox.warning(self, "No Tickets Selected", "Please select at least one ticket for pickup and payment.")
            return

        # Retrieve payment method
        payment_method = self.get_selected_payment_method()
        if not payment_method:
            QMessageBox.warning(self, "No Payment Method", "Please select a payment method.")
            return

        # Mark tickets as paid and picked up
        for page, ticket_number in self.selected_tickets:
            # Update the database to mark the ticket as paid and picked up
            conn = sqlite3.connect('pos_system.db')  # Use your database connection
            cursor = conn.cursor()
            cursor.execute("UPDATE Tickets SET payment = 1, pickedup = 1 WHERE ticket_number = ?", (ticket_number,))
            conn.commit()
            conn.close()

            # Update the ctlist to reflect the payment and pickup (Page 1 or Page 2)
            ctlist = self.ui.ctlist if page == 1 else self.ui.ctlist_2
            for row in range(ctlist.rowCount()):
                if ctlist.item(row, 4).text() == ticket_number:  # Assuming column 4 has the ticket number
                    # Mark payment and pickup as complete
                    for col in range(ctlist.columnCount()):
                        ctlist.item(row, col).setBackground(QBrush(QColor("#00002b")))  # Dark blue for paid
                    # Set payment status to 1 (paid) and picked up status to ✓ (checkmark)
                    ctlist.setItem(row, 8, QTableWidgetItem('1'))  # Assuming column 8 holds payment status
                    ctlist.setItem(row, 0, QTableWidgetItem('✓'))  # Assuming column 0 holds pickup status
                    break

        # Clear selected tickets after pickup and payment is processed
        self.clear_selected_tickets()

        # Update total owed
        self.update_total_owed()

        QMessageBox.information(self, "Pickup and Payment", "Pickup and payment have been processed successfully!")


    def clear_selected_tickets(self):
        """ Clears selected tickets and unhighlights them. """
        for page, ticket_number in self.selected_tickets:
            ctlist = self.ui.ctlist if page == 1 else self.ui.ctlist_2
            for row in range(ctlist.rowCount()):
                if ctlist.item(row, 4).text() == ticket_number:
                    # Unhighlight ticket
                    for col in range(ctlist.columnCount()):
                        ctlist.item(row, col).setBackground(QBrush(QColor(255, 255, 255)))  # Reset to default color
                    break
        # Clear the selection
        self.selected_tickets.clear()
        
    def update_total_owed(self):
        """ Retrieve the total amount owed for all unpaid tickets directly from the database and display it on both pages. """
        total_owed_page1 = 0.0
        total_owed_page2 = 0.0

        # Connect to the database
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Retrieve total amount owed for unpaid tickets for customer 1 (Page 1)
        if self.customer_id1:
            cursor.execute("""
                SELECT SUM(total_price) 
                FROM Tickets 
                WHERE customer_id = ? AND payment = 0
            """, (self.customer_id1,))
            result = cursor.fetchone()
            if result and result[0] is not None:
                total_owed_page1 = result[0]

        # Retrieve total amount owed for unpaid tickets for customer 2 (Page 2)
        if self.customer_id2:
            cursor.execute("""
                SELECT SUM(total_price) 
                FROM Tickets 
                WHERE customer_id = ? AND payment = 0
            """, (self.customer_id2,))
            result = cursor.fetchone()
            if result and result[0] is not None:
                total_owed_page2 = result[0]

        conn.close()

        # Display the total owed in the QLineEdit widgets (which should not be editable)
        self.ui.totalowed.setText(f"${total_owed_page1:.2f}")
        self.ui.totalowed_2.setText(f"${total_owed_page2:.2f}")





    def toggle_ticket_selection(self, item, page):
        """ Toggle the selection of a ticket (highlight/unhighlight and add/remove from selected list). """
        row = item.row()
        ctlist = self.ui.ctlist if page == 1 else self.ui.ctlist_2
        ticket_number = ctlist.item(row, 4).text()  # Assuming ticket number is in column 4

        # Check if the ticket is already marked as paid
        if ctlist.item(row, 7).background().color().name() == '#00002b':
            return  # Ticket is already paid, ignore selection

        if (page, ticket_number) in self.selected_tickets:
            # Deselect ticket: remove from selected list and unhighlight
            self.selected_tickets.remove((page, ticket_number))
            for column in range(ctlist.columnCount()):
                ctlist.item(row, column).setBackground(QBrush(QColor(0, 0, 0)))  
        else:
            # Select ticket: add to selected list and highlight
            self.selected_tickets.add((page, ticket_number))
            for column in range(ctlist.columnCount()):
                ctlist.item(row, column).setBackground(QBrush(QColor(255, 0, 0)))
    
    def initiate_payment(self):
        """ Initiate payment for the selected tickets. """
        if not self.selected_tickets:
            QMessageBox.warning(self, "No Tickets Selected", "Please select at least one ticket for payment.")
            return

        # Calculate the total cost of selected tickets
        total_cost = 0
        selected_ticket_data = []

        for page, ticket_number in self.selected_tickets:
            ctlist = self.ui.ctlist if page == 1 else self.ui.ctlist_2
            for row in range(ctlist.rowCount()):
                if ctlist.item(row, 4).text() == ticket_number:  # Assuming ticket number is in column 4
                    ticket_cost = float(ctlist.item(row, 7).text().replace('$', ''))  # Assuming price is in column 7
                    total_cost += ticket_cost
                    selected_ticket_data.append((ticket_number, ticket_cost))
                    break
        
        self.update_total_owed()  # Call this after relevant events such as payment or ticket pickup

        # Open the payment window with the selected ticket data and total cost
        self.payment_window = PaymentWindow(selected_ticket_data, total_cost, self)
        self.payment_window.show()

    def update_ticket_status(self, ticket_number, status):
        """
        Update the status of a ticket in the ctlist (Page 1 or Page 2).
        This could be called after payment or pickup to update the UI.
        
        :param ticket_number: The number of the ticket to update.
        :param status: The new status of the ticket (e.g., 'Paid', 'Picked Up').
        """
        # Look for the ticket in both Page 1 and Page 2's ticket lists
        for ctlist in [self.ui.ctlist, self.ui.ctlist_2]:
            for row in range(ctlist.rowCount()):
                if ctlist.item(row, 4).text() == str(ticket_number):  # Assuming ticket number is in column 4
                    # Update the status in column 5 (or whichever column represents the status)
                    ctlist.setItem(row, 5, QTableWidgetItem(status))
                    
                    # Optionally, change the background color or provide some other visual indication
                    if status == 'Paid':
                        for col in range(ctlist.columnCount()):
                            ctlist.item(row, col).setBackground(QBrush(QColor("#00002b")))  # Dark blue for paid
                    elif status == 'Picked Up':
                        ctlist.setItem(row, 0, QTableWidgetItem('✓'))  # Add checkmark for picked up
                    break
                
                
    
    



    def cancel_selection(self):
        """ Cancel all ticket selections and reset highlights. """
        for page, ticket_number in self.selected_tickets:
            ctlist = self.ui.ctlist if page == 1 else self.ui.ctlist_2
            for row in range(ctlist.rowCount()):
                if ctlist.item(row, 4).text() == ticket_number:
                    for column in range(ctlist.columnCount()):
                        ctlist.item(row, column).setBackground(QBrush(QColor(0, 0, 0)))  # Reset to black
        self.selected_tickets.clear()
        self.update_total_owed()  # Call this after relevant events such as payment or ticket pickup


    def keyPressEvent(self, event):
        """ Handle key press events (ESC to cancel selections). """
        if event.key() == Qt.Key_Escape:
            self.cancel_selection()

    def load_tickets(self, customer_id, ctlist):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT t.ticket_number, tt.name as ticket_type, t.date_created, t.date_due, t.total_price, t.pieces, t.payment
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
            ticket_number, ticket_type, date_created, date_due, total_price, pieces, payment_status = ticket
            row_position = ctlist.rowCount()
            ctlist.insertRow(row_position)

            # Add ticket details to the table
            ctlist.setItem(row_position, 0, QTableWidgetItem(""))  
            ctlist.setItem(row_position, 1, QTableWidgetItem(ticket_type))  
            ctlist.setItem(row_position, 2, QTableWidgetItem(date_created))  
            ctlist.setItem(row_position, 3, QTableWidgetItem(date_due))  
            ctlist.setItem(row_position, 4, QTableWidgetItem(str(ticket_number))) 
            ctlist.setItem(row_position, 5, QTableWidgetItem("None"))  
            ctlist.setItem(row_position, 6, QTableWidgetItem(str(pieces))) 
            ctlist.setItem(row_position, 7, QTableWidgetItem(f"${total_price:.2f}"))

            # Check payment status and apply color accordingly
            if payment_status == 1:  # If ticket is paid
                for col in range(ctlist.columnCount()):
                    ctlist.item(row_position, col).setBackground(QBrush(QColor("#00002b")))  # Dark blue for paid

        # Load quick tickets as before
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