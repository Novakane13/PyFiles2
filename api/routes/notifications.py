from flask import Blueprint, jsonify, request, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.models import get_db_connection
from datetime import datetime

notifications_bp = Blueprint('notifications', __name__)

# Helper function to create notifications
def create_notification(conn, customer_id, notification_type, message):
    """
    Create a new notification in the database.
    """
    conn.execute(
        '''
        INSERT INTO Notifications (customer_id, type, message, created_at, is_read)
        VALUES (?, ?, ?, ?, 0)
        ''',
        (customer_id, notification_type, message, datetime.now())
    )
    conn.commit()

# Retrieve all notifications for the logged-in user
@notifications_bp.route('/api/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """
    Fetch notifications for the current user.
    Query parameters:
    - is_read (optional): 0 for unread notifications, 1 for read notifications.
    """
    user_id = get_jwt_identity()['id']
    is_read = request.args.get('is_read')  # Optional filter

    query = 'SELECT * FROM Notifications WHERE customer_id = ?'
    params = [user_id]

    if is_read in ['0', '1']:  # Filter by read status if provided
        query += ' AND is_read = ?'
        params.append(is_read)

    query += ' ORDER BY created_at DESC'  # Sort by newest first

    conn = get_db_connection()
    notifications = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify([dict(row) for row in notifications]), 200

# Mark notifications as read
@notifications_bp.route('/api/notifications/read', methods=['POST'])
@jwt_required()
def mark_notifications_read():
    """
    Mark all notifications as read for the current user.
    """
    user_id = get_jwt_identity()['id']
    conn = get_db_connection()
    conn.execute('UPDATE Notifications SET is_read = 1 WHERE customer_id = ?', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Notifications marked as read'}), 200

# Create a new notification
@notifications_bp.route('/api/notifications', methods=['POST'])
@jwt_required()
def create_user_notification():
    """
    Create a notification for the logged-in user. Admin-only functionality could be added here.
    """
    user_id = get_jwt_identity()['id']
    data = request.get_json()

    if not data or 'type' not in data or 'message' not in data:
        abort(400, description="Missing 'type' or 'message' in the request body")

    conn = get_db_connection()
    create_notification(conn, user_id, data['type'], data['message'])
    conn.close()

    return jsonify({'message': 'Notification created successfully'}), 201

# Real-time WebSocket notifications (Placeholder for WebSocket server)
@notifications_bp.route('/api/notifications/realtime', methods=['GET'])
def realtime_notifications():
    """
    WebSocket connection placeholder for real-time notifications.
    To be implemented with a WebSocket server (e.g., Flask-SocketIO or similar).
    """
    return jsonify({'message': 'Real-time notifications require WebSocket connection'}), 501

# Specific notifications for events
def notify_order_ready(customer_id):
    """
    Notify a customer that their order is ready for pickup.
    """
    conn = get_db_connection()
    create_notification(
        conn,
        customer_id,
        'Order Ready',
        'Your order is ready for pickup!'
    )
    conn.close()

def notify_monthly_bill_ready(customer_id):
    """
    Notify a customer that their monthly bill is ready to be paid.
    """
    conn = get_db_connection()
    create_notification(
        conn,
        customer_id,
        'Monthly Bill',
        'Your monthly bill is ready for payment.'
    )
    conn.close()

def notify_delivery_status(customer_id, status):
    """
    Notify a customer about delivery status updates.
    """
    conn = get_db_connection()
    message = 'Your delivery is on its way!' if status == 'Out for Delivery' else 'Your delivery has been dropped off!'
    create_notification(conn, customer_id, 'Delivery Update', message)
    conn.close()

def notify_account_change(customer_id):
    """
    Notify a customer about changes to their account information.
    """
    conn = get_db_connection()
    create_notification(
        conn,
        customer_id,
        'Account Update',
        'Your account information has been updated.'
    )
    conn.close()

def notify_new_message(customer_id):
    """
    Notify a customer about a new message from an employee.
    """
    conn = get_db_connection()
    create_notification(
        conn,
        customer_id,
        'New Message',
        'You have a new message from our team.'
    )
    conn.close()
