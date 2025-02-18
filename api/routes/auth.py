from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from api.models import get_db_connection
import sqlite3
from views.utils import hash_password, check_password

auth_bp = Blueprint('auth', __name__)

# Helper function to validate registration data
def validate_registration_data(data):
    required_fields = ['employee_name', 'password', 'display_name', 'phone_number', 'email']
    for field in required_fields:
        if field not in data:
            abort(400, description=f"Missing required field: {field}")

# Register a new employee
@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()

    # Validate input
    if not data or 'employee_name' not in data or 'password' not in data or 'display_name' not in data:
        abort(400, description="Employee name, password, and display name are required")

    # Normalize input
    employee_name = data['employee_name'].strip().lower()
    password = data['password']
    display_name = data['display_name'].strip()

    # Hash the password
    password_hash = hash_password(password)

    # Database connection
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Check if the employee already exists
        cursor.execute('SELECT 1 FROM Employees WHERE employee_name = ?', (employee_name,))
        if cursor.fetchone():
            abort(400, description="Employee name already exists")

        # Insert employee
        cursor.execute(
            'INSERT INTO Employees (employee_name, password_hash, display_name) VALUES (?, ?, ?)',
            (employee_name, password_hash, display_name)
        )
        conn.commit()

    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            abort(400, description=f"Employee name '{employee_name}' already exists.")
        abort(400, description=f"Database integrity error: {str(e)}")
    except Exception as e:
        abort(500, description=f"Database error: {str(e)}")
    finally:
        conn.close()

    return jsonify({'message': 'Employee registered successfully'}), 201

# Login
@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()

    # Validate input
    if not data or 'employee_name' not in data or 'password' not in data:
        abort(400, description="Employee name and password are required")

    employee_name = data['employee_name'].strip().lower()
    password = data['password']

    try:
        conn = get_db_connection()
        # Fetch employee record
        employee = conn.execute(
            'SELECT employee_id, password_hash FROM Employees WHERE employee_name = ?',
            (employee_name,)
        ).fetchone()
        conn.close()

        if employee:
            # Compare the plain text password with the stored hash
            if check_password(password, employee['password_hash']):
                # Create a token with employee_id as a string
                access_token = create_access_token(identity=str(employee['employee_id']))
                return jsonify({'access_token': access_token}), 200
            else:
                abort(401, description="Invalid credentials")
        else:
            abort(401, description="Invalid credentials")

    except Exception as e:
        print(f"Login error: {e}")  # Log error details for debugging
        abort(500, description=f"Internal Server Error: {str(e)}")

# Get account details
@auth_bp.route('/api/account', methods=['GET'])
@jwt_required()
def get_account():
    # Decode JWT identity
    user_id = get_jwt_identity()  # Ensure this returns the employee_id as a string

    try:
        conn = get_db_connection()
        # Fetch employee account using the decoded user_id
        account = conn.execute(
            'SELECT * FROM Employees WHERE employee_id = ?',
            (user_id,)
        ).fetchone()
        conn.close()

        if account:
            # Return account details as JSON
            return jsonify(dict(account)), 200
        else:
            abort(404, description="Account not found")
    except Exception as e:
        print(f"Error in /api/account: {e}")
        abort(500, description="Internal Server Error")

# Update account details
@auth_bp.route('/api/account', methods=['PUT'])
@jwt_required()
def update_account():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        abort(400, description="Request body is required")

    # Validate required fields for update
    required_fields = ['employee_name', 'display_name', 'phone_number', 'email']
    for field in required_fields:
        if field not in data:
            abort(400, description=f"Missing required field: {field}")

    try:
        # If password is provided, hash it
        if 'password' in data and data['password']:
            data['password_hash'] = hash_password(data['password'])

        conn = get_db_connection()
        conn.execute(
            '''
            UPDATE Employees 
            SET 
                employee_name = ?, 
                password_hash = COALESCE(?, password_hash), 
                display_name = ?, 
                phone_number = ?, 
                email = ? 
            WHERE employee_id = ?
            ''',
            (
                data['employee_name'],
                data.get('password_hash'),  # Update if provided
                data['display_name'],
                data['phone_number'],
                data['email'],
                user_id,
            )
        )
        conn.commit()
        conn.close()

        return jsonify({'message': 'Account updated successfully'}), 200
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            abort(400, description="Employee name already exists")
        abort(400, description=f"Database integrity error: {str(e)}")
    except Exception as e:
        print(f"Error in update_account: {e}")
        abort(500, description=f"Internal Server Error: {str(e)}")


def has_permission(employee_id, permission_name):
    conn = get_db_connection()

    # Check if the employee has a 'custom' role
    role = conn.execute(
        '''
        SELECT r.name
        FROM roles r
        JOIN employee_roles er ON r.id = er.role_id
        WHERE er.employee_id = ?
        ''', (employee_id,)
    ).fetchone()

    if role and role['name'] == 'custom':
        # Only check employee-specific permissions for custom roles
        employee_permissions = conn.execute(
            '''
            SELECT p.name
            FROM permissions p
            JOIN employee_permissions ep ON p.id = ep.permission_id
            WHERE ep.employee_id = ?
            ''', (employee_id,)
        ).fetchall()

        conn.close()
        # Check if the required permission exists
        return permission_name in {perm['name'] for perm in employee_permissions}

    # Otherwise, combine role permissions and employee-specific permissions
    employee_permissions = conn.execute(
        '''
        SELECT p.name
        FROM permissions p
        JOIN employee_permissions ep ON p.id = ep.permission_id
        WHERE ep.employee_id = ?
        ''', (employee_id,)
    ).fetchall()

    role_permissions = conn.execute(
        '''
        SELECT p.name
        FROM permissions p
        JOIN role_permissions rp ON p.id = rp.permission_id
        JOIN employee_roles er ON rp.role_id = er.role_id
        WHERE er.employee_id = ?
        ''', (employee_id,)
    ).fetchall()

    conn.close()

    # Combine all permissions
    all_permissions = {perm['name'] for perm in employee_permissions + role_permissions}

    # Check if the required permission exists
    return permission_name in all_permissions


@auth_bp.route('/api/account', methods=['DELETE'])
@jwt_required()
def delete_employee():
    current_employee = get_jwt_identity()
    data = request.get_json()

    if not data or 'employee_id' not in data:
        abort(400, description="Employee ID is required")

    try:
        employee_id_to_delete = int(data['employee_id'])

        # Prevent self-deletion
        if str(current_employee) == str(employee_id_to_delete):
            abort(403, description="You cannot delete your own account")

        conn = get_db_connection()
        # Check if the employee exists
        employee_to_delete = conn.execute(
            'SELECT * FROM Employees WHERE employee_id = ?',
            (employee_id_to_delete,)
        ).fetchone()

        if not employee_to_delete:
            conn.close()
            abort(404, description="Employee not found")

        # Perform deletion
        conn.execute('DELETE FROM Employees WHERE employee_id = ?', (employee_id_to_delete,))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Employee deleted successfully'}), 200
    except ValueError:
        abort(400, description="Invalid employee ID format")
    except Exception as e:
        print(f"Error in delete_employee: {e}")
        abort(500, description=f"Internal Server Error: {str(e)}")
