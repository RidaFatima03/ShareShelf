# app/app.py
import os
from flask import Flask, session
import MySQLdb.cursors  
from extensions import mysql
from routes.auth import auth_bp
from routes.main import main_bp
from routes.admin import admin_bp
from routes.profile import profile_bp  # <--- NEW IMPORT
from routes.librarian import librarian_bp
from routes.copies import copies_bp
from routes.policy import policy_bp
from routes.request import request_bp

def create_app():
    app = Flask(__name__)

    app.secret_key = 'abcdefgh'

    # ---- EMAIL SMTP CONFIG ----
    app.config['SMTP_HOST'] = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    app.config['SMTP_PORT'] = int(os.environ.get('SMTP_PORT', 587))
    app.config['SMTP_USER'] = os.environ.get('SMTP_USER')
    app.config['SMTP_PASS'] = os.environ.get('SMTP_PASS')
    app.config['SMTP_FROM'] = os.environ.get('SMTP_FROM', app.config['SMTP_USER'])
    # ---------------------------

    # ---- MySQL CONFIG ----
    app.config['MYSQL_HOST'] = 'db'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'password'
    app.config['MYSQL_DB'] = 'shareshelfdb'
    # ----------------------

    mysql.init_app(app)
    

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(profile_bp)  # <--- NEW REGISTRATION
    app.register_blueprint(librarian_bp)
    app.register_blueprint(copies_bp)
    app.register_blueprint(policy_bp)
    app.register_blueprint(request_bp)

    return app

app = create_app()

@app.context_processor
def inject_notification_count_global():
    if 'loggedin' in session:
        user_id = session['userid']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT COUNT(*) AS count FROM Notification WHERE user_id = %s AND is_read = FALSE",
            (user_id,)
        )
        result = cursor.fetchone()
        count = result['count'] if result else 0
        return dict(unread_notifications_count=count)

    return dict(unread_notifications_count=0)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
