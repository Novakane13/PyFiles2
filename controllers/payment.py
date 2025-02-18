import sqlite3
import stripe
import webbrowser
from PySide6.QtWidgets import QDialog, QMessageBox
from views.utils import get_db_path, get_stripe_customer_id_and_email,\
    get_db_connection, create_stripe_customer
from views.paymentui import Ui_payment

stripe.api_key = "YOUR_STRIPE_SECRET_KEY"  

class PaymentWindow(QDialog):
    def __init__(self, selected_ticket_data, total_cost, mark_as_picked_up=False, parent=None):
        super(PaymentWindow, self).__init__(parent)
        self.ui = Ui_payment()
        self.ui.setupUi(self)

        self.selected_ticket_data = selected_ticket_data
        self.total_cost = total_cost
        self.mark_as_picked_up = mark_as_picked_up

        # Set default values
        self.ui.initial_cost_display.setText(f"{self.total_cost:.2f}")
        self.ui.taxes_display.setText("0")
        self.ui.total_cost_display.setText(f"${self.total_cost:.2f}")

        # Populate placeholder coupon list
        self.populate_coupon_list()

        # Connect UI elements
        self.ui.closeb.clicked.connect(self.cancel_and_close)  # Close window
        self.ui.clearb.clicked.connect(self.clear_fields)      # Clear input fields
        self.ui.payb.clicked.connect(self.process_payment)     # Process payment

        # Cash payment handling
        self.ui.cash_received_input.textChanged.connect(self.calculate_change)
        self.ui.cashb.clicked.connect(self.toggle_cash_fields)

        # Tax and Coupon updates
        self.ui.taxes_display.textChanged.connect(self.calculate_total_cost)
        self.ui.coupons.currentIndexChanged.connect(self.calculate_total_cost)  # Placeholder handling

    def populate_coupon_list(self):
        """ Populate placeholder coupons for now. """
        self.ui.coupons.clear()
        self.ui.coupons.addItem("No Coupon", 0)
        self.ui.coupons.addItem("$5 Off", 5)
        self.ui.coupons.addItem("$10 Off", 10)

    def calculate_total_cost(self):
        """ Calculate the final cost including taxes and coupon discounts. """
        try:
            initial_cost = float(self.ui.initial_cost_display.text())
            taxes = float(self.ui.taxes_display.text())
            coupon_value = self.ui.coupons.currentData()  # Gets value from dropdown

            total_cost = initial_cost + taxes - coupon_value
            self.ui.total_cost_display.setText(f"${max(total_cost, 0):.2f}")  # Ensure no negative total
        except ValueError:
            self.ui.total_cost_display.setText("$0.00")

    def calculate_change(self):
        """ Calculate and display change when cash is received. """
        try:
            total_cost = float(self.ui.total_cost_display.text().replace('$', ''))
            cash_received = float(self.ui.cash_received_input.text()) if self.ui.cash_received_input.text() else 0.0

            change_due = max(cash_received - total_cost, 0)  # Prevent negative change
            self.ui.customer_change_display.setText(f"${change_due:.2f}")
        except ValueError:
            self.ui.customer_change_display.setText("$0.00")  # Reset on invalid input

    def toggle_cash_fields(self):
        """ Enable/disable cash input fields based on payment method selection. """
        if self.ui.cashb.isChecked():
            self.ui.cash_received_input.setEnabled(True)
            self.ui.customer_change_display.setEnabled(True)
        else:
            self.ui.cash_received_input.setEnabled(False)
            self.ui.cash_received_input.setText("")
            self.ui.customer_change_display.setEnabled(False)
            self.ui.customer_change_display.setText("$0.00")

    def process_payment(self):
        """Process the payment and update the database & UI."""
        payment_method = self.get_selected_payment_method()
        if not payment_method:
            QMessageBox.warning(self, "No Payment Method", "Please select a payment method.")
            return

        total_cost = float(self.ui.total_cost_display.text().replace('$', ''))
        customer_id = self.parent().get_current_customer_id()

        if payment_method == "Cash":
            cash_received = float(self.ui.cash_received_input.text()) if self.ui.cash_received_input.text() else 0.0
            if cash_received < total_cost:
                QMessageBox.warning(self, "Insufficient Payment", "Cash received is less than total cost.")
                return
            change_due = cash_received - total_cost
            self.record_payment_in_db(customer_id, "Cash", total_cost)
            QMessageBox.information(self, "Payment Successful", f"Cash payment recorded.\nChange Due: ${change_due:.2f}")

        elif payment_method in ["Check", "Other"]:
            self.record_payment_in_db(customer_id, payment_method, total_cost)

        elif payment_method == "Unable To Pay":
            self.parent().mark_tickets_as_picked_up(customer_id)

        else:
            self.process_card_payment(customer_id, total_cost)

        if self.mark_as_picked_up:
            self.parent().mark_tickets_as_picked_up(customer_id, self.selected_ticket_data)

        
        self.parent().update_total_owed() 
        self.parent().load_tickets(customer_id, self.parent().ui.ctlist) 
        self.parent().refresh_customer_account(customer_id)

        self.accept() 


    def process_card_payment(self, customer_id, total_cost):
        """Processes credit card payments via Stripe and auto-creates a customer if needed."""
        stripe_customer_id, customer_email = get_stripe_customer_id_and_email(customer_id)

        # ✅ If no Stripe customer ID exists, create one automatically
        if not stripe_customer_id:
            QMessageBox.information(self, "Creating Stripe Account", "Creating a Stripe account for this customer...")
            customer_name = self.parent().get_customer_full_name(customer_id)  # Fetch full name

            # 🚨 Ensure the email is valid before creating a Stripe customer
            if not customer_email:
                QMessageBox.critical(self, "Stripe Error", "Customer does not have a valid email address. Cannot create Stripe account.")
                return

            stripe_customer_id = create_stripe_customer(customer_name, customer_email)

            if not stripe_customer_id:
                QMessageBox.critical(self, "Stripe Error", "Failed to create a Stripe customer account.")
                return

            # ✅ Update the database with the new Stripe ID
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE customers SET stripe_customer_id = ? WHERE id = ?", (stripe_customer_id, customer_id))
            conn.commit()
            conn.close()

        # ✅ Fetch saved payment methods for the customer
        try:
            payment_methods = stripe.PaymentMethod.list(customer=stripe_customer_id, type="card")["data"]

            if not payment_methods:
                QMessageBox.warning(self, "No Saved Card", "Customer has no saved cards on Stripe. Redirecting to add a card...")
                self.open_add_card_window(stripe_customer_id)  # Open Stripe card entry page
                return
            
            default_payment_method = payment_methods[0]["id"]
        except stripe.error.StripeError as e:
            QMessageBox.critical(self, "Stripe Error", f"Error fetching payment methods: {e.user_message}")
            return

        # ✅ Charge the customer
        try:
            charge = stripe.PaymentIntent.create(
                amount=int(total_cost * 100),
                currency="usd",
                customer=stripe_customer_id,
                receipt_email=customer_email,
                payment_method=default_payment_method,
                confirm=True
            )
        except stripe.error.StripeError as e:
            QMessageBox.critical(self, "Payment Error", f"Stripe Error: {e.user_message}")
            return

        if charge["status"] not in ["succeeded", "requires_capture"]:
            QMessageBox.warning(self, "Payment Failed", "Payment was not successful.")
            return

        # ✅ Store payment in the database
        self.record_payment_in_db(customer_id, "Credit Card", total_cost, charge["id"])
        QMessageBox.information(self, "Payment Successful", "The payment was processed successfully!")


    def open_add_card_window(self, stripe_customer_id):
        """Opens a Stripe-hosted link to allow the customer to add a new payment method."""
        try:
            # ✅ Generate a Stripe setup link to add a card
            setup_intent = stripe.SetupIntent.create(
                customer=stripe_customer_id
            )
            
            # ✅ Open the link in a browser
            url = f"https://checkout.stripe.com/pay/{setup_intent['id']}"
            webbrowser.open(url)

            QMessageBox.information(self, "Add Card", "A window has been opened for the customer to enter their card details.")
        
        except stripe.error.StripeError as e:
            QMessageBox.critical(self, "Stripe Error", f"Failed to generate add-card link: {e.user_message}")

    def record_payment_in_db(self, customer_id, payment_method, total_cost, stripe_charge_id=None):
        """ Record payment in database and update ticket statuses. """
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            for ticket_number, _ in self.selected_ticket_data:
                cursor.execute("UPDATE Tickets SET payment = 1 WHERE ticket_number = ?", (ticket_number,))
                cursor.execute(
                    "INSERT INTO Payments (customer_id, ticket_number, payment_method, amount, stripe_charge_id) VALUES (?, ?, ?, ?, ?)",
                    (customer_id, ticket_number, payment_method, total_cost, stripe_charge_id),
                )
            conn.commit()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error recording payment: {e}")
        finally:
            conn.close()

    def clear_fields(self):
        """ Clears all input fields in the payment window. """
        self.ui.taxes_display.setText("0")
        self.ui.initial_cost_display.setText(f"{self.total_cost:.2f}")
        self.ui.total_cost_display.setText(f"${self.total_cost:.2f}")
        self.ui.cash_received_input.setText("")
        self.ui.customer_change_display.setText("$0.00")
        self.ui.coupons.setCurrentIndex(0)  # Reset coupon selection

    def cancel_and_close(self):
        """ Closes the payment window without processing payment. """
        self.reject()  # This closes the dialog without saving

    def get_selected_payment_method(self):
        """ Get the selected payment method. """
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
