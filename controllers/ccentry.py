from PySide6.QtWidgets import QDialog, QMessageBox
import stripe
from views.ccinfo import Ui_cc_info_dialog
from views.utils import get_db_connection
from controllers.config import STRIPE_SECRET_KEY
import firebase_admin
from firebase_admin import messaging


class CreditCardEntryDialog(QDialog):
    """Dialog for entering or swiping credit card details"""

    def __init__(self, customer_id, parent=None):
        super().__init__(parent)
        self.ui = Ui_cc_info_dialog()
        self.ui.setupUi(self)

        self.customer_id = self.ensure_integer(customer_id)
        stripe.api_key = STRIPE_SECRET_KEY  

        # Connect manual save button to Stripe
        self.ui.buttonBox.accepted.connect(self.manual_card_entry)

    def ensure_integer(self, customer_id):
        """Ensures customer_id is an integer"""
        if isinstance(customer_id, list) and customer_id:
            return customer_id[0]  
        elif isinstance(customer_id, dict):
            return customer_id.get("id", None)  
        return customer_id

    def manual_card_entry(self):
        """Process manual credit card entry"""
        card_number = self.ui.lineEdit.text().strip()
        exp_date = self.ui.lineEdit_2.text().strip()
        cvc = self.ui.lineEdit_3.text().strip()

        if not card_number or not exp_date or not cvc:
            QMessageBox.warning(self, "Input Error", "All fields must be filled out.")
            return

        try:
            exp_month, exp_year = map(int, exp_date.split('/'))
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Expiration date must be in MM/YY format.")
            return

        self.store_card_with_stripe(card_number, exp_month, exp_year, cvc)

    def store_card_with_stripe(self, card_number, exp_month, exp_year, cvc):
        """Stores the card securely using Stripe"""
        try:
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={
                    "number": card_number,
                    "exp_month": exp_month,
                    "exp_year": exp_year,
                    "cvc": cvc,
                }
            )

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT stripe_customer_id, email FROM customers WHERE id = ?", (self.customer_id,))
            result = cursor.fetchone()

            if result and result[0]:
                stripe_customer_id = result[0]
            else:
                # If customer does not exist, create them with a valid email
                customer_email = result[1] if result and result[1] else f"user_{self.customer_id}@example.com"
                customer = stripe.Customer.create(email=customer_email)
                stripe_customer_id = customer.id
                cursor.execute("UPDATE customers SET stripe_customer_id = ? WHERE id = ?", (stripe_customer_id, self.customer_id))
                conn.commit()

            # Attach the payment method to the customer
            stripe.PaymentMethod.attach(payment_method.id, customer=stripe_customer_id)
            stripe.Customer.modify(
                stripe_customer_id,
                invoice_settings={"default_payment_method": payment_method.id},
            )

            # Save card details in the database
            cursor.execute(
                """
                INSERT INTO customer_cards (customer_id, brand, last4, exp_date, stripe_card_id, is_default)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (self.customer_id, payment_method.card["brand"], payment_method.card["last4"], f"{exp_month}/{exp_year}", payment_method.id, 1),
            )
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Success", "Credit card saved successfully!")
            self.send_firebase_notification()
            self.accept()

        except stripe.error.StripeError as e:
            QMessageBox.critical(self, "Stripe Error", f"Failed to store card: {e.user_message}")

    def send_firebase_notification(self):
        """Send a confirmation notification using Firebase Cloud Messaging"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT fcm_token FROM customers WHERE id = ?", (self.customer_id,))
            result = cursor.fetchone()
            conn.close()

            customer_fcm_token = result[0] if result else None
            if not customer_fcm_token:
                print("❌ No FCM token found for customer.")
                return False

            if not firebase_admin._apps:
                print("❌ Firebase app is not initialized.")
                return False

            message = messaging.Message(
                notification=messaging.Notification(
                    title="Payment Method Added",
                    body="Your credit card has been securely added to your account.",
                ),
                token=customer_fcm_token,
            )

            response = messaging.send(message)
            print(f"✅ Firebase Notification Sent: {response}")
            return True

        except Exception as e:
            print(f"❌ Firebase Notification Failed: {e}")
            return False
