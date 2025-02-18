from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.models import get_db_connection

# Credit Card APIs
credit_cards_bp = Blueprint('credit_cards', __name__)

# Retrieve saved credit/debit cards
@credit_cards_bp.route('/api/credit-cards', methods=['GET'])
@jwt_required()
def get_credit_cards():
    """
    Fetch all saved credit/debit cards for the authenticated user.
    """
    user_id = get_jwt_identity()['id']
    conn = get_db_connection()
    try:
        cards = conn.execute(
            '''
            SELECT id, card_last_4, expiration_date, is_default 
            FROM CreditCards 
            WHERE user_id = ? 
            ORDER BY is_default DESC
            ''',
            (user_id,)
        ).fetchall()
        conn.close()
        return jsonify([dict(row) for row in cards]), 200
    except Exception as e:
        conn.close()
        abort(500, description=f"Error fetching credit cards: {str(e)}")

# Add a new credit/debit card
@credit_cards_bp.route('/api/credit-cards', methods=['POST'])
@jwt_required()
def add_credit_card():
    """
    Add a new credit/debit card for the authenticated user.
    """
    data = request.get_json()
    required_fields = ['card_last_4', 'expiration_date', 'stripe_token']

    # Validate input
    for field in required_fields:
        if field not in data or not data[field].strip():
            abort(400, description=f"'{field}' is required")

    user_id = get_jwt_identity()['id']
    conn = get_db_connection()

    try:
        # Insert the card into the database
        conn.execute(
            '''
            INSERT INTO CreditCards (user_id, card_last_4, expiration_date, token, is_default) 
            VALUES (?, ?, ?, ?, ?)
            ''',
            (
                user_id,
                data['card_last_4'],
                data['expiration_date'],
                data['stripe_token'],
                1 if data.get('set_as_default', False) else 0
            )
        )
        # If set_as_default is True, ensure all other cards are not default
        if data.get('set_as_default', False):
            conn.execute(
                '''
                UPDATE CreditCards 
                SET is_default = 0 
                WHERE user_id = ? AND card_last_4 != ?
                ''',
                (user_id, data['card_last_4'])
            )
        conn.commit()
        conn.close()
        return jsonify({'message': 'Credit card added successfully'}), 201
    except Exception as e:
        conn.close()
        abort(500, description=f"Error adding credit card: {str(e)}")

# Remove a saved credit/debit card
@credit_cards_bp.route('/api/credit-cards/<int:card_id>', methods=['DELETE'])
@jwt_required()
def delete_credit_card(card_id):
    """
    Delete a saved credit/debit card by card ID for the authenticated user.
    """
    user_id = get_jwt_identity()['id']
    conn = get_db_connection()
    try:
        # Check if the card exists
        card = conn.execute(
            'SELECT * FROM CreditCards WHERE id = ? AND user_id = ?',
            (card_id, user_id)
        ).fetchone()
        if not card:
            conn.close()
            abort(404, description="Card not found")

        # Delete the card
        conn.execute(
            'DELETE FROM CreditCards WHERE id = ? AND user_id = ?',
            (card_id, user_id)
        )
        conn.commit()
        conn.close()
        return jsonify({'message': 'Credit card deleted successfully'}), 200
    except Exception as e:
        conn.close()
        abort(500, description=f"Error deleting credit card: {str(e)}")

# Set a default credit/debit card
@credit_cards_bp.route('/api/credit-cards/<int:card_id>/set-default', methods=['POST'])
@jwt_required()
def set_default_credit_card(card_id):
    """
    Set a credit/debit card as the default for the authenticated user.
    """
    user_id = get_jwt_identity()['id']
    conn = get_db_connection()
    try:
        # Validate the card exists for the user
        card = conn.execute(
            'SELECT * FROM CreditCards WHERE id = ? AND user_id = ?',
            (card_id, user_id)
        ).fetchone()
        if not card:
            conn.close()
            abort(404, description="Card not found")

        # Update default card
        conn.execute(
            'UPDATE CreditCards SET is_default = 0 WHERE user_id = ?',
            (user_id,)
        )
        conn.execute(
            'UPDATE CreditCards SET is_default = 1 WHERE id = ?',
            (card_id,)
        )
        conn.commit()
        conn.close()
        return jsonify({'message': 'Default credit card updated successfully'}), 200
    except Exception as e:
        conn.close()
        abort(500, description=f"Error updating default credit card: {str(e)}")
