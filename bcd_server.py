from flask import Flask, request, jsonify
from pywebpush import webpush, WebPushException
from flask_cors import CORS
from dotenv import load_dotenv
from os import getenv
import json
import copy
import sqlite3

load_dotenv()

app = Flask(__name__)
CORS(app)

DATABASE = '/home/rpi/lullgo/databases/subscriptions.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This enables fetching rows as dictionary-like objects
    return conn


def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT UNIQUE NOT NULL,
                p256dh TEXT NOT NULL,
                auth TEXT NOT NULL
            )
        ''')
        conn.commit()


# Initialize the database when the app starts
with app.app_context():
    init_db()


@app.route('/api/save-subscription', methods=['POST'])
def save_subscscription():
    subscription = request.json
    endpoint = subscription.get('endpoint')
    keys = subscription.get('keys', {})
    p256dh = keys.get('p256dh')
    auth = keys.get('auth')

    if not all([endpoint, p256dh, auth]):
        return jsonify({"success": False, "message": "Missing subscription data"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO subscriptions (endpoint, p256dh, auth) VALUES (?, ?, ?)",
            (endpoint, p256dh, auth)
        )
        conn.commit()
        return jsonify({"success": True}), 200
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({"success": False, "message": "Subscription already exists"}), 409
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"Database error: {e}"}), 500
    finally:
        conn.close()


def send_notification():
    notification = {
        "title": "Your baby is crying!",
        "body": "It's time to soothe them!"
    }

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT endpoint, p256dh, auth FROM subscriptions")
    db_subscriptions = cursor.fetchall()
    conn.close()

    for sub_row in db_subscriptions:
        sub_info = {
            "endpoint": sub_row["endpoint"],
            "keys": {
                "p256dh": sub_row["p256dh"],
                "auth": sub_row["auth"]
            }
        }
        try:
            webpush(
                subscription_info=sub_info,
                data=json.dumps(notification),
                vapid_private_key=getenv("VAPID_PRIVATE_KEY"),
                vapid_claims={"sub": getenv("VAPID_CLAIMS_SUB")}
            )
        except WebPushException as e:
            print(f"Failed to send notification to {sub_info['endpoint']}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred for {sub_info['endpoint']}: {e}")


@app.route('/notify', methods=['POST'])
def trigger_notification():
    send_notification()
    return jsonify({"status": "Notification sent"}), 200


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000, ssl_context=('/home/rpi/lullgo/certs/rpi_local.crt', '/home/rpi/lullgo/certs/rpi_local.key'))
