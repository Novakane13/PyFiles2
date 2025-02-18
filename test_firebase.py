from views.utils import send_firebase_notification, get_customer_fcm_token

customer_id = 1  # Replace with your test customer ID

# Fetch the customer's FCM token
fcm_token = get_customer_fcm_token(customer_id)

# Send a test notification
if fcm_token:
    send_firebase_notification(fcm_token, "Test Notification", "Your order is ready for pickup!")
else:
    print("❌ No FCM token found for this customer.")
