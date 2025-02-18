import os
import firebase_admin
from firebase_admin import credentials

### 🔹 Load Database Path
def get_db_path():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path = os.path.join(project_root, 'models', 'pos_system.db')
    return db_path

### 🔹 Firebase Setup
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")

if not FIREBASE_CREDENTIALS_PATH:
    raise ValueError("❌ FIREBASE_CREDENTIALS_PATH is not set. Make sure to add it as an environment variable.")

if FIREBASE_CREDENTIALS_PATH and not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)

### 🔹 Amazon SES Configuration
AWS_SES_USERNAME = os.getenv("AWS_SES_USERNAME")
AWS_SES_PASSWORD = os.getenv("AWS_SES_PASSWORD")
AWS_SES_SMTP_SERVER = os.getenv("AWS_SES_SMTP_SERVER", "email-smtp.us-east-2.amazonaws.com")  # Default to us-east-2
AWS_SES_SMTP_PORT = os.getenv("AWS_SES_SMTP_PORT")

if AWS_SES_SMTP_PORT:
    AWS_SES_SMTP_PORT = int(AWS_SES_SMTP_PORT)  # Convert to int if set
else:
    AWS_SES_SMTP_PORT = 587  # Default to 587 if not set

AWS_SES_SENDER_EMAIL = os.getenv("AWS_SES_SENDER_EMAIL")

### 🔹 Stripe API Keys
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")

# Ensure critical API keys are set
missing_env_vars = []

if not AWS_SES_USERNAME:
    missing_env_vars.append("AWS_SES_USERNAME")
if not AWS_SES_PASSWORD:
    missing_env_vars.append("AWS_SES_PASSWORD")
if not AWS_SES_SENDER_EMAIL:
    missing_env_vars.append("AWS_SES_SENDER_EMAIL")
if not STRIPE_SECRET_KEY:
    missing_env_vars.append("STRIPE_SECRET_KEY")

if missing_env_vars:
    raise ValueError(f"❌ Missing required environment variables: {', '.join(missing_env_vars)}. Please set them before running the application.")
