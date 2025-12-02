from flask import Blueprint, render_template, request, redirect, url_for, session
import MySQLdb.cursors
from extensions import mysql

main_bp = Blueprint('main', __name__)

def get_cursor():
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)

# 1. HOME PAGE (Clicking Logo) - Shows Recently Added
@main_bp.route('/main', methods=['GET'], endpoint='main_page')
def main_page():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = get_cursor()
    
    # Query for Recently Added Books (Limit 9)
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
    
    return render_template('home.html', books=books, view_title="Recently Added Books")


# 2. SEARCH PAGE (Clicking Library Search) - Shows Filters + Results
@main_bp.route('/library-search', methods=['GET'], endpoint='library-search')
def library_search():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))

    cursor = get_cursor()

    # Get Filters
    search_query = request.args.get('search_query') or None
    genre = request.args.get('genre') or None
    language = request.args.get('language') or None
    min_rating = request.args.get('min_rating') or None
    status_filter = request.args.get('status') or None

    # Call Stored Procedure
    cursor.callproc('SearchBooks', (
        search_query,  # p_keyword
        None, None, None, # title, author, isbn (unused)
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
    return render_template('library-search.html', books=books, view_title=view_title)

@main_bp.route('/my-checkouts', endpoint='my_checkouts')
def my_checkouts():
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    return render_template('my-checkouts.html')

@main_bp.route('/my-fines', endpoint='my_fines')
def my_fines():
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    return render_template('my-fines.html')

@main_bp.route('/my-requests', endpoint='my_requests')
def my_requests():
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    return render_template('my-requests.html')

@main_bp.route('/notifications', endpoint='notifications')
def notifications():
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    return render_template('notifications.html')

@main_bp.route('/book-details/<int:book_id>', endpoint='book_details')
def book_details(book_id):
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))

    cursor = get_cursor()

    query_book = """
        SELECT 
            b.book_id, b.title, b.isbn, b.publisher, b.publication_date, 
            b.language, b.physical_description, b.summary, b.average_rating,
            GROUP_CONCAT(DISTINCT a.author_name SEPARATOR ', ') AS authors,
            GROUP_CONCAT(DISTINCT g.genre_name SEPARATOR ', ') AS genres
        FROM Book b
        LEFT JOIN Book_Author ba ON b.book_id = ba.book_id
        LEFT JOIN Author a ON ba.author_id = a.author_id
        LEFT JOIN Book_Genre bg ON b.book_id = bg.book_id
        LEFT JOIN Genre g ON bg.genre_id = g.genre_id
        WHERE b.book_id = %s
        GROUP BY b.book_id
    """
    cursor.execute(query_book, (book_id,))
    book = cursor.fetchone()

    if not book:
        return "Book not found", 404

    query_copies = """
        SELECT 
            c.item_barcode, c.material_type, c.call_number, 
            l.direction, l.collection, l.shelf_row,
            c.status, c.acquisition_type
        FROM Copy c
        LEFT JOIN Location l ON c.location_id = l.location_id
        WHERE c.book_id = %s
    """
    cursor.execute(query_copies, (book_id,))
    copies = cursor.fetchall()

    available_count = sum(1 for copy in copies if copy['status'] == 'Available')

    return render_template('book-details.html', book=book, copies=copies, available_count=available_count)

@main_bp.route('/reviews/<int:book_id>', endpoint='reviews')
def reviews(book_id):
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = get_cursor()
    
    # Fetch book title to display on the page
    cursor.execute("SELECT title FROM Book WHERE book_id = %s", (book_id,))
    book = cursor.fetchone()
    
    if not book:
        return "Book not found", 404

    # (Optional: In the future, you can query actual reviews from the DB here)
    
    return render_template('reviews.html', book=book)