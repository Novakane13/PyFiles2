from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required

settings_bp = Blueprint('settings', __name__)

# Fetch app settings or configurations
@settings_bp.route('/api/settings', methods=['GET'])
@jwt_required()
def get_settings():
    """
    Fetch user-specific app settings.
    """
    # Example static settings; this could be enhanced by fetching from a database.
    settings = {
        "language": "English",
        "notifications": True,
        "dark_mode": False
    }
    return jsonify(settings), 200

# Update user language preference
@settings_bp.route('/api/settings/language', methods=['POST'])
@jwt_required()
def update_language():
    """
    Update the user's preferred language.
    """
    data = request.get_json()
    if 'language' not in data or not data['language']:
        abort(400, description="'language' is required")

    # Example logic for updating settings
    # Replace this with actual database updates as needed.
    return jsonify({'message': f"Language updated to {data['language']}"}), 200
