from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.models import get_db_connection

messages_bp = Blueprint('messages', __name__)

# Fetch conversations
@messages_bp.route('/api/messages', methods=['GET'])
@jwt_required()
def get_messages():
    """
    Fetch all messages for the authenticated user.
    """
    conn = get_db_connection()
    try:
        messages = conn.execute(
            '''
            SELECT * FROM Messages WHERE user_id = ? ORDER BY sent_at DESC
            ''',
            (get_jwt_identity()['id'],)
        ).fetchall()
    except Exception as e:
        conn.close()
        abort(500, description=f"Error fetching messages: {str(e)}")
    conn.close()
    return jsonify([dict(row) for row in messages]), 200

# Send a new message
@messages_bp.route('/api/messages', methods=['POST'])
@jwt_required()
def send_message():
    """
    Send a new message to a recipient.
    """
    data = request.get_json()
    required_fields = ['recipient_id', 'content']

    for field in required_fields:
        if field not in data or not data[field]:
            abort(400, description=f"'{field}' is required")

    conn = get_db_connection()
    try:
        conn.execute(
            '''
            INSERT INTO Messages (user_id, recipient_id, content, sent_at) 
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''',
            (get_jwt_identity()['id'], data['recipient_id'], data['content'])
        )
        conn.commit()
    except Exception as e:
        conn.close()
        abort(500, description=f"Error sending message: {str(e)}")
    conn.close()
    return jsonify({'message': 'Message sent successfully'}), 201
