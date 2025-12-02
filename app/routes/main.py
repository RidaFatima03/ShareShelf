# routes/main.py
from flask import Blueprint, render_template, request, redirect, url_for, session
import MySQLdb.cursors
from extensions import mysql

main_bp = Blueprint('main', __name__)

def get_cursor():
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)


@main_bp.route('/main', methods=['GET'], endpoint='main_page')
def main_page():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    role = session.get('user_type')

    if role == 'Reader':
        cursor = get_cursor()
        cursor.execute("SELECT is_approved FROM Reader WHERE reader_id = %s", (session['userid'],))
        r = cursor.fetchone()
        if not r or not r['is_approved']:
            return "Your reader account is awaiting approval.", 403

    cursor = get_cursor()
    
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
        LEFT JOIN Copy As c ON c.book_id = b.book_id
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

    return render_template('home.html', books=books, view_title=view_title)
