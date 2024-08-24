import sys
import os
from PySide6.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QListWidgetItem, QMessageBox
from views.Test import Ui_payment
import sqlite3
from controllers.config import get_db_path


class PaymentWindow(QDialog):
    def __init__(self, selected_ticket_data, total_cost, parent=None):
        super(PaymentWindow, self).__init__(parent)
        self.ui = Ui_payment()
        self.ui.setupUi(self)

        self.selected_ticket_data = selected_ticket_data
        self.total_cost = total_cost

        # Set initial values in the payment fields
        self.ui.icost.setText(f"{self.total_cost:.2f}")
        self.ui.taxes.setText("0")  # Set default taxes to 0
        self.ui.discount.setText("0")  # Set default discount to 0
        self.ui.totalcost.setText(f"${self.total_cost:.2f}")

        # Calculate initial total cost (Initial cost + taxes - discount)
        self.calculate_total_cost()

        # Populate the order list with the selected tickets
        self.populate_order_list()

        # Set up buttons
        self.ui.payb.clicked.connect(self.process_payment)
        self.ui.clearb.clicked.connect(self.clear_selection)
        self.ui.closeb.clicked.connect(self.cancel_and_close)

        # Update total cost dynamically when taxes or discount changes
        self.ui.taxes.textChanged.connect(self.calculate_total_cost)
        self.ui.discount.textChanged.connect(self.calculate_total_cost)

    def populate_order_list(self):
        """ Populate the list of orders with ticket numbers and prices. """
        model = QStandardItemModel()
        for ticket_number, ticket_cost in self.selected_ticket_data:
            item = QStandardItem(f"Ticket {ticket_number}: ${ticket_cost:.2f}")
            model.appendRow(item)
        self.ui.orderlist.setModel(model)

    def calculate_total_cost(self):
        """ Calculate the total cost based on initial cost, taxes, and discounts. """
        try:
            initial_cost = float(self.ui.icost.text())
            taxes = float(self.ui.taxes.text())
            discount = float(self.ui.discount.text())
            total_cost = initial_cost + taxes - discount
            self.ui.totalcost.setText(f"{total_cost:.2f}")
        except ValueError:
            self.ui.totalcost.setText("0.00")

    def process_payment(self):
        """ Handles the payment logic for the selected tickets. """
        payment_method = self.get_selected_payment_method()

        if not payment_method:
            QMessageBox.warning(self, "No Payment Method", "Please select a payment method.")
            return
        
        # Mark tickets as paid in the database
        self.mark_tickets_as_paid()
        
        db_path = get_db_path()

        for ticket_number, _ in self.selected_ticket_data:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE Tickets SET payment = 1 WHERE ticket_number = ?", (ticket_number,))
                conn.commit()
            except sqlite3.OperationalError as e:
                print(f"Error: {e}")
            finally:
                conn.close()
        
        # Show payment confirmation message only once, outside the loop
        QMessageBox.information(self, "Payment", f"Payment of ${self.ui.totalcost.text()} processed with {payment_method}.")
        
        # Close the payment window after processing
        self.accept()


    def get_selected_payment_method(self):
        """ Retrieves the selected payment method. """
        if self.ui.cashb.isChecked():
            return "Cash"
        elif self.ui.creditb.isChecked():
            return "Credit Card"
        elif self.ui.debitb.isChecked():
            return "Debit Card"
        elif self.ui.checkb.isChecked():
            return "Check"
        elif self.ui.otherb.isChecked():
            return "Other"
        elif self.ui.unableb.isChecked():
            return "Unable To Pay"
        return None
    
    

    def mark_tickets_as_paid(self):
        """ Update the database to mark selected tickets as paid and update the UI. """
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(project_root, 'models', 'pos_system.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            for ticket_number, _ in self.selected_ticket_data:
                # Update the payment status in the database
                cursor.execute("UPDATE Tickets SET payment = 1 WHERE ticket_number = ?", (ticket_number,))
            
            # Commit the changes to the database
            conn.commit()
        except Exception as e:
            QMessageBox.critical(self, "Payment Error", f"An error occurred while processing the payment: {e}")
        finally:
            conn.close()

        # Update the UI to reflect the payment status for each ticket
        parent = self.parent()
        if parent:
            parent.mark_tickets_as_paid_in_ui()
            for ticket_number, _ in self.selected_ticket_data:
                parent.update_ticket_status(ticket_number, "Paid")


    def clear_selection(self):
        """ Clear the selected tickets and reset the payment window. """
        self.ui.icost.clear()
        self.ui.taxes.clear()
        self.ui.discount.clear()
        self.ui.totalcost.clear()
        self.ui.orderlist.setModel(QStandardItemModel())  # Clear the list

    def cancel_and_close(self):
        """ Clear selections and close the payment window. """
        self.clear_selection()
        self.close()