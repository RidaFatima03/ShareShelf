import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__) 

app.secret_key = 'abcdefgh'
  
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
    message = ''
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
            message = 'Logged in successfully!'
            return redirect(url_for('main_page'))
        else:
            message = 'Incorrect email or password!'
            
    return render_template('login.html', message=message)

@app.route('/register', methods =['GET', 'POST'])
def register():
    return render_template('register.html')

@app.route('/main', methods=['GET'])
def main_page():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
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

    return render_template('dashboard.html', books=books, view_title=view_title)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)