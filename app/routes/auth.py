# routes/auth.py
import smtplib, ssl
from email.message import EmailMessage

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, flash, current_app
)
import MySQLdb.cursors

from extensions import mysql

auth_bp = Blueprint('auth', __name__)

def get_cursor():
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)


@auth_bp.route('/', endpoint='index')
def index():
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'], endpoint='login')
def login():
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']

        cursor = get_cursor()
        cursor.execute(
            'SELECT * FROM User WHERE user_email = %s AND user_password = SHA2(%s, 256)',
            (email, password,)
        )
        user = cursor.fetchone()

        if user:
            session['loggedin'] = True
            session['userid'] = user['user_id']

            if user['user_middle_name'].strip() == '':
                session['username'] = user['user_first_name'] + ' ' + user['user_last_name']
            else:
                session['username'] = (
                    user['user_first_name'] + ' ' +
                    user['user_middle_name'] + ' ' +
                    user['user_last_name']
                )

            session['user_type'] = user['user_type']   # 'Reader', 'Librarian', or 'Admin'

            user_log_activity(
                session['userid'],
                'Login',
                f"{session['user_type']} {session['username']} logged in."
            )

            return redirect(url_for('main.main_page'))
        else:
            flash('Incorrect email or password!', 'danger')
            return redirect(url_for('auth.login'))

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'], endpoint='register')
def register():
    message = ''
    if request.method == 'POST' :
        user_first_name = request.form['user_first_name']
        user_middle_name = request.form['user_middle_name']
        user_last_name = request.form['user_last_name']
        user_password = request.form['user_password']
        user_phone_number = request.form['user_phone_number']
        user_email = request.form['user_email']
    
  
        if not user_first_name or not user_middle_name or not user_last_name or not user_password or not user_phone_number or not user_email:
            message = 'Please fill out the form!'
            return render_template('register.html', message=message)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        cursor.execute('SELECT * FROM User WHERE user_email = %s', (user_email,))
        user_email_exists = cursor.fetchone()

        if user_email_exists:
            message = 'Email already used! Please use a different one.'
            return render_template('register.html', message=message)

        
        cursor.execute('INSERT INTO User (user_first_name, user_middle_name, user_last_name, user_phone_number, user_email, user_password) ' \
        '     VALUES (% s, %s, %s, %s, %s, %s)',
             (user_first_name, user_middle_name, user_last_name, user_phone_number, user_email, user_password))
        mysql.connection.commit()
        message = 'User successfully created!'
        return render_template('login.html', message = message)

    return render_template('register.html', message = message)

@auth_bp.route('/reset_password', endpoint='reset_password')
def reset_password():
    return render_template('reset_password.html')


@auth_bp.route('/send_reset_link', methods=['POST'], endpoint='send_reset_link')
def send_reset_link():
    email = request.form.get('email')

    cursor = get_cursor()

    # 1) Check if email exists and get user_id
    cursor.execute("SELECT user_id FROM User WHERE user_email = %s", (email,))
    row = cursor.fetchone()

    if row:
        user_id = row['user_id']

        # 2) Generate token in DB using SHA2(UUID(), 256)
        cursor.execute("SELECT SHA2(UUID(), 256) AS token")
        token_row = cursor.fetchone()
        token = token_row['token']

        # 3) Insert into PasswordResetToken with 30 min expiry
        cursor.execute("""
            INSERT INTO PasswordResetToken (token_id, user_id, expires_at, used)
            VALUES (%s, %s, DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 30 MINUTE), 0)
        """, (token, user_id))

        mysql.connection.commit()

        # 4) Build reset URL and send it by email
        reset_url = url_for('auth.change_password', token=token, _external=True)
        print("Password reset link:", reset_url)  # keep for debugging

        try:
            send_reset_email(email, reset_url)
        except Exception as e:
            print("Error sending reset email:", e)

    flash("If that email exists, we'll send a reset link.", "info")
    return redirect(url_for('auth.login'))


def send_reset_email(to_email, reset_url):
    msg = EmailMessage()
    msg['Subject'] = 'Password reset instructions'
    msg['From'] = current_app.config['SMTP_FROM']
    msg['To'] = to_email

    msg.set_content(f"""\
Hi,

We received a request to reset the password for your account.

Click the link below to reset your password (valid for 30 minutes):

{reset_url}

If you did not request this, you can ignore this email.

Thanks.
""")

    context = ssl.create_default_context()

    with smtplib.SMTP(current_app.config['SMTP_HOST'], current_app.config['SMTP_PORT']) as server:
        server.starttls(context=context)
        server.login(current_app.config['SMTP_USER'], current_app.config['SMTP_PASS'])
        server.send_message(msg)


@auth_bp.route('/change_password/<token>', methods=['GET', 'POST'], endpoint='change_password')
def change_password(token):
    cursor = get_cursor()

    # Check if token exists, not expired, and not used
    cursor.execute("""
        SELECT pr.user_id, u.user_email
        FROM PasswordResetToken pr
        JOIN User u ON u.user_id = pr.user_id
        WHERE pr.token_id = %s
          AND pr.expires_at > CURRENT_TIMESTAMP
          AND pr.used = 0
    """, (token,))
    row = cursor.fetchone()

    if not row:
        return "Invalid or expired reset link.", 400

    user_id = row['user_id']

    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not new_password or new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('change_password.html', token=token)

        cursor.execute("""
            UPDATE User
            SET user_password = SHA2(%s, 256)
            WHERE user_id = %s
        """, (new_password, user_id))

        cursor.execute("""
            UPDATE PasswordResetToken
            SET used = 1
            WHERE token_id = %s
        """, (token,))

        mysql.connection.commit()

        flash("Your password has been reset. You can now log in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('change_password.html', token=token)


@auth_bp.route('/logout', endpoint='logout')
def logout():
    if 'userid' in session:
        user_log_activity(
            session['userid'],
            'Logout',
            f"{session.get('user_type', '')} {session.get('username', '')} logged out."
        )
    session.clear()
    return redirect(url_for('auth.login'))


def user_log_activity(user_id, action_type, details):
    cursor = get_cursor()
    cursor.execute(
        '''
        INSERT INTO user_activity_log (action_type, details, user_id)
        VALUES (%s, %s, %s)
        ''',
        (action_type, details, user_id)
    )
    mysql.connection.commit()
