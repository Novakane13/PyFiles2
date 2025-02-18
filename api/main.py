import os
import sys
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
os.chdir(project_root)  



if project_root not in sys.path:
    sys.path.append(project_root)

from api.routes.auth import auth_bp
from api.routes.customers import customers_bp
from api.routes.tickets import tickets_bp
from api.routes.payments import payments_bp
from api.routes.deliveries import deliveries_bp
from api.routes.notifications import notifications_bp
from api.routes.messages import messages_bp
from api.routes.credit_cards import credit_cards_bp
from api.routes.reports import reports_bp
from api.routes.settings import settings_bp

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = '9f823c4a8d8f45e292e8a6bdfb6721e5c4e9bb78db61471e24ef99bce12b3c45'  # Replace with a secure key
CORS(app, resources={r"/*": {"origins": "https://your-app-domain.com"}})

CORS(app)
jwt = JWTManager(app)

app.register_blueprint(auth_bp)
app.register_blueprint(customers_bp)
app.register_blueprint(tickets_bp)
app.register_blueprint(payments_bp)
app.register_blueprint(deliveries_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(messages_bp)
app.register_blueprint(credit_cards_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(settings_bp)

if __name__ == '__main__':
    app.run(debug=True)
