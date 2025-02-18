import sqlite3
from PySide6.QtWidgets import QDialog, QMessageBox
from views.utils import get_db_path
from views.cashpaymentui import Ui_cashpayment

class CashPaymentWindow(QDialog):
    def __init__(self, selected_ticket_data, total_cost, parent=None):
        super(CashPaymentWindow, self).__init__(parent)
        self.ui = Ui_cashpayment()
        self.ui.setupUi(self)

        self.selected_ticket_data = selected_ticket_data
        self.total_cost = total_cost

        # Set initial values
        self.ui.totalcost.setText(f"${self.total_cost:.2f}")
        self.ui.cashreceived.textChanged.connect(self.calculate_change)
        self.ui.payb.clicked.connect(self.process_cash_payment)
        self.ui.cancelb.clicked.connect(self.reject)

    def calculate_change(self):
        """Calculate the change due based on cash received."""
        try:
            cash_received = float(self.ui.cashreceived.text())
            change_due = cash_received - self.total_cost
            self.ui.change.setText(f"${max(change_due, 0):.2f}")
        except ValueError:
            self.ui.change.setText("$0.00")

    def process_cash_payment(self):
        """Processes cash payment and updates the database."""
        try:
            cash_received = float(self.ui.cashreceived.text())
            if cash_received < self.total_cost:
                QMessageBox.warning(self, "Insufficient Payment", "Cash received is less than total cost.")
                return

            db_path = get_db_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            customer_id = self.get_current_customer_id()
            
            for ticket_number, _ in self.selected_ticket_data:
                cursor.execute("""
                    INSERT INTO Payments (customer_id, ticket_id, payment_method, amount, stripe_charge_id)
                    VALUES (?, ?, ?, ?, NULL)
                """, (customer_id, ticket_number, "Cash", self.total_cost))
                
                cursor.execute("UPDATE Tickets SET payment = 1 WHERE ticket_number = ?", (ticket_number,))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Payment Success", "Cash payment recorded successfully.")
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid cash amount.")
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to record payment: {e}")
