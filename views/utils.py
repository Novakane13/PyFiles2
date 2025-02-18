import sqlite3
import os
import stripe
import bcrypt
import smtplib
from firebase_admin import messaging
from cryptography.fernet import Fernet
from controllers.config import STRIPE_SECRET_KEY, get_db_path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from controllers.config import (
    AWS_SES_USERNAME,
    AWS_SES_PASSWORD,
    AWS_SES_SMTP_SERVER,
    AWS_SES_SMTP_PORT,
    AWS_SES_SENDER_EMAIL
)

stripe.api_key = STRIPE_SECRET_KEY


def get_db_connection():
    """Establish database connection"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn
    
def get_employee_permissions(employee_id):
    """Fetch all permissions assigned to an employee's role(s)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.name FROM permissions p
        JOIN role_permissions rp ON p.id = rp.permission_id
        JOIN employee_roles er ON rp.role_id = er.role_id
        WHERE er.employee_id = ?
    """, (employee_id,))
    
    permissions = {row[0] for row in cursor.fetchall()}
    conn.close()
    return permissions

def has_permission(employee_id, permission_name):
    """Check if an employee has a specific permission."""
    permissions = get_employee_permissions(employee_id)
    return permission_name in permissions

def get_next_ticket_number():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path = os.path.join(project_root, 'models', 'pos_system.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get max from Tickets
    cursor.execute("SELECT MAX(ticket_number) FROM Tickets")
    max_ticket_detailed = cursor.fetchone()[0]
    if max_ticket_detailed is None:
        max_ticket_detailed = 0
    else:
        max_ticket_detailed = int(max_ticket_detailed)

    # Get max from quick_tickets
    cursor.execute("SELECT MAX(ticket_number) FROM quick_tickets")
    max_ticket_quick = cursor.fetchone()[0]
    if max_ticket_quick is None:
        max_ticket_quick = 0
    else:
        max_ticket_quick = int(max_ticket_quick)

    # Whichever is larger
    max_ticket_number = max(max_ticket_detailed, max_ticket_quick)
    conn.close()
    
    return max_ticket_number + 1

def get_stripe_customer_id_and_email(customer_id):
    """Fetches or creates a Stripe Customer ID, ensuring the customer has an email."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT stripe_customer_id, first_name, last_name, COALESCE(email, '') FROM customers WHERE id = ?", (customer_id,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return None, None  # No customer found

    stripe_customer_id, first_name, last_name, email = result

    # 🚨 Check if the email is missing and provide a fallback
    if not email:
        email = f"{first_name.lower()}.{last_name.lower()}@example.com"  # Temporary placeholder

    # ✅ If Stripe ID exists, return it
    if stripe_customer_id:
        conn.close()
        return stripe_customer_id, email

    # 🔥 Auto-create Stripe customer if missing
    stripe_customer_id = create_stripe_customer(f"{first_name} {last_name}", email)

    if stripe_customer_id:
        cursor.execute("UPDATE customers SET stripe_customer_id = ? WHERE id = ?", (stripe_customer_id, customer_id))
        conn.commit()

    conn.close()
    return stripe_customer_id, email




def create_stripe_customer(customer_name, email):
    """Creates a Stripe customer and returns the Stripe customer ID."""
    if not email:
        print("❌ Error: Cannot create Stripe customer without an email.")
        return None

    try:
        customer = stripe.Customer.create(
            name=customer_name,
            email=email
        )
        print(f"✅ Stripe customer created: {customer['id']} ({email})")
        return customer["id"]
    except stripe.error.StripeError as e:
        print(f"❌ Stripe Error: {e.user_message}")
        return None



def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    if isinstance(hashed, str):
        hashed = hashed.encode('utf-8') 
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def update_employee(conn, employee_id, display_name, phone, acting_employee_id):
    """Update employee details, restricted by role permissions."""
    if not has_permission(acting_employee_id, "Manage Employees"):
        raise PermissionError("Access Denied: You do not have permission to manage employees.")

    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Employees
        SET display_name = ?, phone_number = ?
        WHERE employee_id = ?
    """, (display_name, phone, employee_id))
    conn.commit()


def insert_employee(conn, display_name, employee_name, phone, pin):
    if not has_permission(acting_employee_id, "Manage Employees"):
        raise PermissionError("Access Denied: You do not have permission to add employees.")

    cursor = conn.cursor()
    hashed_pin = hash_password(pin)
    cursor.execute("""
        INSERT INTO Employees (display_name, employee_name, phone_number, password_hash, date_created)
        VALUES (?, ?, ?, ?, DATETIME('now'))
    """, (display_name, employee_name, phone, hashed_pin))
    conn.commit()
    return cursor.lastrowid  # Return the new employee ID



class Encryption:
    """Handles encryption for sensitive data."""
    def __init__(self):
        self.key = os.environ.get("ENCRYPTION_KEY")  # Load securely
        if not self.key:
            raise ValueError("Missing encryption key. Set ENCRYPTION_KEY in environment variables.")
        self.cipher = Fernet(self.key)

    def encrypt(self, data):
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data):
        return self.cipher.decrypt(encrypted_data.encode()).decode()


### ---- Stripe Payment Methods with RBAC ---- ###

def add_card_to_stripe_and_save(acting_employee_id, customer_id, card_number, exp_month, exp_year, cvc, is_default):
    """Add a credit card to Stripe and save details in the database."""
    if not has_permission(acting_employee_id, "Credit/debit card processing"):
        raise PermissionError("❌ Access Denied: No permission to process credit cards.")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Retrieve or create the Stripe customer ID
        stripe_customer_id, _ = get_stripe_customer_id_and_email(customer_id)

        if not stripe_customer_id:
            raise Exception("❌ Could not retrieve or create Stripe Customer ID.")

        # Add the card to Stripe
        token = stripe.Token.create(
            card={
                "number": card_number,
                "exp_month": exp_month,
                "exp_year": exp_year,
                "cvc": cvc,
            }
        )

        card = stripe.Customer.create_source(stripe_customer_id, source=token.id)

        # Encrypt card details before storing
        encryption = Encryption()
        encrypted_last_4 = encryption.encrypt(card["last4"])
        encrypted_exp = encryption.encrypt(f"{exp_month}/{exp_year}")

        # Save card details in the database
        cursor.execute(
            """
            INSERT INTO CreditCards (customer_id, stripe_customer_id, stripe_card_id, card_last_4, expiration_date, is_default)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (customer_id, stripe_customer_id, card.id, encrypted_last_4, encrypted_exp, is_default),
        )

        # Set as default card if specified
        if is_default:
            cursor.execute(
                "UPDATE CreditCards SET is_default = 0 WHERE customer_id = ? AND stripe_card_id != ?",
                (customer_id, card.id),
            )

        conn.commit()
        print(f"✅ Card added successfully for Customer ID {customer_id}.")
        return {"message": "Card added successfully", "last_4": card["last4"]}

    except Exception as e:
        conn.rollback()
        print(f"❌ Error adding card: {e}")
        return None

    finally:
        conn.close()



def get_default_card_from_db(acting_employee_id, customer_id):
    """Retrieve the default card for a customer from the database."""
    if not has_permission(acting_employee_id, "Credit/debit card processing"):
        raise PermissionError("Access Denied: You do not have permission to access card details.")

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT stripe_card_id, card_last_4, expiration_date FROM CreditCards WHERE customer_id = ? AND is_default = 1",
            (customer_id,),
        )
        card = cursor.fetchone()
        if card:
            encryption = Encryption()
            decrypted_last_4 = encryption.decrypt(card[1])
            decrypted_exp = encryption.decrypt(card[2])
            return {"stripe_card_id": card[0], "last_4": decrypted_last_4, "expiration": decrypted_exp}
        else:
            return None

    except Exception as e:
        raise Exception(f"Error retrieving default card: {str(e)}")

    finally:
        conn.close()


def delete_card(acting_employee_id, customer_id, last_4):
    """Remove card from Stripe and the database."""
    if not has_permission(acting_employee_id, "Credit/debit card processing"):
        raise PermissionError("❌ Access Denied: No permission to delete stored cards.")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Find the card in the database
        cursor.execute(
            "SELECT stripe_card_id FROM CreditCards WHERE customer_id = ?",
            (customer_id,),
        )
        card = cursor.fetchone()

        if not card:
            print("❌ Card not found in database.")
            return {"message": "Card not found"}

        stripe_card_id = card[0]

        # Delete from Stripe
        stripe.Customer.delete_source(customer_id, stripe_card_id)

        # Remove from database
        cursor.execute("DELETE FROM CreditCards WHERE customer_id = ? AND stripe_card_id = ?", (customer_id, stripe_card_id))
        conn.commit()

        print(f"✅ Card deleted for Customer ID {customer_id}.")
        return {"message": "Card deleted successfully"}

    except Exception as e:
        conn.rollback()
        print(f"❌ Error deleting card: {e}")
        return None

    finally:
        conn.close()



def save_card_to_database(acting_employee_id, customer_id, stripe_customer_id, stripe_card_id, last_4, exp_date, is_default):
    """Save encrypted card metadata in the database."""
    if not has_permission(acting_employee_id, "Credit/debit card processing"):
        raise PermissionError("❌ Access Denied: No permission to save card data.")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        encryption = Encryption()
        encrypted_last_4 = encryption.encrypt(last_4)
        encrypted_exp = encryption.encrypt(exp_date)

        cursor.execute(
            """
            INSERT INTO CreditCards (customer_id, stripe_customer_id, stripe_card_id, card_last_4, expiration_date, is_default)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (customer_id, stripe_customer_id, stripe_card_id, encrypted_last_4, encrypted_exp, is_default),
        )

        # Set as default card if specified
        if is_default:
            cursor.execute(
                "UPDATE CreditCards SET is_default = 0 WHERE customer_id = ? AND stripe_card_id != ?",
                (customer_id, stripe_card_id),
            )

        conn.commit()
        print(f"✅ Card saved in database for Customer ID {customer_id}.")
        return {"message": "Card saved successfully"}

    except Exception as e:
        conn.rollback()
        print(f"❌ Error saving card: {e}")
        return None

    finally:
        conn.close()


def send_email(recipient_email, subject, body):
    """Send an email using Amazon SES"""
    try:
        msg = MIMEMultipart()
        msg['From'] = AWS_SES_SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(AWS_SES_SMTP_SERVER, AWS_SES_SMTP_PORT)
        server.starttls()
        server.login(AWS_SES_USERNAME, AWS_SES_PASSWORD)
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()

        print(f"✅ Email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"❌ Email sending error: {e}")
        return False

def send_firebase_notification(customer_fcm_token, title, body):
    """
    Sends a push notification to the customer's device using Firebase Cloud Messaging (FCM).
    
    :param customer_fcm_token: The FCM token of the customer's device
    :param title: Notification title
    :param body: Notification body message
    """
    if not customer_fcm_token:
        print("❌ No FCM token found for customer.")
        return False

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=customer_fcm_token,  # Customer's unique device token
    )

    try:
        response = messaging.send(message)
        print(f"✅ Firebase Notification Sent: {response}")
        return True
    except Exception as e:
        print(f"❌ Firebase Notification Failed: {e}")
        return False

def save_customer_fcm_token(customer_id, fcm_token):
    """ Save or update a customer's Firebase Cloud Messaging (FCM) token in the database. """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute("UPDATE customers SET fcm_token = ? WHERE id = ?", (fcm_token, customer_id))
    conn.commit()
    conn.close()
    
    print(f"✅ Saved FCM Token for Customer ID {customer_id}")

def get_customer_fcm_token(customer_id):
    """ Retrieve a customer's FCM token from the database. """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute("SELECT fcm_token FROM customers WHERE id = ?", (customer_id,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None
