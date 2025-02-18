from flask import Blueprint, send_file, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.models import get_db_connection
import csv
import io

reports_bp = Blueprint('reports', __name__)

# Export order history as a CSV
@reports_bp.route('/api/reports/orders', methods=['GET'])
@jwt_required()
def export_order_history():
    """
    Export the user's order history as a CSV file.
    """
    conn = get_db_connection()
    try:
        orders = conn.execute(
            'SELECT * FROM Tickets WHERE customer_id = ?',
            (get_jwt_identity()['id'],)
        ).fetchall()
        if not orders:
            abort(404, description="No orders found")
    except Exception as e:
        conn.close()
        abort(500, description=f"Error fetching orders: {str(e)}")
    conn.close()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=orders[0].keys())
    writer.writeheader()
    writer.writerows([dict(row) for row in orders])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='order_history.csv'
    )

# Export billing history as a CSV
@reports_bp.route('/api/reports/bills', methods=['GET'])
@jwt_required()
def export_billing_history():
    """
    Export the user's billing history as a CSV file.
    """
    conn = get_db_connection()
    try:
        bills = conn.execute(
            'SELECT * FROM Tickets WHERE customer_id = ? AND payment > 0',
            (get_jwt_identity()['id'],)
        ).fetchall()
        if not bills:
            abort(404, description="No billing history found")
    except Exception as e:
        conn.close()
        abort(500, description=f"Error fetching billing history: {str(e)}")
    conn.close()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=bills[0].keys())
    writer.writeheader()
    writer.writerows([dict(row) for row in bills])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='billing_history.csv'
    )
