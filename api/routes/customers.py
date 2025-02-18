from flask import Blueprint, request, jsonify, abort
from api.models import get_db_connection

customers_bp = Blueprint('customers', __name__)

# Helper function for validation
def validate_customer_data(data):
    required_fields = ['first_name', 'last_name', 'phone_number']
    for field in required_fields:
        if field not in data or not data[field].strip():
            abort(400, description=f"Missing or invalid field: {field}")

# Get all customers
@customers_bp.route('/api/customers', methods=['GET'])
def get_customers():
    try:
        conn = get_db_connection()
        customers = conn.execute('SELECT * FROM customers').fetchall()
        conn.close()
        return jsonify([dict(row) for row in customers]), 200
    except Exception as e:
        return jsonify({'error': f"Internal Server Error: {str(e)}"}), 500

# Add a new customer
@customers_bp.route('/api/customers', methods=['POST'])
def add_customer():
    data = request.get_json()
    validate_customer_data(data)

    try:
        conn = get_db_connection()
        conn.execute(
            '''
            INSERT INTO customers (first_name, last_name, phone_number, notes, deladdress, billaddress, email, zipcode) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                data['first_name'].strip(),
                data['last_name'].strip(),
                data['phone_number'].strip(),
                data.get('notes', '').strip(),
                data.get('deladdress', '').strip(),
                data.get('billaddress', '').strip(),
                data.get('email', '').strip(),
                data.get('zipcode', '').strip()
            )
        )
        conn.commit()
        conn.close()
        return jsonify({'message': 'Customer added successfully'}), 201
    except Exception as e:
        return jsonify({'error': f"Internal Server Error: {str(e)}"}), 500

# Update an existing customer
@customers_bp.route('/api/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    data = request.get_json()
    validate_customer_data(data)

    try:
        conn = get_db_connection()
        result = conn.execute(
            '''
            UPDATE customers 
            SET first_name = ?, last_name = ?, phone_number = ?, notes = ?, deladdress = ?, billaddress = ?, email = ?, zipcode = ? 
            WHERE id = ?
            ''',
            (
                data['first_name'].strip(),
                data['last_name'].strip(),
                data['phone_number'].strip(),
                data.get('notes', '').strip(),
                data.get('deladdress', '').strip(),
                data.get('billaddress', '').strip(),
                data.get('email', '').strip(),
                data.get('zipcode', '').strip(),
                customer_id
            )
        )
        conn.commit()
        conn.close()

        if result.rowcount == 0:
            return jsonify({'error': 'Customer not found'}), 404

        return jsonify({'message': 'Customer updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': f"Internal Server Error: {str(e)}"}), 500

# Delete a customer
@customers_bp.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    try:
        conn = get_db_connection()
        result = conn.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
        conn.commit()
        conn.close()

        if result.rowcount == 0:
            return jsonify({'error': 'Customer not found'}), 404

        return jsonify({'message': 'Customer deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': f"Internal Server Error: {str(e)}"}), 500

@customers_bp.route('/api/customers/<int:customer_id>/total_owed', methods=['GET'])
def get_customer_total_owed(customer_id):
    try:
        conn = get_db_connection()
        total = conn.execute(
            '''
            SELECT SUM(total_price) as total_owed 
            FROM Tickets 
            WHERE customer_id = ? AND pickedup = 0
            ''',
            (customer_id,)
        ).fetchone()
        conn.close()
        return jsonify({'total_owed': total['total_owed'] if total['total_owed'] else 0}), 200
    except Exception as e:
        return jsonify({'error': f"Internal Server Error: {str(e)}"}), 500

@customers_bp.route('/api/customers/<int:customer_id>/tickets', methods=['GET'])
def get_customer_tickets(customer_id):
    try:
        conn = get_db_connection()

        # Extract query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status = request.args.get('status')
        ticket_type_id = request.args.get('type')
        page = max(1, int(request.args.get('page', 1)))
        per_page = max(1, int(request.args.get('per_page', 10)))

        # Base query
        query = 'SELECT * FROM Tickets WHERE customer_id = ?'
        params = [customer_id]

        # Apply filters
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
        total_count_query = 'SELECT COUNT(*) FROM Tickets WHERE customer_id = ?'
        total_count_params = [customer_id]

        if start_date:
            total_count_query += ' AND date_created >= ?'
            total_count_params.append(start_date)
        if end_date:
            total_count_query += ' AND date_created <= ?'
            total_count_params.append(end_date)
        if status:
            total_count_query += ' AND delivery_status = ?'
            total_count_params.append(status)
        if ticket_type_id:
            total_count_query += ' AND ticket_type_id = ?'
            total_count_params.append(ticket_type_id)

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
    except Exception as e:
        return jsonify({'error': f"Internal Server Error: {str(e)}"}), 500


