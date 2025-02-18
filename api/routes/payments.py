from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.models import get_db_connection
import stripe

stripe.api_key = "pk_test_51QEmC6F9q8Y1A3UES8uzimDczaKS3xMRUNr9QN4vhQN8wjktGMEONNrWWP7mFCJRrdYDmTPADDDVxn1GvS0mTkCw00XlEDwkSY"

payments_bp = Blueprint('payments', __name__)

# Retrieve outstanding balance
@payments_bp.route('/api/balance', methods=['GET'])
def get_balance():
    """
    Fetch outstanding balance for a customer.
    """
    # For testing, get customer_id directly from query params
    customer_id = request.args.get('customer_id', type=int)
    if not customer_id:
        abort(400, description="'customer_id' is required")

    conn = get_db_connection()
    try:
        balance = conn.execute(
            '''
            SELECT COALESCE(SUM(total_price - payment), 0) AS outstanding_balance
            FROM tickets
            WHERE customer_id = ? AND pickedup = 0 AND total_price > payment
            ''',
            (customer_id,)
        ).fetchone()
    except Exception as e:
        conn.close()
        abort(500, description=f"Error fetching balance: {str(e)}")
    conn.close()

    return jsonify({'outstanding_balance': balance['outstanding_balance']}), 200


# Make a payment
@payments_bp.route('/api/payments', methods=['POST'])
def make_payment():
    """
    Make a payment toward the user's outstanding balance.
    """
    data = request.get_json()
    if 'amount' not in data or not isinstance(data['amount'], (int, float)) or data['amount'] <= 0:
        abort(400, description="'amount' is required and must be a positive number")
    if 'customer_id' not in data:
        abort(400, description="'customer_id' is required")

    customer_id = data['customer_id']
    payment_amount = data['amount']

    conn = get_db_connection()
    try:
        # Apply payment to unpaid tickets in order of ticket creation
        conn.execute(
            '''
            UPDATE Tickets
            SET payment = MIN(total_price, payment + ?)
            WHERE customer_id = ? AND pickedup = 0 AND total_price > payment
            ''',
            (payment_amount, customer_id)
        )
        conn.commit()
    except Exception as e:
        conn.close()
        abort(500, description=f"Error processing payment: {str(e)}")
    conn.close()
    return jsonify({'message': 'Payment successful'}), 200

# Pay a specific bill
@payments_bp.route('/api/bills', methods=['POST'])
@jwt_required()
def pay_bill():
    """
    Pay a specific bill by ticket ID.
    """
    data = request.get_json()
    if 'ticket_id' not in data:
        abort(400, description="'ticket_id' is required")

    user_id = get_jwt_identity()['id']
    conn = get_db_connection()
    try:
        result = conn.execute(
            '''
            UPDATE Tickets 
            SET payment = total_price 
            WHERE id = ? AND customer_id = ? AND pickedup = 0
            ''',
            (data['ticket_id'], user_id)
        )
        if result.rowcount == 0:
            abort(404, description="Ticket not found or already paid")
        conn.commit()
    except Exception as e:
        conn.close()
        abort(500, description=f"Error paying bill: {str(e)}")
    conn.close()
    return jsonify({'message': 'Bill paid successfully'}), 200

# Retrieve billing statements
@payments_bp.route('/api/billing-statements', methods=['GET'])
@jwt_required()
def get_billing_statements():
    """
    Fetch all billing statements with payments for the authenticated user.
    """
    user_id = get_jwt_identity()['id']
    conn = get_db_connection()
    try:
        statements = conn.execute(
            '''
            SELECT * 
            FROM Tickets 
            WHERE customer_id = ? AND payment > 0
            ORDER BY date_created DESC
            ''',
            (user_id,)
        ).fetchall()
    except Exception as e:
        conn.close()
        abort(500, description=f"Error fetching billing statements: {str(e)}")
    conn.close()
    return jsonify([dict(row) for row in statements]), 200

# Fetch payment history
@payments_bp.route('/api/payments', methods=['GET'])
@jwt_required()
def get_payment_history():
    """
    Fetch payment history for the authenticated user.
    """
    user_id = get_jwt_identity()['id']
    conn = get_db_connection()
    try:
        payments = conn.execute(
            'SELECT * FROM Payments WHERE customer_id = ? ORDER BY payment_date DESC',
            (user_id,)
        ).fetchall()
    except Exception as e:
        conn.close()
        abort(500, description=f"Error fetching payment history: {str(e)}")
    conn.close()
    return jsonify([dict(row) for row in payments]), 200

# Fetch a payment receipt
@payments_bp.route('/api/receipts/<int:payment_id>', methods=['GET'])
@jwt_required()
def get_payment_receipt(payment_id):
    """
    Fetch a specific payment receipt by payment ID.
    """
    user_id = get_jwt_identity()['id']
    conn = get_db_connection()
    try:
        receipt = conn.execute(
            'SELECT * FROM Payments WHERE id = ? AND customer_id = ?',
            (payment_id, user_id)
        ).fetchone()
        if not receipt:
            abort(404, description="Receipt not found")
    except Exception as e:
        conn.close()
        abort(500, description=f"Error fetching receipt: {str(e)}")
    conn.close()
    return jsonify(dict(receipt)), 200

@payments_bp.route('/api/save-card', methods=['POST'])
@jwt_required()
def save_card():
    """
    Saves a customer's card to Stripe.
    """
    data = request.get_json()
    payment_method_id = data.get('payment_method_id')
    if not payment_method_id:
        abort(400, description="Payment method ID is required")

    user_id = get_jwt_identity()['id']

    # Retrieve or create Stripe customer
    conn = get_db_connection()
    customer = conn.execute('SELECT stripe_customer_id FROM Users WHERE id = ?', (user_id,)).fetchone()
    if not customer or not customer['stripe_customer_id']:
        stripe_customer = stripe.Customer.create()
        conn.execute('UPDATE Users SET stripe_customer_id = ? WHERE id = ?', (stripe_customer['id'], user_id))
        conn.commit()
        stripe_customer_id = stripe_customer['id']
    else:
        stripe_customer_id = customer['stripe_customer_id']

    # Attach the payment method to the customer
    try:
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=stripe_customer_id,
        )
        stripe.Customer.modify(
            stripe_customer_id,
            invoice_settings={"default_payment_method": payment_method_id}
        )
        return jsonify({"message": "Card saved successfully"}), 200
    except Exception as e:
        abort(500, description=f"Error saving card: {str(e)}")


# Retrieve saved cards
@payments_bp.route('/api/cards', methods=['GET'])
@jwt_required()
def get_saved_cards():
    """
    Retrieve saved cards for the authenticated user.
    """
    user_id = get_jwt_identity()['id']
    conn = get_db_connection()
    customer = conn.execute('SELECT stripe_customer_id FROM Users WHERE id = ?', (user_id,)).fetchone()
    if not customer or not customer['stripe_customer_id']:
        return jsonify([]), 200

    stripe_customer_id = customer['stripe_customer_id']
    try:
        payment_methods = stripe.PaymentMethod.list(
            customer=stripe_customer_id,
            type="card",
        )
        cards = [
            {
                "id": pm.id,
                "brand": pm.card.brand,
                "last4": pm.card.last4,
                "exp_month": pm.card.exp_month,
                "exp_year": pm.card.exp_year,
                "is_default": pm.id == stripe.Customer.retrieve(stripe_customer_id)['invoice_settings']['default_payment_method']
            }
            for pm in payment_methods['data']
        ]
        return jsonify(cards), 200
    except Exception as e:
        abort(500, description=f"Error retrieving saved cards: {str(e)}")

@payments_bp.route('/api/cards/<card_id>', methods=['DELETE'])
@jwt_required()
def delete_card(card_id):
    """
    Deletes a saved card for the authenticated user.
    """
    user_id = get_jwt_identity()['id']
    conn = get_db_connection()
    customer = conn.execute('SELECT stripe_customer_id FROM Users WHERE id = ?', (user_id,)).fetchone()
    if not customer or not customer['stripe_customer_id']:
        abort(400, description="No Stripe customer associated with this user")

    stripe_customer_id = customer['stripe_customer_id']
    try:
        stripe.PaymentMethod.detach(card_id)
        return jsonify({"message": "Card deleted successfully"}), 200
    except Exception as e:
        abort(500, description=f"Error deleting card: {str(e)}")

# Create Payment Intent
@payments_bp.route('/api/create-payment-intent', methods=['POST'])
@jwt_required()
def create_payment_intent():
    """
    Creates a payment intent with Stripe for the given amount.
    """
    data = request.get_json()
    amount = data.get('amount')
    if not amount or amount <= 0:
        abort(400, description="Invalid payment amount")

    user_id = get_jwt_identity()['id']

    # Retrieve or create Stripe customer
    conn = get_db_connection()
    customer = conn.execute('SELECT stripe_customer_id FROM Users WHERE id = ?', (user_id,)).fetchone()
    if not customer or not customer['stripe_customer_id']:
        # Create a new Stripe customer if none exists
        stripe_customer = stripe.Customer.create()
        conn.execute('UPDATE Users SET stripe_customer_id = ? WHERE id = ?', (stripe_customer['id'], user_id))
        conn.commit()
        stripe_customer_id = stripe_customer['id']
    else:
        stripe_customer_id = customer['stripe_customer_id']

    # Create payment intent
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert dollars to cents
            currency="usd",
            customer=stripe_customer_id,
            automatic_payment_methods={"enabled": True},
        )
        return jsonify({"client_secret": payment_intent.client_secret}), 200
    except Exception as e:
        abort(500, description=f"Error creating payment intent: {str(e)}")
