from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.models import get_db_connection

deliveries_bp = Blueprint('deliveries', __name__)

# Request a delivery pickup
@deliveries_bp.route('/api/delivery/request', methods=['POST'])
@jwt_required()
def request_delivery():
    """
    Create a delivery pickup request.
    """
    data = request.get_json()
    required_fields = ['address', 'pickup_date']

    for field in required_fields:
        if field not in data or not data[field]:
            abort(400, description=f"'{field}' is required")

    conn = get_db_connection()
    try:
        conn.execute(
            '''
            INSERT INTO Deliveries (customer_id, address, pickup_date, notes, status) 
            VALUES (?, ?, ?, ?, 'Pending')
            ''',
            (
                get_jwt_identity()['id'],
                data['address'],
                data['pickup_date'],
                data.get('notes', '')
            )
        )
        conn.commit()
    except Exception as e:
        conn.close()
        abort(500, description=f"Error creating delivery request: {str(e)}")
    conn.close()
    return jsonify({'message': 'Delivery request created successfully'}), 201

# Update delivery status
@deliveries_bp.route('/api/delivery/status', methods=['PUT'])
@jwt_required()
def update_delivery_status():
    """
    Update the status of a delivery.
    """
    data = request.get_json()
    required_fields = ['status', 'delivery_id']

    for field in required_fields:
        if field not in data or not data[field]:
            abort(400, description=f"'{field}' is required")

    conn = get_db_connection()
    try:
        result = conn.execute(
            '''
            UPDATE Deliveries 
            SET status = ? 
            WHERE customer_id = ? AND id = ?
            ''',
            (data['status'], get_jwt_identity()['id'], data['delivery_id'])
        )
        if result.rowcount == 0:
            abort(404, description="Delivery not found")
        conn.commit()
    except Exception as e:
        conn.close()
        abort(500, description=f"Error updating delivery status: {str(e)}")
    conn.close()
    return jsonify({'message': 'Delivery status updated successfully'}), 200

# Get current delivery status
@deliveries_bp.route('/api/delivery/status', methods=['GET'])
@jwt_required()
def get_delivery_status():
    """
    Fetch the latest delivery status for the user.
    """
    conn = get_db_connection()
    try:
        delivery = conn.execute(
            'SELECT * FROM Deliveries WHERE customer_id = ? ORDER BY pickup_date DESC LIMIT 1',
            (get_jwt_identity()['id'],)
        ).fetchone()
    except Exception as e:
        conn.close()
        abort(500, description=f"Error fetching delivery status: {str(e)}")
    conn.close()
    return jsonify(dict(delivery) if delivery else {'message': 'No delivery status available'}), 200

# Check delivery range
@deliveries_bp.route('/api/delivery-range', methods=['GET'])
@jwt_required()
def check_delivery_range():
    """
    Check if a postal code is within the delivery range.
    """
    postal_code = request.args.get('postal_code')
    if not postal_code:
        abort(400, description="'postal_code' is required")

    conn = get_db_connection()
    try:
        in_range = conn.execute(
            'SELECT * FROM DeliveryRanges WHERE postal_code = ?',
            (postal_code,)
        ).fetchone()
    except Exception as e:
        conn.close()
        abort(500, description=f"Error checking delivery range: {str(e)}")
    conn.close()
    return jsonify({'in_range': bool(in_range)}), 200

# Cancel a delivery request
@deliveries_bp.route('/api/delivery/<int:delivery_id>', methods=['DELETE'])
@jwt_required()
def cancel_delivery(delivery_id):
    """
    Cancel a delivery request by ID if it's still pending.
    """
    user_id = get_jwt_identity()['id']
    conn = get_db_connection()
    try:
        delivery = conn.execute(
            'SELECT * FROM Deliveries WHERE id = ? AND customer_id = ? AND status = "Pending"',
            (delivery_id, user_id)
        ).fetchone()
        if not delivery:
            abort(404, description="Delivery not found or already processed")
        conn.execute('DELETE FROM Deliveries WHERE id = ?', (delivery_id,))
        conn.commit()
    except Exception as e:
        conn.close()
        abort(500, description=f"Error canceling delivery: {str(e)}")
    conn.close()
    return jsonify({'message': 'Delivery request cancelled successfully'}), 200

# Get saved delivery addresses
@deliveries_bp.route('/api/delivery/addresses', methods=['GET'])
@jwt_required()
def get_delivery_addresses():
    """
    Fetch all saved delivery addresses for the user.
    """
    conn = get_db_connection()
    try:
        addresses = conn.execute(
            'SELECT * FROM DeliveryAddresses WHERE customer_id = ?',
            (get_jwt_identity()['id'],)
        ).fetchall()
    except Exception as e:
        conn.close()
        abort(500, description=f"Error fetching delivery addresses: {str(e)}")
    conn.close()
    return jsonify([dict(row) for row in addresses]), 200

# Save a new delivery address
@deliveries_bp.route('/api/delivery/addresses', methods=['POST'])
@jwt_required()
def save_delivery_address():
    """
    Save a new delivery address for the user.
    """
    data = request.get_json()
    required_fields = ['address', 'city', 'state', 'postal_code']

    for field in required_fields:
        if field not in data or not data[field]:
            abort(400, description=f"'{field}' is required")

    conn = get_db_connection()
    try:
        conn.execute(
            '''
            INSERT INTO DeliveryAddresses (customer_id, address, city, state, postal_code) 
            VALUES (?, ?, ?, ?, ?)
            ''',
            (
                get_jwt_identity()['id'],
                data['address'],
                data['city'],
                data['state'],
                data['postal_code']
            )
        )
        conn.commit()
    except Exception as e:
        conn.close()
        abort(500, description=f"Error saving delivery address: {str(e)}")
    conn.close()
    return jsonify({'message': 'Delivery address saved successfully'}), 201
