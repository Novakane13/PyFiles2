import sqlite3
import stripe
from PySide6.QtWidgets import QDialog, QMessageBox
from firebase_admin import messaging
from views.moreinfoui import Ui_MoreInfoDialog  
from api.models import get_db_connection
from controllers.config import STRIPE_SECRET_KEY
from views.utils import send_email  

stripe.api_key = STRIPE_SECRET_KEY

class MoreInfoDialog(QDialog):

    def __init__(self, customer_id, parent=None):
        super().__init__(parent)
        self.ui = Ui_MoreInfoDialog()
        self.ui.setupUi(self)

        self.customer_id = customer_id

        # self.ui.add_cc_button.clicked.connect(self.open_credit_card_dialog)  # Placeholder
        # self.ui.send_cc_link.clicked.connect(self.send_stripe_secure_link)  
        self.ui.save_info_button.clicked.connect(self.save_customer_info)
        self.ui.close_button.clicked.connect(self.close_dialog)
        self.ui.email_customer.clicked.connect(self.email_customer)
        self.ui.send_notification.clicked.connect(self.send_firebase_notification)

        self.load_customer_data()

    # def load_cards_from_db(self):
#     """ Load saved credit cards from the database (TEMPORARILY DISABLED) """
#     try:
#         with get_db_connection() as conn:
#             cursor = conn.cursor()
#             query = """
#                 SELECT brand, last4, exp_date
#                 FROM customer_cards
#                 WHERE customer_id = ?
#             """
#             cursor.execute(query, (self.customer_id,))
#             cards = cursor.fetchall()

#         print("Loaded Cards from DB:", cards)

#         self.ui.tableWidget.setRowCount(len(cards))
#         for row, card in enumerate(cards):
#             if isinstance(card, dict):  
#                 print(f"⚠️ ERROR: Dictionary found in card data at row {row}: {card}")
#                 continue  

#             self.ui.tableWidget.setItem(row, 0, QTableWidgetItem(card[0]))  
#             self.ui.tableWidget.setItem(row, 1, QTableWidgetItem(f"**** {card[1]}"))  
#             self.ui.tableWidget.setItem(row, 2, QTableWidgetItem(card[2]))  

#     except sqlite3.Error as e:
#         QMessageBox.critical(self, "Database Error", f"Failed to load cards: {e}")



    def open_credit_card_dialog(self):
        """ Placeholder function for adding a card manually """
        QMessageBox.information(self, "Add Card", "This button is a placeholder.")

    def send_stripe_secure_link(self):
        """ Generate a Stripe-hosted link for the customer to enter card details """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT stripe_customer_id, email FROM customers WHERE id = ?", (self.customer_id,))
                result = cursor.fetchone()

            if not result or not result[0]:
                QMessageBox.warning(self, "Error", "Customer does not have a Stripe account.")
                return

            stripe_customer_id, email = result

            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                mode="setup",
                customer=stripe_customer_id,
                success_url="https://yourdomain.com/success",
                cancel_url="https://yourdomain.com/cancel",
            )

            if send_email(email, "Secure Payment Link", f"Click here to add your card securely: {session.url}"):
                QMessageBox.information(self, "Success", "Secure payment link sent to customer.")
            else:
                QMessageBox.warning(self, "Email Error", "Failed to send payment link.")

        except stripe.error.StripeError as e:
            QMessageBox.critical(self, "Stripe Error", f"Failed to generate payment link: {e.user_message}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {e}")

    def save_customer_info(self):
        """ Saves only the customer information that has been filled in. """
        try:
            fields_to_update = []
            values = []

            email = self.ui.email_add.text().strip()
            if email:
                fields_to_update.append("email = ?")
                values.append(str(email))

            home_address = self.ui.home_address.text().strip()
            if home_address:
                fields_to_update.append("home_address = ?")
                values.append(str(home_address))

            ste_apt_number = self.ui.ste_apt.text().strip()
            if ste_apt_number:
                fields_to_update.append("ste_apt_number = ?")
                values.append(str(ste_apt_number))

            zipcode = self.ui.zip_code.text().strip()
            if zipcode:
                fields_to_update.append("zipcode = ?")
                values.append(str(zipcode))

            customer_preferences = self.ui.customer_preferences.toPlainText().strip()
            if customer_preferences:
                fields_to_update.append("customer_preferences = ?")
                values.append(str(customer_preferences))

            price_list = self.ui.pricelist_selection.currentText().strip()
            if price_list:
                fields_to_update.append("price_list = ?")
                values.append(str(price_list))

            jeans_starch = self.ui.jean_starch_box.currentText().strip()
            if jeans_starch:
                fields_to_update.append("jeans_starch = ?")
                values.append(str(jeans_starch))

            shirt_starch = self.ui.shirt_starch_box.currentText().strip()
            if shirt_starch:
                fields_to_update.append("shirt_starch = ?")
                values.append(str(shirt_starch))

            if self.ui.delivery_checkbox.isChecked():
                fields_to_update.append("delivery_customer = ?")
                values.append(1)
            else:
                fields_to_update.append("delivery_customer = ?")
                values.append(0)

            if self.ui.billing_checkbox.isChecked():
                fields_to_update.append("billing_customer = ?")
                values.append(1)
            else:
                fields_to_update.append("billing_customer = ?")
                values.append(0)

            if self.ui.fold_shirts_checkbox.isChecked():
                fields_to_update.append("fold_shirts = ?")
                values.append(1)
            else:
                fields_to_update.append("fold_shirts = ?")
                values.append(0)

            if self.ui.box_shirts_checkbox.isChecked():
                fields_to_update.append("box_shirts = ?")
                values.append(1)
            else:
                fields_to_update.append("box_shirts = ?")
                values.append(0)

            if self.ui.fluff_fold_checkbox.isChecked():
                fields_to_update.append("fluff_and_fold = ?")
                values.append(1)
            else:
                fields_to_update.append("fluff_and_fold = ?")
                values.append(0)

            if not fields_to_update:
                QMessageBox.warning(self, "No Changes", "No new information was provided to save.")
                return

            query = f"UPDATE customers SET {', '.join(fields_to_update)} WHERE id = ?"
            values.append(self.customer_id) 

            print("Executing SQL Query:", query)
            print("Values:", values)

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(values))  
                conn.commit()

            QMessageBox.information(self, "Success", "Customer info saved successfully.")
            self.load_customer_data()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save info: {e}")









    def load_customer_data(self):
        """ Load customer data from the database and update the UI """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT email, home_address, ste_apt_number, zipcode, 
                        customer_preferences, price_list, 
                        jeans_starch, shirt_starch, 
                        delivery_customer, billing_customer, 
                        fold_shirts, box_shirts, fluff_and_fold
                    FROM customers
                    WHERE id = ?
                """, (self.customer_id,))
                customer = cursor.fetchone()

            if customer:
                self.ui.email_add.setText(customer[0])
                self.ui.home_address.setText(customer[1])  
                self.ui.ste_apt.setText(customer[2]) 
                self.ui.zip_code.setText(customer[3])
                self.ui.customer_preferences.setPlainText(customer[4])  

                
                self.ui.pricelist_selection.setCurrentText(customer[5] or "")

                # Load starch selections
                jeans_starch = customer[6]
                shirt_starch = customer[7]
                self.ui.jean_starch_box.setCurrentText(jeans_starch)
                self.ui.shirt_starch_box.setCurrentText(shirt_starch)

                # Load checkboxes
                self.ui.delivery_checkbox.setChecked(bool(customer[8]))
                self.ui.billing_checkbox.setChecked(bool(customer[9]))
                self.ui.fold_shirts_checkbox.setChecked(bool(customer[10]))
                self.ui.box_shirts_checkbox.setChecked(bool(customer[11]))
                self.ui.fluff_fold_checkbox.setChecked(bool(customer[12]))

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load customer info: {e}")


    def email_customer(self):
        email, _ = self.get_customer_details()
        if email:
            if send_email(email, "Subject: Customer Notification", "This is a test message."):
                QMessageBox.information(self, "Email Sent", f"Email sent to {email}.")
            else:
                QMessageBox.warning(self, "Email Failed", "Failed to send email. Check configuration.")
        else:
            QMessageBox.warning(self, "No Email", "Customer does not have an email on file.")

    def send_firebase_notification(self):
        """ Sends a push notification via Firebase to the customer """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT fcm_token FROM customers WHERE id = ?", (self.customer_id,))
                result = cursor.fetchone()

            if not result or not result[0]:
                QMessageBox.warning(self, "Error", "Customer does not have an FCM token registered.")
                return

            fcm_token = result[0]
            message = messaging.Message(
                notification=messaging.Notification(
                    title="Order Update",
                    body="Your order is ready for pickup."
                ),
                token=fcm_token
            )
            response = messaging.send(message)

            QMessageBox.information(self, "Notification Sent", f"Notification sent successfully: {response}")

        except Exception as e:
            QMessageBox.critical(self, "Firebase Error", f"Failed to send notification: {e}")

    def close_dialog(self):
        """ Closes the dialog with a check for unsaved changes """
        if self.has_unsaved_changes():
            response = QMessageBox.question(
                self,
                "Unsaved Changes",
                "There are unsaved changes. Do you still want to close?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if response == QMessageBox.No:
                return
        self.accept()

    def has_unsaved_changes(self):
        """ Placeholder function for checking unsaved changes """
        return False
