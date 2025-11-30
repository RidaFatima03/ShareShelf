import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import smtplib, ssl
from email.message import EmailMessage

app = Flask(__name__) 

app.secret_key = 'abcdefgh'

# ---- EMAIL SMTP CONFIG ----
app.config['SMTP_HOST'] = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
app.config['SMTP_PORT'] = int(os.environ.get('SMTP_PORT', 587))
app.config['SMTP_USER'] = os.environ.get('SMTP_USER')          # your email / SMTP username
app.config['SMTP_PASS'] = os.environ.get('SMTP_PASS')          # SMTP password / app password
app.config['SMTP_FROM'] = os.environ.get('SMTP_FROM', app.config['SMTP_USER'])
# ---------------------------
  
app.config['MYSQL_HOST'] = 'db'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'shareshelfdb'
  
mysql = MySQL(app)  

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        cursor.execute(
            'SELECT * FROM User WHERE user_email = %s AND user_password = SHA2(%s, 256)', 
            (email, password, )
        )
        user = cursor.fetchone()
        
        if user:              
            session['loggedin'] = True
            session['userid'] = user['user_id']
            session['username'] = user['user_first_name']
            session['user_type'] = user['user_type']   # 'Reader', 'Librarian', or 'Admin'

            flash('Logged in successfully!', 'success')
            return redirect(url_for('main_page'))
        else:
            flash('Incorrect email or password!', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods =['GET', 'POST'])
def register():
    return render_template('register.html')

@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/send_reset_link', methods=['POST'])
def send_reset_link():
    email = request.form.get('email')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

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
        reset_url = url_for('reset_password', token=token, _external=True)
        print("Password reset link:", reset_url)  # keep for debugging

        try:
            send_reset_email(email, reset_url)
        except Exception as e:
            # optional: log error, but don't reveal details to user
            print("Error sending reset email:", e)

    # Security: always show same message
    flash("If that email exists, we'll send a reset link.", "info")
    return redirect(url_for('login'))

def send_reset_email(to_email, reset_url):
    msg = EmailMessage()
    msg['Subject'] = 'Password reset instructions'
    msg['From'] = app.config['SMTP_FROM']
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

    with smtplib.SMTP(app.config['SMTP_HOST'], app.config['SMTP_PORT']) as server:
        server.starttls(context=context)
        server.login(app.config['SMTP_USER'], app.config['SMTP_PASS'])
        server.send_message(msg)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

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
            return render_template('reset_password.html', token=token)

        # Update User.user_password using same SHA2 logic as login
        cursor.execute("""
            UPDATE User
            SET user_password = SHA2(%s, 256)
            WHERE user_id = %s
        """, (new_password, user_id))

        # Mark token as used (make sure your table has this column)
        cursor.execute("""
            UPDATE PasswordResetToken
            SET used = 1
            WHERE token_id = %s
        """, (token,))

        mysql.connection.commit()

        flash("Your password has been reset. You can now log in.", "success")
        return redirect(url_for('login'))

    # GET: show the reset form
    return render_template('reset_password.html', token=token)

@app.route('/main', methods=['GET'])
def main_page():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    role = session.get('user_type')

    if role == 'Reader':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT is_approved FROM Reader WHERE reader_id = %s", (session['userid'],))
        r = cursor.fetchone()
        if not r or not r['is_approved']:
            return "Your reader account is awaiting approval.", 403

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    search_query = request.args.get('search_query')
    if search_query == "": search_query = None
    
    genre = request.args.get('genre')
    if genre == "": genre = None
    
    status_filter = request.args.get('status')
    if status_filter == "": status_filter = None

    language = request.args.get('language')
    if language == "": language = None
    
    min_rating = request.args.get('min_rating')
    if min_rating == "": min_rating = None

    if not any([search_query, genre, status_filter, language, min_rating]):
        query = """
        SELECT 
            b.book_id, 
            b.title, 
            b.average_rating,
            GROUP_CONCAT(DISTINCT a.author_name SEPARATOR ', ') AS authors,
            GROUP_CONCAT(DISTINCT g.genre_name SEPARATOR ', ') AS genres,
            SUM(CASE WHEN c.status = 'Available' THEN 1 ELSE 0 END) AS available_copies
        FROM (
            SELECT c.book_id, MAX(c.added_date) AS latest_added_date
            FROM Copy AS c
            GROUP BY c.book_id
        ) AS l
        JOIN Book AS b ON b.book_id = l.book_id
        LEFT JOIN Book_Author AS ba ON ba.book_id = b.book_id
        LEFT JOIN Author AS a ON a.author_id = ba.author_id
        LEFT JOIN Book_Genre AS bg ON bg.book_id = b.book_id
        LEFT JOIN Genre AS g ON g.genre_id = bg.genre_id
        LEFT JOIN Copy AS c ON c.book_id = b.book_id
        GROUP BY b.book_id, b.title, b.average_rating, l.latest_added_date
        ORDER BY l.latest_added_date DESC
        LIMIT 9;
        """
        cursor.execute(query)
        books = cursor.fetchall()
        view_title = "Recently Added Books"

    else:
        cursor.callproc('SearchBooks', (
            search_query,  # p_keyword
            None,          # p_title
            None,          # p_author
            None,          # p_isbn
            genre,         # p_genre
            language,      # p_language 
            status_filter, # p_availability
            None,          # p_acquisition
            min_rating,    # p_min_avg_rating  
            20,            # p_limit
            0              # p_offset
        ))
        books = cursor.fetchall()
        view_title = f"Search Results ({len(books)} Books)"

    return render_template('search.html', books=books, view_title=view_title)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)