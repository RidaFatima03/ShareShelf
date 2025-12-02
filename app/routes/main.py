from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta
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
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['userid']
    cursor = get_cursor()

    query_current = """
        SELECT 
            b.title, 
            c.due_date, 
            c.renew_count,
            c.checkout_id,
            GROUP_CONCAT(DISTINCT a.author_name SEPARATOR ', ') AS authors
        FROM Checkout c
        JOIN Copy y ON c.copy_id = y.item_barcode
        JOIN Book b ON y.book_id = b.book_id
        LEFT JOIN Book_Author ba ON b.book_id = ba.book_id
        LEFT JOIN Author a ON ba.author_id = a.author_id
        WHERE c.reader_id = %s AND c.returned_date IS NULL
        GROUP BY c.checkout_id, b.title, c.due_date, c.renew_count
        ORDER BY c.due_date ASC;
    """
    cursor.execute(query_current, (user_id,))
    current_checkouts = cursor.fetchall()

    query_history = """
        SELECT 
            b.title, 
            c.checkout_date, 
            c.returned_date,
            GROUP_CONCAT(DISTINCT a.author_name SEPARATOR ', ') AS authors
        FROM Checkout c
        JOIN Copy y ON c.copy_id = y.item_barcode
        JOIN Book b ON y.book_id = b.book_id
        LEFT JOIN Book_Author ba ON b.book_id = ba.book_id
        LEFT JOIN Author a ON ba.author_id = a.author_id
        WHERE c.reader_id = %s AND c.returned_date IS NOT NULL
        GROUP BY c.checkout_id, b.title, c.checkout_date, c.returned_date
        ORDER BY c.returned_date DESC;
    """
    cursor.execute(query_history, (user_id,))
    history = cursor.fetchall()

    return render_template('my-checkouts.html', current_checkouts=current_checkouts, history=history)

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

@main_bp.route('/reviews/<int:book_id>', methods=['GET', 'POST'], endpoint='reviews')
def reviews(book_id):
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = get_cursor()
    user_id = session['userid']

    cursor.execute("SELECT review_id FROM Review WHERE reader_id = %s AND book_id = %s", (user_id, book_id))
    existing_review = cursor.fetchone()
    has_reviewed = True if existing_review else False

    if request.method == 'POST':
        if has_reviewed:
            flash("You have already reviewed this book.", "warning")
            return redirect(url_for('main.reviews', book_id=book_id))

        rating = request.form.get('rating')
        comment = request.form.get('comment')
        
        if not rating or not comment:
            flash("Please provide both a rating and a comment.", "warning")
        else:
            try:
                cursor.execute("""
                    INSERT INTO Review (rating, review_text, created_date, reader_id, book_id)
                    VALUES (%s, %s, NOW(), %s, %s)
                """, (rating, comment, user_id, book_id))
                mysql.connection.commit()
                flash("Review submitted successfully!", "success")
                return redirect(url_for('main.reviews', book_id=book_id))
                
            except Exception as e:
                mysql.connection.rollback()
                flash(f"Error submitting review: {str(e)}", "danger")

    cursor.execute("SELECT book_id, title FROM Book WHERE book_id = %s", (book_id,))
    book = cursor.fetchone()
    
    if not book:
        return "Book not found", 404

    query_reviews = """
        SELECT 
            r.rating, 
            r.review_text, 
            r.created_date,
            u.user_first_name, 
            u.user_last_name
        FROM Review r
        JOIN Reader rd ON r.reader_id = rd.reader_id
        JOIN User u ON rd.reader_id = u.user_id
        WHERE r.book_id = %s
        ORDER BY r.created_date DESC
    """
    cursor.execute(query_reviews, (book_id,))
    reviews_list = cursor.fetchall()

    return render_template('reviews.html', book=book, reviews=reviews_list, has_reviewed=has_reviewed)
@main_bp.route('/borrow/<string:copy_id>', methods=['POST'], endpoint='borrow_book')
def borrow_book(copy_id):
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['userid']
    cursor = get_cursor()

    try:
        cursor.execute("SELECT book_id, status FROM Copy WHERE item_barcode = %s", (copy_id,))
        copy_data = cursor.fetchone()

        if not copy_data:
            flash("Error: Copy not found.", "danger")
            return redirect(request.referrer)

        book_id = copy_data['book_id']

        check_loan_query = """
            SELECT c.checkout_id 
            FROM Checkout c
            JOIN Copy cp ON c.copy_id = cp.item_barcode
            WHERE c.reader_id = %s 
              AND cp.book_id = %s 
              AND c.returned_date IS NULL
        """
        cursor.execute(check_loan_query, (user_id, book_id))
        existing_loan = cursor.fetchone()

        if existing_loan:
            flash("You already have a copy of this book checked out.", "warning")
            return redirect(request.referrer)

        if copy_data['status'] != 'Available':
            flash("Error: This copy is no longer available.", "danger")
            return redirect(request.referrer)

        due_date = datetime.now() + timedelta(days=14)
        
        insert_query = """
            INSERT INTO Checkout (checkout_date, due_date, reader_id, copy_id)
            VALUES (NOW(), %s, %s, %s)
        """
        cursor.execute(insert_query, (due_date, user_id, copy_id))

        update_query = "UPDATE Copy SET status = 'On Loan' WHERE item_barcode = %s"
        cursor.execute(update_query, (copy_id,))

        mysql.connection.commit()
        flash(f"Successfully borrowed copy {copy_id}. Due: {due_date.strftime('%Y-%m-%d')}", "success")

    except Exception as e:
        mysql.connection.rollback()
        print("Borrow Error:", e)
        flash("An error occurred while borrowing.", "danger")

    return redirect(request.referrer or url_for('main.main_page'))


@main_bp.route('/hold/<int:book_id>', methods=['POST'], endpoint='hold_book')
def hold_book(book_id):
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['userid']
    cursor = get_cursor()

    try:
        check_loan_query = """
            SELECT c.checkout_id 
            FROM Checkout c
            JOIN Copy cp ON c.copy_id = cp.item_barcode
            WHERE c.reader_id = %s 
              AND cp.book_id = %s 
              AND c.returned_date IS NULL
        """
        cursor.execute(check_loan_query, (user_id, book_id))
        existing_loan = cursor.fetchone()

        if existing_loan:
            flash("You cannot place a hold on a book you currently have checked out.", "warning")
            return redirect(request.referrer)

        check_hold_query = """
            SELECT request_id FROM Request 
            WHERE reader_id = %s AND book_id = %s 
            AND request_type = 'Hold' AND status IN ('Pending', 'Approved')
        """
        cursor.execute(check_hold_query, (user_id, book_id))
        existing_hold = cursor.fetchone()

        if existing_hold:
            flash("You already have an active hold on this book.", "warning")
        else:
            insert_query = """
                INSERT INTO Request (request_date, request_type, status, reader_id, book_id)
                VALUES (NOW(), 'Hold', 'Pending', %s, %s)
            """
            cursor.execute(insert_query, (user_id, book_id))
            mysql.connection.commit()
            flash("Hold placed successfully!", "success")

    except Exception as e:
        mysql.connection.rollback()
        print("Hold Error:", e)
        flash("An error occurred while placing hold.", "danger")

    return redirect(request.referrer or url_for('main.main_page'))