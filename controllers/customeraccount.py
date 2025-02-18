import sqlite3
import os
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import QMainWindow, QPushButton, QTableWidgetItem, QMessageBox, QHeaderView
from PySide6.QtCore import QEvent, Qt, Signal
from views.customeraccountui import Ui_CustomerAccount2
from controllers.customersearch import CustomerSearch
from controllers.quickticket import QuickTicketWindow
from controllers.detailedticket import DetailedTicketWindow
from controllers.payment import PaymentWindow
from controllers.moreinfo import MoreInfoDialog
from controllers.config import get_db_path
from views.utils import get_db_connection


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

        self.ui.more_info_button_2.clicked.connect(self.open_more_info_dialog)
        self.ui.more_info_button.clicked.connect(self.open_more_info_dialog)

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
        
        self.ui.paybutton.clicked.connect(lambda: self.initiate_payment(mark_as_picked_up=False))  
        self.ui.puandpbutton.clicked.connect(lambda: self.initiate_payment(mark_as_picked_up=True))
        self.ui.paybutton_2.clicked.connect(lambda: self.initiate_payment(mark_as_picked_up=False))
        self.ui.puandpbutton_2.clicked.connect(lambda: self.initiate_payment(mark_as_picked_up=True))
        
        if self.customer_id1:
            self.load_tickets(self.customer_id1, self.ui.ctlist)
            self.update_total_owed()
        if self.customer_id2:
            self.load_tickets(self.customer_id2, self.ui.ctlist_2)
            self.update_total_owed()
            
    def get_current_customer_id(self):
        """Returns the active customer's ID based on the current page."""
        current_page = self.ui.pageswidget.currentIndex()
        return self.customer_id1 if current_page == 0 else self.customer_id2
            
    def mark_tickets_as_picked_up(self, customer_id, selected_ticket_data):
        """Marks selected tickets as picked up in the database and refreshes the UI immediately."""
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            for ticket_number, _ in selected_ticket_data:
                cursor.execute("UPDATE Tickets SET pickedup = 1 WHERE ticket_number = ?", (ticket_number,))
            conn.commit()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to update tickets as picked up: {e}")
        finally:
            conn.close()

        # ✅ Refresh the UI immediately after marking as picked up
        self.refresh_customer_account(customer_id)

    def refresh_customer_account(self, customer_id):
        """Reloads the correct customer's ticket list immediately after payment or pickup."""
        if customer_id == self.customer_id1:
            self.load_customer_tickets(self.customer_id1, None, self.ui.ctlist, None)  # Update Page 1 Only
        elif customer_id == self.customer_id2:
            self.load_customer_tickets(None, self.customer_id2, None, self.ui.ctlist_2)  # Update Page 2 Only

        self.update_total_owed()  # Ensure the total owed updates immediately



    def mark_tickets_as_paid_in_ui(self):
        """ Update UI after payment. """
        for page, ticket_number in self.selected_tickets:
            ctlist = self.ui.ctlist if page == 1 else self.ui.ctlist_2
            for row in range(ctlist.rowCount()):
                if ctlist.item(row, 4).text() == ticket_number:
                    # Fetch payment status from database
                    db_path = get_db_path()
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT payment, pickedup FROM Tickets WHERE ticket_number = ?", (ticket_number,))
                    payment, pickedup = cursor.fetchone()
                    conn.close()

                    # Update Picked/Paid Column
                    status_text = ""
                    if payment:
                        status_text += "✓"  # Paid
                    if pickedup:
                        status_text += " ◯" if status_text else "◯"  # Picked Up

                    ctlist.setItem(row, 0, QTableWidgetItem(status_text.strip()))


    def mark_ticket_as_picked_up(self):
        """ Mark selected ticket as picked up without changing payment status. """
        if not self.selected_tickets:
            QMessageBox.warning(self, "No Tickets Selected", "Select at least one ticket to mark as picked up.")
            return

        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        for page, ticket_number in self.selected_tickets:
            cursor.execute("UPDATE Tickets SET pickedup = 1 WHERE ticket_number = ?", (ticket_number,))

            # Update UI
            ctlist = self.ui.ctlist if page == 1 else self.ui.ctlist_2
            for row in range(ctlist.rowCount()):
                if ctlist.item(row, 4).text() == ticket_number:
                    # Fetch updated payment status
                    cursor.execute("SELECT payment FROM Tickets WHERE ticket_number = ?", (ticket_number,))
                    payment = cursor.fetchone()[0]

                    # Update Picked/Paid column
                    status_text = "✓" if payment else ""
                    status_text += " ◯" if status_text else "◯"  # Add the circle for picked up status

                    ctlist.setItem(row, 0, QTableWidgetItem(status_text.strip()))

        conn.commit()
        conn.close()

            
        
    def update_total_owed(self):
        """Update the total amount owed and refresh ticket lists immediately."""
        total_owed_page1 = 0.0
        total_owed_page2 = 0.0

        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if self.customer_id1:
            cursor.execute("""
                SELECT SUM(total_price) 
                FROM Tickets 
                WHERE customer_id = ? AND payment = 0 
            """, (self.customer_id1,))
            result = cursor.fetchone()
            total_owed_page1 = result[0] if result[0] is not None else 0.0

        if self.customer_id2:
            cursor.execute("""
                SELECT SUM(total_price) 
                FROM Tickets 
                WHERE customer_id = ? AND payment = 0 
            """, (self.customer_id2,))
            result = cursor.fetchone()
            total_owed_page2 = result[0] if result[0] is not None else 0.0

        conn.close()

        # ✅ Update the total owed immediately
        self.ui.totalowed.setText(f"${total_owed_page1:.2f}")
        self.ui.totalowed_2.setText(f"${total_owed_page2:.2f}")

        # ✅ Refresh tickets immediately
        if self.customer_id1:
            self.load_tickets(self.customer_id1, self.ui.ctlist)
        if self.customer_id2:
            self.load_tickets(self.customer_id2, self.ui.ctlist_2)


    def get_customer_full_name(self, customer_id):
        """Retrieve the full name of the customer from the database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT first_name, last_name FROM customers WHERE id = ?", (customer_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return f"{result[0]} {result[1]}"  # Combine first and last name
        return "Unknown Customer"


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
        """Process payment and mark selected tickets as paid & picked up."""
        if not self.selected_tickets:
            QMessageBox.warning(self, "No Tickets Selected", "Please select at least one ticket for payment and pickup.")
            return

        total_cost = 0
        selected_ticket_data = []

        for page, ticket_number in self.selected_tickets:
            ctlist = self.ui.ctlist if page == 1 else self.ui.ctlist_2
            for row in range(ctlist.rowCount()):
                if ctlist.item(row, 4).text() == ticket_number:
                    ticket_cost = float(ctlist.item(row, 7).text().replace('$', ''))
                    total_cost += ticket_cost
                    selected_ticket_data.append((ticket_number, ticket_cost))
                    break

        self.update_total_owed()

        # Open Payment Window with pickup flag
        self.payment_window = PaymentWindow(selected_ticket_data, total_cost, mark_as_picked_up=True, parent=self)
        self.payment_window.exec_()



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
        

    def toggle_ticket_selection(self, item, page):
        """ Toggle the selection of a ticket (highlight/unhighlight and add/remove from selected list). """
        row = item.row()
        ctlist = self.ui.ctlist if page == 1 else self.ui.ctlist_2
        ticket_number = ctlist.item(row, 4).text()  # Assuming ticket number is in column 4

        if (page, ticket_number) in self.selected_tickets:
            # Deselect ticket: remove from selected list and unhighlight
            self.selected_tickets.remove((page, ticket_number))
            for column in range(ctlist.columnCount()):
                ctlist.item(row, column).setBackground(QBrush(QColor(0, 0, 0)))  # Reset to black
        else:
            # Select ticket: add to selected list and highlight
            self.selected_tickets.add((page, ticket_number))
            for column in range(ctlist.columnCount()):
                ctlist.item(row, column).setBackground(QBrush(QColor(255, 0, 0)))  # Highlight in red
        
    def initiate_payment(self, mark_as_picked_up=False):
        """Initiate payment for selected tickets, handling both 'Pay' and 'Pick Up & Pay' buttons."""

        if not self.selected_tickets:
            QMessageBox.warning(self, "No Tickets Selected", "Please select at least one ticket for payment.")
            return

        total_cost = 0
        selected_ticket_data = []

        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        
        for page, ticket_number in self.selected_tickets:
            ctlist = self.ui.ctlist if page == 1 else self.ui.ctlist_2
            for row in range(ctlist.rowCount()):
                if ctlist.item(row, 4).text() == ticket_number:  # Column 4 contains ticket number
                    cursor.execute("SELECT payment FROM Tickets WHERE ticket_number = ?", (ticket_number,))
                    is_paid = cursor.fetchone()[0]

                    if is_paid:
                        QMessageBox.warning(self, "Already Paid", f"Ticket {ticket_number} has already been paid.")
                        continue  # Skip already paid tickets

                    ticket_cost = float(ctlist.item(row, 7).text().replace('$', ''))  # Column 7 contains total cost
                    total_cost += ticket_cost
                    selected_ticket_data.append((ticket_number, ticket_cost))
                    break

        conn.close()

        if not selected_ticket_data:
            QMessageBox.warning(self, "No Valid Tickets", "All selected tickets are already paid.")
            return

        # ✅ Open Payment Window
        self.payment_window = PaymentWindow(selected_ticket_data, total_cost, mark_as_picked_up, parent=self)
        self.payment_window.exec_()



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

    def is_valid_quick_ticket(self, ticket_type, converted):
        return ticket_type == "Quick Ticket" and not converted

    def load_tickets(self, customer_id, ctlist):
        if not customer_id:
            return

        def create_item(text):
            item = QTableWidgetItem(text)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            return item

        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ticket_number, ticket_type_id, date_created, date_due, total_price, pieces, payment, pickedup
            FROM Tickets
            WHERE customer_id = ?
        """, (customer_id,))
        detailed_tickets = cursor.fetchall()

        cursor.execute("""
            SELECT ticket_number, ticket_type_id1, date_created, due_date1, pieces1, pieces2, pieces3, converted
            FROM quick_tickets
            WHERE customer_id = ? AND converted = 0
        """, (customer_id,))
        quick_tickets = cursor.fetchall()

        conn.close()

        ctlist.setRowCount(0)

        for ticket in detailed_tickets:
            ticket_number, ticket_type_id, date_created, date_due, total_price, pieces, payment, pickedup = ticket
            row_position = ctlist.rowCount()
            ctlist.insertRow(row_position)

            status_text = ""
            if payment:
                status_text += "✓"
            if pickedup:
                status_text += " ◯" if status_text else "◯"

            ctlist.setItem(row_position, 0, create_item(status_text.strip()))
            ctlist.setItem(row_position, 1, create_item(self.get_ticket_type_name(ticket_type_id) if ticket_type_id else "Unknown"))
            ctlist.setItem(row_position, 2, create_item(date_created))
            ctlist.setItem(row_position, 3, create_item(date_due))
            ctlist.setItem(row_position, 4, create_item(str(ticket_number)))
            ctlist.setItem(row_position, 5, create_item("N/A"))
            ctlist.setItem(row_position, 6, create_item(str(pieces)))
            ctlist.setItem(row_position, 7, create_item(f"${total_price:.2f}"))

            if payment:
                for col in range(ctlist.columnCount()):
                    ctlist.item(row_position, col).setBackground(QBrush(QColor("#00002b")))

        for ticket in quick_tickets:
            ticket_number, ticket_type_id, date_created, due_date, pieces1, pieces2, pieces3, converted = ticket
            estimated_pieces = sum(filter(None, [pieces1, pieces2, pieces3]))
            row_position = ctlist.rowCount()
            ctlist.insertRow(row_position)

            # Create a QTableWidgetItem for the first column and attach ticket data to it.
            item = create_item("")
            # Create a dictionary of the ticket data so you can reference it later.
            ticket_data = {
                "ticket_number": ticket_number,
                "ticket_type_id1": ticket_type_id,
                "date_created": date_created,
                "due_date1": due_date,
                "pieces1": pieces1,
                "pieces2": pieces2,
                "pieces3": pieces3,
                "converted": converted,
            }
            item.setData(Qt.UserRole, ticket_data)
            ctlist.setItem(row_position, 0, item)

            ctlist.setItem(row_position, 1, create_item("Quick Ticket"))
            ctlist.setItem(row_position, 2, create_item(date_created))
            ctlist.setItem(row_position, 3, create_item(due_date))
            ctlist.setItem(row_position, 4, create_item(str(ticket_number)))
            ctlist.setItem(row_position, 5, create_item("N/A"))
            ctlist.setItem(row_position, 6, create_item(str(estimated_pieces)))
            ctlist.setItem(row_position, 7, create_item(""))

            # If the ticket has been converted, shade the row.
            if converted:
                for col in range(ctlist.columnCount()):
                    ctlist.item(row_position, col).setBackground(QBrush(QColor("#CCCCCC")))

            header = ctlist.horizontalHeader()
            for col in range(ctlist.columnCount()):
                header.setSectionResizeMode(col, QHeaderView.Stretch)

            ctlist.resizeRowsToContents()

        
    def load_customer_tickets(self, customer_id1=None, customer_id2=None, ctlist1=None, ctlist2=None):
        """Loads tickets for the correct customer into the correct list UI."""
        if customer_id1 and ctlist1:
            self.load_tickets(customer_id1, ctlist1)
        elif ctlist1:
            ctlist1.setRowCount(0)  # Clear if no valid customer_id1

        if customer_id2 and ctlist2:
            self.load_tickets(customer_id2, ctlist2)
        elif ctlist2:
            ctlist2.setRowCount(0)  # Clear if no valid customer_id2

        # Force UI update to reflect changes immediately
        if ctlist1:
            ctlist1.viewport().update()
        if ctlist2:
            ctlist2.viewport().update()


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
        # Update internal data and customer id for page 1
        self.customer_data1 = customer_data
        self.customer_id1 = customer_data.get("id", None)

        # Update UI fields
        self.ui.FirstNameInput.setText(customer_data.get("first_name", ""))
        self.ui.LastNameInput.setText(customer_data.get("last_name", ""))
        self.ui.PhoneNumberInput.setText(customer_data.get("phone_number", ""))
        self.ui.NotesInput.setPlainText(customer_data.get("notes", ""))

        # Reload tickets and update total owed if we have a valid customer id
        if self.customer_id1:
            self.load_tickets(self.customer_id1, self.ui.ctlist)
            self.update_total_owed()

    def load_customer_data_page2(self, customer_data):
        # Update internal data and customer id for page 2
        self.customer_data2 = customer_data
        self.customer_id2 = customer_data.get("id", None)

        # Update UI fields
        self.ui.FirstNameInput_2.setText(customer_data.get("first_name", ""))
        self.ui.LastNameInput_2.setText(customer_data.get("last_name", ""))
        self.ui.PhoneNumberInput_2.setText(customer_data.get("phone_number", ""))
        self.ui.NotesInput_2.setPlainText(customer_data.get("notes", ""))

        # Reload tickets and update total owed if we have a valid customer id
        if self.customer_id2:
            self.load_tickets(self.customer_id2, self.ui.ctlist_2)
            self.update_total_owed()


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

        # Use your helper to check that it's a quick ticket and hasn't been converted
        if not self.is_valid_quick_ticket("Quick Ticket", ticket_data.get("converted", 0)):
            QMessageBox.warning(self, "Invalid Ticket", "The selected ticket is either not a quick ticket or has already been converted.")
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

    def open_more_info_dialog(self):
        customer_id = self.get_current_customer_id()  
        if customer_id is None:
            QMessageBox.warning(self, "Error", "No customer selected.")
            return
        dialog = MoreInfoDialog(customer_id)  
        dialog.exec()

