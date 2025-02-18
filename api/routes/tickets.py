from flask import Blueprint, request, jsonify, abort
from api.models import get_db_connection

tickets_bp = Blueprint('tickets', __name__)


# Helper function for ticket data validation
def validate_ticket_data(data, required_fields=None):
    """
    Validate the incoming ticket data for required fields.
    """
    if required_fields is None:
        required_fields = [
            'customer_id', 'ticket_type_id', 'employee_id', 'ticket_number',
            'total_price', 'date_created', 'date_due'
        ]
    for field in required_fields:
        if field not in data or data[field] is None:
            abort(400, description=f"Missing required field: {field}")


# Get all tickets with optional filters and pagination
@tickets_bp.route('/api/tickets', methods=['GET'])
def get_tickets():
    """
    Fetch all tickets with optional filters and pagination.
    """
    conn = get_db_connection()

    # Extract query parameters
    customer_id = request.args.get('customer_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status')
    ticket_type_id = request.args.get('type')
    page = max(1, int(request.args.get('page', 1)))
    per_page = max(1, int(request.args.get('per_page', 10)))

    # Base query
    query = 'SELECT * FROM Tickets WHERE 1=1'
    params = []

    # Apply filters
    if customer_id:
        query += ' AND customer_id = ?'
        params.append(customer_id)
    if start_date:
        query += ' AND date_created >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND date_created <= ?'
        params.append(end_date)
    if status:
        query += ' AND delivery_status = ?'
        params.append(status)
    if ticket_type_id:
        query += ' AND ticket_type_id = ?'
        params.append(ticket_type_id)

    # Add pagination
    query += ' LIMIT ? OFFSET ?'
    params.extend([per_page, (page - 1) * per_page])

    tickets = conn.execute(query, params).fetchall()

    # Fetch total count for pagination metadata
    total_count_query = 'SELECT COUNT(*) FROM Tickets WHERE 1=1'
    total_count_params = params[:-2]  # Exclude pagination params
    total_count = conn.execute(total_count_query, total_count_params).fetchone()[0]
    conn.close()

    return jsonify({
        'tickets': [dict(row) for row in tickets],
        'pagination': {
            'current_page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page,
            'total_items': total_count
        }
    }), 200


# Get a specific ticket by ID
@tickets_bp.route('/api/tickets/<int:ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    """
    Fetch detailed information for a specific ticket.
    """
    conn = get_db_connection()
    ticket = conn.execute('SELECT * FROM Tickets WHERE id = ?', (ticket_id,)).fetchone()
    conn.close()
    if not ticket:
        abort(404, description="Ticket not found")
    return jsonify(dict(ticket)), 200


# Add a new ticket
@tickets_bp.route('/api/tickets', methods=['POST'])
def add_ticket():
    """
    Add a new ticket to the database.
    """
    data = request.get_json()
    validate_ticket_data(data)

    conn = get_db_connection()
    conn.execute(
        '''
        INSERT INTO Tickets 
        (customer_id, ticket_type_id, employee_id, ticket_number, total_price,
         date_created, date_due, location, pieces, payment, pickedup, payment_type,
         is_detailed, parent_ticket_number, notes, allnotes, delivery_status) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            data['customer_id'], data['ticket_type_id'], data['employee_id'],
            data['ticket_number'], data['total_price'], data['date_created'],
            data['date_due'], data.get('location', ''), data.get('pieces', 0),
            data.get('payment', 0), data.get('pickedup', 0), data.get('payment_type', ''),
            data.get('is_detailed', 0), data.get('parent_ticket_number', ''),
            data.get('notes', ''), data.get('allnotes', ''),
            data.get('delivery_status', 'Pending')
        )
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Ticket added successfully'}), 201


# Update an existing ticket
@tickets_bp.route('/api/tickets/<int:ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    """
    Update an existing ticket by ID.
    """
    data = request.get_json()
    validate_ticket_data(data, required_fields=[
        'customer_id', 'ticket_type_id', 'employee_id',
        'ticket_number', 'total_price', 'date_due'
    ])

    conn = get_db_connection()
    conn.execute(
        '''
        UPDATE Tickets 
        SET customer_id = ?, ticket_type_id = ?, employee_id = ?, ticket_number = ?, 
            total_price = ?, date_due = ?, notes = ?, allnotes = ?, delivery_status = ? 
        WHERE id = ?
        ''',
        (
            data['customer_id'], data['ticket_type_id'], data['employee_id'],
            data['ticket_number'], data['total_price'], data['date_due'],
            data.get('notes', ''), data.get('allnotes', ''),
            data.get('delivery_status', 'Pending'), ticket_id
        )
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Ticket updated successfully'}), 200


# Delete a ticket
@tickets_bp.route('/api/tickets/<int:ticket_id>', methods=['DELETE'])
def delete_ticket(ticket_id):
    """
    Delete a ticket by ID.
    """
    conn = get_db_connection()
    conn.execute('DELETE FROM Tickets WHERE id = ?', (ticket_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Ticket deleted successfully'}), 200


# Get the current delivery status of a specific ticket
@tickets_bp.route('/api/tickets/<int:ticket_id>/delivery_status', methods=['GET'])
def get_ticket_delivery_status(ticket_id):
    """
    Fetch the delivery status of a specific ticket.
    """
    conn = get_db_connection()
    status = conn.execute(
        'SELECT delivery_status FROM Tickets WHERE id = ?',
        (ticket_id,)
    ).fetchone()
    conn.close()
    if not status:
        abort(404, description="Ticket not found")
    return jsonify({'ticket_id': ticket_id, 'delivery_status': status['delivery_status']}), 200


# Update the delivery status of a specific ticket
@tickets_bp.route('/api/tickets/<int:ticket_id>/delivery_status', methods=['PATCH'])
def update_ticket_delivery_status(ticket_id):
    data = request.get_json()
    if 'delivery_status' not in data:
        abort(400, description="Missing required field: delivery_status")

    conn = get_db_connection()
    conn.execute(
        'UPDATE Tickets SET delivery_status = ? WHERE id = ?',
        (data['delivery_status'], ticket_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'Delivery status updated successfully'}), 200
