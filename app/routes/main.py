from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
import MySQLdb.cursors
from extensions import mysql
from routes.notifications import NotificationService
from utils.system_log import system_log

main_bp = Blueprint('main', __name__)

def get_cursor():
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)

def notify_librarians(subject, details):
    cursor = get_cursor()
    cursor.execute("SELECT user_id FROM User WHERE user_type = 'Librarian'")
    librarians = cursor.fetchall()
    service = NotificationService(mysql.connection)
    for librarian in librarians:
        service.add_notification(librarian["user_id"], subject, details)

@main_bp.route('/main', methods=['GET'], endpoint='main_page')
def main_page():
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    
    cursor = get_cursor()
    
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
        WHERE c.acquisition_type != 'Exchange'  -- [FILTER 1] Exclude Exchange from recent list
        GROUP BY c.book_id
    ) AS l
    JOIN Book AS b ON b.book_id = l.book_id
    LEFT JOIN Book_Author AS ba ON ba.book_id = b.book_id
    LEFT JOIN Author AS a ON a.author_id = ba.author_id
    LEFT JOIN Book_Genre AS bg ON bg.book_id = b.book_id
    LEFT JOIN Genre AS g ON g.genre_id = bg.genre_id
    LEFT JOIN Copy AS c ON c.book_id = b.book_id AND c.acquisition_type != 'Exchange' -- [FILTER 2] Exclude from counts
    GROUP BY b.book_id, b.title, b.average_rating, l.latest_added_date
    ORDER BY l.latest_added_date DESC
    LIMIT 9;
    """
    cursor.execute(query)
    books = cursor.fetchall()
    
    return render_template('home.html', books=books, view_title="Recently Added Books")

@main_bp.route('/library-search', methods=['GET'], endpoint='library-search')
def library_search():
    if 'loggedin' not in session: return redirect(url_for('auth.login'))

    cursor = get_cursor()

    search_query = request.args.get('search_query') or None
    genre = request.args.get('genre') or None
    language = request.args.get('language') or None
    min_rating = request.args.get('min_rating') or None
    status_filter = request.args.get('status') or None
    
    acquisition = request.args.get('acquisition') or None

    cursor.callproc('SearchBooks', (
        search_query,  # p_keyword
        None, None, None, # title, author, isbn (unused)
        genre,         # p_genre
        language,      # p_language
        status_filter, # p_availability
        acquisition,   # [CHANGED] Pass the variable here (was None)
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
    show_payment = request.args.get('pay')
    success = request.args.get('success')
    
    if 'loggedin' not in session: return redirect(url_for('auth.login'))

    cursor = get_cursor()
    user_id = session['userid']
    
    # Outstanding fines
    cursor.execute("""
        SELECT f.*
        FROM Fine f
        JOIN Checkout c ON f.checkout_id = c.checkout_id
        WHERE f.status != 'Paid'
            AND c.reader_id = %s
    """, (user_id,))
    outstanding_fines = cursor.fetchall()

    # Payment history
    cursor.execute("""
        SELECT f.*
        FROM Fine f
        JOIN Checkout c ON f.checkout_id = c.checkout_id
        WHERE f.status = 'Paid'
            AND c.reader_id = %s
    """, (user_id,))
    paid_fines = cursor.fetchall()

    cursor.close()
    
    return render_template(
        'my-fines.html',
        show_payment=show_payment,
        success=success,
        outstanding_fines=outstanding_fines,
        paid_fines=paid_fines
    )

@main_bp.route('/notifications', endpoint='notifications')
def notifications():
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    user_id = session['userid']
    cursor = get_cursor()
    
    query = """
        SELECT notification_id, subject, details, notification_date, is_read
        FROM Notification
        WHERE user_id = %s
        ORDER BY notification_date DESC
    """

    cursor.execute(query, (user_id,))
    notifs = cursor.fetchall()
    
    return render_template('notifications.html', notifications=notifs)

@main_bp.route('/mark-notification-read/<int:notification_id>', methods=['POST'], endpoint='mark_notification_read')
def mark_notification_read(notification_id):
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    
    cursor = get_cursor()
    cursor.execute("UPDATE Notification SET is_read = TRUE WHERE notification_id = %s", (notification_id,))
    mysql.connection.commit()
    
    return redirect(url_for('main.notifications'))

@main_bp.route('/book-details/<int:book_id>', endpoint='book_details')
def book_details(book_id):
    if 'loggedin' not in session: return redirect(url_for('auth.login'))

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

    if not book: return "Book not found", 404

    query_copies = """
        SELECT 
            c.item_barcode, c.material_type, c.call_number, 
            l.direction, l.collection, l.shelf_row,
            c.status, c.acquisition_type
        FROM Copy c
        LEFT JOIN Location l ON c.location_id = l.location_id
        WHERE c.book_id = %s AND c.acquisition_type != 'Exchange'
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
                system_log("Reviews", "ERROR", "ReviewService", f"Review submission failed: {e}")
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
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    user_id = session['userid']
    cursor = get_cursor()

    try:
        cursor.execute("SELECT book_id, status FROM Copy WHERE item_barcode = %s", (copy_id,))
        copy_data = cursor.fetchone()

        if not copy_data:
            flash("Error: Copy not found.", "danger")
            return redirect(request.referrer)

        cursor.execute("""
            SELECT request_id FROM Request 
            WHERE reader_id = %s AND book_id = %s AND request_type = 'Borrow'
              AND status IN ('Pending', 'Approved')
        """, (user_id, copy_data['book_id']))
        
        if cursor.fetchone():
            flash("You already have an active borrow request for this book.", "warning")
            return redirect(request.referrer)

        cursor.execute("""
            INSERT INTO Request (request_date, expire_date, request_type, status, reader_id, book_id)
            VALUES (NOW(), DATE_ADD(NOW(), INTERVAL 14 DAY), 'Borrow', 'Pending', %s, %s)
        """, (user_id, copy_data['book_id']))
        request_id = cursor.lastrowid

        mysql.connection.commit()
        cursor.execute("""
            SELECT CONCAT_WS(' ', user_first_name, user_middle_name, user_last_name) AS full_name
            FROM User
            WHERE user_id = %s
        """, (user_id,))
        user_row = cursor.fetchone() or {}
        cursor.execute("SELECT title FROM Book WHERE book_id = %s", (copy_data['book_id'],))
        book_row = cursor.fetchone() or {}
        user_full_name = user_row.get("full_name") or f"User {user_id}"
        book_title = book_row.get("title") or f"book {copy_data['book_id']}"
        notify_librarians(
            "New borrow request",
            f"User {user_full_name} created a request to borrow {book_title}."
        )
        system_log(
            "Requests",
            "INFO",
            "RequestService",
            f"Borrow request created (request_id={request_id}, book_id={copy_data['book_id']})."
        )
        flash("Borrow request sent to Librarian for approval.", "success")

    except Exception as e:
        mysql.connection.rollback()
        system_log("Requests", "ERROR", "RequestService", f"Borrow request failed: {e}")
        flash(f"Error sending request: {str(e)}", "danger")

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
                INSERT INTO Request (request_date, expire_date, request_type, status, reader_id, book_id)
                VALUES (NOW(), NULL, 'Hold', 'Pending', %s, %s)
            """
            cursor.execute(insert_query, (user_id, book_id))
            cursor.execute("""
                SELECT CONCAT_WS(' ', user_first_name, user_middle_name, user_last_name) AS full_name
                FROM User
                WHERE user_id = %s
            """, (user_id,))
            user_row = cursor.fetchone() or {}
            
            cursor.execute("SELECT title FROM Book WHERE book_id = %s", (book_id,))
            book_row = cursor.fetchone() or {}
            
            user_full_name = user_row.get("full_name") or f"User {user_id}"
            book_title = book_row.get("title") or f"book {book_id}"

            request_id = cursor.lastrowid
            mysql.connection.commit()

            notify_librarians(
            "New hold request",
            f"User {user_full_name} created a request to hold {book_title}."
            )
            system_log(
                "Requests",
                "INFO",
                "RequestService",
                f"Hold request created (request_id={request_id}, book_id={book_id})."
            )
            flash("Hold placed successfully!", "success")

    except Exception as e:
        mysql.connection.rollback()
        system_log("Requests", "ERROR", "RequestService", f"Hold request failed: {e}")
        print("Hold Error:", e)
        flash("An error occurred while placing hold.", "danger")

    return redirect(request.referrer or url_for('main.main_page'))

@main_bp.route('/add-book', methods=['POST'], endpoint='add_book')
def add_book():
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    user_id = session['userid']
    cursor = get_cursor()
    
    acquisition_type = request.form.get('type')  
    mode = request.form.get('mode') 
    
    try:
        if acquisition_type == 'Donation':
            request_id = None
            if mode == 'existing':
                book_id = request.form.get('book_id')
                cursor.execute("""
                    SELECT request_id FROM Request
                    WHERE reader_id = %s AND book_id = %s AND request_type = 'Donation'
                      AND status IN ('Pending', 'Approved')
                """, (user_id, book_id))
                if cursor.fetchone():
                    flash("You already have an active donation request for this book.", "warning")
                    return redirect(request.referrer)

                cursor.execute("""
                    INSERT INTO Request (request_date, expire_date, request_type, status, reader_id, book_id) 
                    VALUES (NOW(), DATE_ADD(NOW(), INTERVAL 14 DAY), 'Donation', 'Pending', %s, %s)
                """, (user_id, book_id))
                request_id = cursor.lastrowid
                
            elif mode == 'manual':
                isbn = request.form.get('isbn')
                title = request.form.get('title')
                author = request.form.get('author')
                publisher = request.form.get('publisher')
                
                cursor.execute("SELECT material_id FROM Material WHERE isbn = %s", (isbn,))
                existing_material = cursor.fetchone()
                
                if existing_material:
                    material_id = existing_material['material_id']
                else:
                    cursor.execute("""
                        INSERT INTO Material (isbn, title, publisher, author, publication_date)
                        VALUES (%s, %s, %s, %s, NOW())
                    """, (isbn, title, publisher, author))
                    material_id = cursor.lastrowid
                
                cursor.execute("""
                    INSERT INTO Request (request_date, expire_date, request_type, status, reader_id, material_id) 
                    VALUES (NOW(), DATE_ADD(NOW(), INTERVAL 14 DAY), 'Donation', 'Pending', %s, %s)
                """, (user_id, material_id))
                request_id = cursor.lastrowid
            
            mysql.connection.commit()
            cursor.execute("""
                SELECT CONCAT_WS(' ', user_first_name, user_middle_name, user_last_name) AS full_name
                FROM User WHERE user_id = %s
            """, (user_id,))
            user_row = cursor.fetchone() or {}
            user_full_name = user_row.get("full_name") or f"User {user_id}"

            notify_librarians(
                "New donation request",
                f"{user_full_name} submitted a donation request."
            )

            if request_id:
                if mode == "existing":
                    system_log(
                        "Requests",
                        "INFO",
                        "RequestService",
                        f"Donation request created (request_id={request_id}, book_id={book_id})."
                    )
                else:
                    system_log(
                        "Requests",
                        "INFO",
                        "RequestService",
                        f"Donation request created (request_id={request_id}, material_id={material_id})."
                    )
            flash("Donation request sent to Librarian for approval.", "success")
            return redirect(url_for('request.my_requests')) 

        elif acquisition_type == 'Exchange':
            book_id = None
            
            if mode == 'existing':
                book_id = request.form.get('book_id')
            
            elif mode == 'manual':
                isbn = request.form.get('isbn')
                title = request.form.get('title')
                author_name = request.form.get('author')
                genre_name = request.form.get('genre')
                publisher = request.form.get('publisher')
                pub_date = request.form.get('publication_date') or None
                lang = request.form.get('language')
                pages = request.form.get('page_number') or None
                phys_desc = request.form.get('physical_description')
                summary = request.form.get('summary')

                cursor.execute("SELECT book_id FROM Book WHERE isbn = %s", (isbn,))
                existing = cursor.fetchone()
                
                if existing:
                    book_id = existing['book_id']
                else:
                    cursor.execute("""
                        INSERT INTO Book (isbn, title, publisher, publication_date, language, page_number, physical_description, summary)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (isbn, title, publisher, pub_date, lang, pages, phys_desc, summary))
                    book_id = cursor.lastrowid
                    
                    cursor.execute("SELECT author_id FROM Author WHERE author_name = %s", (author_name,))
                    auth = cursor.fetchone()
                    if auth:
                        author_id = auth['author_id']
                    else:
                        cursor.execute("INSERT INTO Author (author_name) VALUES (%s)", (author_name,))
                        author_id = cursor.lastrowid
                    cursor.execute("INSERT INTO Book_Author (book_id, author_id) VALUES (%s, %s)", (book_id, author_id))
                    
                    cursor.execute("SELECT genre_id FROM Genre WHERE genre_name = %s", (genre_name,))
                    gen = cursor.fetchone()
                    if gen:
                        genre_id = gen['genre_id']
                    else:
                        cursor.execute("INSERT INTO Genre (genre_name) VALUES (%s)", (genre_name,))
                        genre_id = cursor.lastrowid
                    cursor.execute("INSERT INTO Book_Genre (book_id, genre_id) VALUES (%s, %s)", (book_id, genre_id))

            import random
            new_barcode = f"EXCH{random.randint(10000,99999)}"
            
            cursor.execute("""
                INSERT INTO Copy (item_barcode, material_type, acquisition_type, status, book_id, owner_id) 
                VALUES (%s, 'Book', 'Exchange', 'Available', %s, %s)
            """, (new_barcode, book_id, user_id))
            
            mysql.connection.commit()
            system_log(
                "Catalog",
                "INFO",
                "ExchangeService",
                f"Exchange copy created (barcode={new_barcode}, book_id={book_id})."
            )
            flash("Book added to your Exchange list!", "success")
            return redirect(url_for('main.my_books'))

    except Exception as e:
        mysql.connection.rollback()
        system_log("Catalog", "ERROR", "ExchangeService", f"Add book failed: {e}")
        flash(f"Error adding book: {str(e)}", "danger")
        print(f"DEBUG ADD BOOK ERROR: {e}")

    return redirect(url_for('main.my_books'))

@main_bp.route('/my-books', endpoint='my_books')
def my_books():
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    user_id = session['userid']
    cursor = get_cursor()

    query_exchange = """
        SELECT c.item_barcode, b.title, c.status, c.book_id,
               GROUP_CONCAT(DISTINCT a.author_name SEPARATOR ', ') AS authors
        FROM Copy c
        JOIN Book b ON c.book_id = b.book_id
        LEFT JOIN Book_Author ba ON b.book_id = ba.book_id
        LEFT JOIN Author a ON ba.author_id = a.author_id
        WHERE c.owner_id = %s AND c.acquisition_type = 'Exchange'
        GROUP BY c.item_barcode, b.title, c.status, c.book_id
    """
    cursor.execute(query_exchange, (user_id,))
    exchange_books = cursor.fetchall()
    for book in exchange_books:
        book['waiting_for_other'] = False  
        
        if book['status'] == 'Pending Handoff':
            cursor.execute("""
                SELECT request_id, requester_confirmed, owner_confirmed, reader_id 
                FROM Request WHERE book_id = %s AND status = 'Approved'
            """, (book['book_id'],))
            req_as_owner = cursor.fetchone()

            cursor.execute("""
                SELECT request_id, requester_confirmed, owner_confirmed, reader_id 
                FROM Request WHERE exchange_book_id = %s AND status = 'Approved'
            """, (book['item_barcode'],))
            req_as_requester = cursor.fetchone()

            if req_as_owner:
                if req_as_owner['owner_confirmed'] == 1 and req_as_owner['requester_confirmed'] == 0:
                    book['waiting_for_other'] = True
            
            elif req_as_requester:
                if req_as_requester['requester_confirmed'] == 1 and req_as_requester['owner_confirmed'] == 0:
                    book['waiting_for_other'] = True

    query_donation = """
        SELECT b.title, c.added_date,
               GROUP_CONCAT(DISTINCT a.author_name SEPARATOR ', ') AS authors
        FROM Copy c
        JOIN Book b ON c.book_id = b.book_id
        LEFT JOIN Book_Author ba ON b.book_id = ba.book_id
        LEFT JOIN Author a ON ba.author_id = a.author_id
        WHERE c.owner_id = %s AND c.acquisition_type = 'Donation'
        GROUP BY c.item_barcode, b.title, c.added_date
    """
    cursor.execute(query_donation, (user_id,))
    donation_books = cursor.fetchall()

    return render_template('my-books.html', exchange_books=exchange_books, donation_books=donation_books)

@main_bp.route('/confirm-handoff/<string:copy_id>', methods=['POST'], endpoint='confirm_handoff')
def confirm_handoff(copy_id):
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    
    user_id = session['userid']
    cursor = get_cursor()
    
    cursor.execute("""
        SELECT request_id, reader_id, book_id, exchange_book_id, requester_confirmed, owner_confirmed
        FROM Request 
        WHERE book_id = (SELECT book_id FROM Copy WHERE item_barcode=%s) 
          AND status='Approved'
    """, (copy_id,))
    req_owner = cursor.fetchone()
    
    cursor.execute("""
        SELECT request_id, reader_id, book_id, exchange_book_id, requester_confirmed, owner_confirmed
        FROM Request 
        WHERE exchange_book_id = %s 
          AND status='Approved'
    """, (copy_id,))
    req_requester = cursor.fetchone()

    req = req_owner or req_requester
    
    if not req:
        flash("Error: Could not find active exchange request to confirm.", "danger")
        return redirect(url_for('main.my_books'))

    request_id = req['request_id']
    partner_id = None
    
    if req_owner:
        cursor.execute("UPDATE Request SET owner_confirmed = TRUE WHERE request_id = %s", (request_id,))
        partner_id = req['reader_id'] 
    elif req_requester:
        cursor.execute("SELECT owner_id FROM Copy WHERE book_id = %s LIMIT 1", (req['book_id'],))
        book_owner_data = cursor.fetchone()
        partner_id = book_owner_data['owner_id']
        cursor.execute("UPDATE Request SET requester_confirmed = TRUE WHERE request_id = %s", (request_id,))
    
    mysql.connection.commit()

    cursor.execute("SELECT requester_confirmed, owner_confirmed FROM Request WHERE request_id = %s", (request_id,))
    updated_req = cursor.fetchone()

    if updated_req['requester_confirmed'] and updated_req['owner_confirmed']:
        cursor.execute("UPDATE Request SET status = 'Completed' WHERE request_id = %s", (request_id,))
        
        cursor.execute("UPDATE Copy SET status = 'Exchanged' WHERE item_barcode = %s", (copy_id,))
        if req['exchange_book_id']:
             cursor.execute("UPDATE Copy SET status = 'Exchanged' WHERE item_barcode = %s", (req['exchange_book_id'],))
        
        cursor.execute("UPDATE Copy SET status = 'Exchanged' WHERE book_id = %s AND status = 'Pending Handoff'", (req['book_id'],))

        msg = "Exchange Successful! Both parties have confirmed the handoff."
        cursor.execute("INSERT INTO Notification (subject, details, is_read, user_id) VALUES (%s, %s, FALSE, %s)", ("Exchange Complete", msg, user_id))
        cursor.execute("INSERT INTO Notification (subject, details, is_read, user_id) VALUES (%s, %s, FALSE, %s)", ("Exchange Complete", msg, partner_id))

        mysql.connection.commit()
        system_log("Requests", "INFO", "ExchangeService", f"Exchange completed (request_id={request_id}).")
        flash("Exchange completed successfully!", "success")
        
    else:
        msg = "Your partner has confirmed the handoff. Please confirm on your 'My Books' page to complete the exchange."
        cursor.execute("INSERT INTO Notification (subject, details, is_read, user_id) VALUES (%s, %s, FALSE, %s)", ("Handoff Update", msg, partner_id))
        
        mysql.connection.commit()
        system_log("Requests", "INFO", "ExchangeService", f"Handoff confirmed (request_id={request_id}).")
        flash("Handoff confirmed. Notification sent to partner.", "info")

    return redirect(url_for('main.my_books'))

@main_bp.route('/api/search-books-db', methods=['GET'])
def search_books_db_api():
    if 'loggedin' not in session: return jsonify([])
    query = request.args.get('q', '')
    cursor = get_cursor()
    
    sql = """
        SELECT b.book_id, b.title, b.isbn, b.publisher, b.language, 
               b.page_number, b.physical_description, b.summary,
               DATE_FORMAT(b.publication_date, '%%Y-%%m-%%d') as publication_date,
               GROUP_CONCAT(DISTINCT a.author_name SEPARATOR ', ') as authors,
               GROUP_CONCAT(DISTINCT g.genre_name SEPARATOR ', ') as genres
        FROM Book b
        LEFT JOIN Book_Author ba ON b.book_id = ba.book_id
        LEFT JOIN Author a ON ba.author_id = a.author_id
        LEFT JOIN Book_Genre bg ON b.book_id = bg.book_id
        LEFT JOIN Genre g ON bg.genre_id = g.genre_id
        WHERE b.title LIKE %s OR b.isbn LIKE %s
        GROUP BY b.book_id
        LIMIT 10
    """
    search_term = f"%{query}%"
    cursor.execute(sql, (search_term, search_term))
    results = cursor.fetchall()
    return jsonify(results)

@main_bp.route('/remove-book/<string:copy_id>', methods=['POST'], endpoint='remove_book')
def remove_book(copy_id):
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    cursor = get_cursor()
    cursor.execute("DELETE FROM Copy WHERE item_barcode = %s AND status = 'Available'", (copy_id,))
    mysql.connection.commit()
    system_log("Catalog", "INFO", "ExchangeService", f"Exchange copy removed (barcode={copy_id}).")
    flash("Book removed.", "success")
    return redirect(url_for('main.my_books'))

@main_bp.route('/cancel-handoff/<string:copy_id>', methods=['POST'], endpoint='cancel_handoff')
def cancel_handoff(copy_id):
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    
    user_id = session['userid']
    cursor = get_cursor()
    
    cursor.execute("""
        SELECT request_id, reader_id, book_id, exchange_book_id 
        FROM Request 
        WHERE (book_id = (SELECT book_id FROM Copy WHERE item_barcode=%s) OR exchange_book_id = %s)
          AND status='Approved'
    """, (copy_id, copy_id))
    req = cursor.fetchone()
    
    if req:
        request_id = req['request_id']
        
        partner_id = None
        if req['reader_id'] == user_id:
            cursor.execute("SELECT owner_id FROM Copy WHERE book_id = %s LIMIT 1", (req['book_id'],))
            owner_data = cursor.fetchone()
            partner_id = owner_data['owner_id']
        else:
            partner_id = req['reader_id']

        cursor.execute("UPDATE Request SET status = 'Rejected' WHERE request_id = %s", (request_id,))
        
        cursor.execute("UPDATE Copy SET status = 'Available' WHERE item_barcode = %s", (copy_id,))
        if req['exchange_book_id']:
            cursor.execute("UPDATE Copy SET status = 'Available' WHERE item_barcode = %s", (req['exchange_book_id'],))
        cursor.execute("UPDATE Copy SET status = 'Available' WHERE book_id = %s AND status = 'Pending Handoff'", (req['book_id'],))

        msg = "The exchange handoff was cancelled by the other user. Your book is now marked 'Available' again."
        cursor.execute("INSERT INTO Notification (subject, details, is_read, user_id) VALUES (%s, %s, FALSE, %s)", ("Handoff Cancelled", msg, partner_id))

        mysql.connection.commit()
        system_log("Requests", "INFO", "ExchangeService", f"Handoff cancelled (request_id={request_id}).")
        flash("Handoff cancelled. Partner has been notified.", "warning")
    else:
        cursor.execute("UPDATE Copy SET status = 'Available' WHERE item_barcode = %s", (copy_id,))
        mysql.connection.commit()
        system_log("Catalog", "INFO", "ExchangeService", f"Exchange copy status reset (barcode={copy_id}).")
        flash("Book status reset to Available.", "info")

    return redirect(url_for('main.my_books'))
@main_bp.route('/exchange-market', endpoint='exchange_market')
def exchange_market():
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    user_id = session['userid']
    cursor = get_cursor()
    
    query = """
        SELECT c.item_barcode, b.title, 
               (SELECT COALESCE(AVG(rating), 0) FROM Reader_Rate WHERE rated_user_id = c.owner_id) as owner_rating,
               GROUP_CONCAT(DISTINCT a.author_name SEPARATOR ', ') AS authors,
               u.user_id AS owner_id, 
               CONCAT(u.user_first_name, ' ', u.user_last_name) as owner_name
        FROM Copy c 
        JOIN Book b ON c.book_id = b.book_id 
        JOIN User u ON c.owner_id = u.user_id
        LEFT JOIN Book_Author ba ON b.book_id = ba.book_id 
        LEFT JOIN Author a ON ba.author_id = a.author_id
        WHERE c.acquisition_type = 'Exchange' 
          AND c.status = 'Available' 
          AND c.owner_id != %s
        GROUP BY c.item_barcode, b.title, c.owner_id, u.user_first_name, u.user_last_name
    """
    cursor.execute(query, (user_id,))
    books = cursor.fetchall()
    return render_template('exchange-market.html', books=books)

@main_bp.route('/exchange-details/<string:barcode>', endpoint='exchange_details')
def exchange_details(barcode):
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    cursor = get_cursor()
    query = """
        SELECT c.item_barcode, b.book_id, b.title, b.summary, b.page_number, b.publisher, b.publication_date,
               GROUP_CONCAT(DISTINCT a.author_name SEPARATOR ', ') AS authors,
               u.user_id AS owner_id, CONCAT(u.user_first_name, ' ', u.user_last_name) as owner_name, c.status
        FROM Copy c JOIN Book b ON c.book_id = b.book_id JOIN User u ON c.owner_id = u.user_id
        LEFT JOIN Book_Author ba ON b.book_id = ba.book_id LEFT JOIN Author a ON ba.author_id = a.author_id
        WHERE c.item_barcode = %s GROUP BY c.item_barcode, b.book_id
    """
    cursor.execute(query, (barcode,))
    book = cursor.fetchone()
    if not book: return redirect(url_for('main.exchange_market'))
    return render_template('exchange-book-details.html', book=book)
@main_bp.route('/reader-reviews/<int:reader_id>', methods=['GET', 'POST'], endpoint='reader_reviews')
def reader_reviews(reader_id):
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    
    user_id = session['userid']
    cursor = get_cursor()

    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')
        
        if not rating or not comment:
            flash("Please provide a rating and comment.", "warning")
        elif int(reader_id) == int(user_id):
            flash("You cannot rate yourself.", "warning")
        else:
            try:
                cursor.execute("""
                    INSERT INTO Reader_Rate (rating, comment, created_date, rated_user_id, rate_owner_id)
                    VALUES (%s, %s, NOW(), %s, %s)
                """, (rating, comment, reader_id, user_id))
                mysql.connection.commit()
                flash("Review submitted successfully!", "success")
            except Exception as e:
                mysql.connection.rollback()
                system_log("Reviews", "ERROR", "ReaderReviewService", f"Reader review failed: {e}")
                if "Duplicate entry" in str(e):
                    flash("You have already rated this user.", "info")
                else:
                    flash(f"Error submitting review: {str(e)}", "danger")
        
        return redirect(url_for('main.reader_reviews', reader_id=reader_id))

    cursor.execute("SELECT CONCAT(user_first_name, ' ', user_last_name) as name FROM User WHERE user_id = %s", (reader_id,))
    user = cursor.fetchone()
    
    query = """
        SELECT rr.rating, rr.comment, rr.created_date, 
               CONCAT(u.user_first_name, ' ', u.user_last_name) as reviewer_name
        FROM Reader_Rate rr 
        JOIN User u ON rr.rate_owner_id = u.user_id 
        WHERE rr.rated_user_id = %s 
        ORDER BY rr.created_date DESC
    """
    cursor.execute(query, (reader_id,))
    reviews = cursor.fetchall()
    
    target_name = user['name'] if user else "Unknown User"
    return render_template('reader-reviews.html', reviews=reviews, target_user=target_name)

@main_bp.route('/request-exchange/<string:barcode>', methods=['POST'], endpoint='request_exchange')
def request_exchange(barcode):
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    user_id = session['userid']
    cursor = get_cursor()

    try:
        cursor.execute("""
            SELECT count(*) as count 
            FROM Copy 
            WHERE owner_id = %s AND acquisition_type = 'Exchange' AND status = 'Available'
        """, (user_id,))
        user_inventory = cursor.fetchone()

        if user_inventory['count'] == 0:
            flash("You must add at least one 'Available' book to 'My Books' before you can make a request.", "warning")
            return redirect(url_for('main.exchange_market'))

        cursor.execute("SELECT c.book_id, c.owner_id, b.title FROM Copy c JOIN Book b ON c.book_id = b.book_id WHERE c.item_barcode = %s", (barcode,))
        copy = cursor.fetchone()
        
        if not copy:
            flash("Book copy not found.", "danger")
            return redirect(url_for('main.exchange_market'))

        if copy['owner_id'] == user_id:
            flash("You cannot request your own book.", "warning")
            return redirect(url_for('main.exchange_market'))

        cursor.execute("""
            SELECT request_id, status FROM Request 
            WHERE reader_id = %s AND book_id = %s AND request_type = 'Exchange'
        """, (user_id, copy['book_id']))
        existing_req = cursor.fetchone()

        request_id = None
        if existing_req:
            if existing_req['status'] in ['Pending', 'Approved']:
                flash("You already have an active request for this book. Please wait for the owner to respond.", "info")
                return redirect(url_for('main.exchange_market'))
            
            else:
                cursor.execute("""
                    UPDATE Request 
                    SET status = 'Pending', request_date = NOW(), 
                        requester_confirmed = 0, owner_confirmed = 0, exchange_book_id = NULL
                    WHERE request_id = %s
                """, (existing_req['request_id'],))
                request_id = existing_req['request_id']
        else:
            cursor.execute("""
                INSERT INTO Request (request_date, expire_date, request_type, status, reader_id, book_id) 
                VALUES (NOW(), DATE_ADD(NOW(), INTERVAL 14 DAY), 'Exchange', 'Pending', %s, %s)
            """, (user_id, copy['book_id']))
            request_id = cursor.lastrowid
        
        owner_id = copy['owner_id']
        book_title = copy['title']
        notif_subject = "New Exchange Request"
        notif_msg = f"A user has requested to exchange for your book: {book_title}. Go to 'Exchange Requests' to view."
        cursor.execute("INSERT INTO Notification (subject, details, is_read, user_id) VALUES (%s, %s, FALSE, %s)", (notif_subject, notif_msg, owner_id))

        mysql.connection.commit()
        if request_id:
            system_log(
                "Requests",
                "INFO",
                "ExchangeService",
                f"Exchange request created (request_id={request_id}, book_id={copy['book_id']})."
            )
        flash("Exchange request sent successfully!", "success")

    except Exception as e:
        mysql.connection.rollback()
        system_log("Requests", "ERROR", "ExchangeService", f"Exchange request failed: {e}")
        flash(f"Error processing request: {str(e)}", "danger")
            
    return redirect(url_for('main.exchange_market'))

@main_bp.route('/exchange-requests', endpoint='exchange_requests')
def exchange_requests():
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    user_id = session['userid']
    cursor = get_cursor()
    query = """
        SELECT r.request_id, r.request_date, b.title AS my_book_title, 
               r.reader_id, CONCAT(u.user_first_name, ' ', u.user_last_name) AS requester_name
        FROM Request r
        JOIN Book b ON r.book_id = b.book_id
        JOIN User u ON r.reader_id = u.user_id
        JOIN Copy c ON c.book_id = b.book_id
        WHERE r.request_type = 'Exchange' AND r.status = 'Pending' AND c.owner_id = %s
        GROUP BY r.request_id, r.request_date, b.title, r.reader_id, requester_name
    """
    cursor.execute(query, (user_id,))
    requests = cursor.fetchall()
    return render_template('exchange-requests.html', requests=requests)

@main_bp.route('/reject-exchange/<int:request_id>', methods=['POST'], endpoint='reject_exchange')
def reject_exchange(request_id):
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    
    cursor = get_cursor()
    
    try:
        cursor.execute("""
            SELECT r.reader_id, b.title 
            FROM Request r 
            JOIN Book b ON r.book_id = b.book_id 
            WHERE r.request_id = %s
        """, (request_id,))
        req_data = cursor.fetchone()
        
        if req_data:
            requester_id = req_data['reader_id']
            book_title = req_data['title']
            
            subject = "Exchange Request Rejected"
            msg = f"Your request to exchange for '{book_title}' was declined by the owner."
            cursor.execute("INSERT INTO Notification (subject, details, is_read, user_id) VALUES (%s, %s, FALSE, %s)", (subject, msg, requester_id))

        cursor.execute("UPDATE Request SET status = 'Rejected' WHERE request_id = %s", (request_id,))
        
        mysql.connection.commit()
        system_log("Requests", "INFO", "ExchangeService", f"Exchange request rejected (request_id={request_id}).")
        flash("Request rejected. The user has been notified.", "info")
        
    except Exception as e:
        mysql.connection.rollback()
        system_log("Requests", "ERROR", "ExchangeService", f"Reject exchange failed: {e}")
        flash(f"Error rejecting request: {str(e)}", "danger")

    return redirect(url_for('main.exchange_requests'))

@main_bp.route('/api/get-user-exchange-books/<int:user_id>')
def get_user_exchange_books(user_id):
    cursor = get_cursor()
    query = "SELECT c.item_barcode as barcode, b.title FROM Copy c JOIN Book b ON c.book_id = b.book_id WHERE c.owner_id = %s AND c.acquisition_type = 'Exchange' AND c.status = 'Available'"
    cursor.execute(query, (user_id,))
    books = cursor.fetchall()
    return jsonify(books)

@main_bp.route('/accept-exchange/<int:request_id>', methods=['POST'], endpoint='accept_exchange')
def accept_exchange(request_id):
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    cursor = get_cursor()
    selected_barcode = request.form.get('selected_book_barcode')
    if not selected_barcode: return redirect(url_for('main.exchange_requests'))

    cursor.execute("UPDATE Request SET status = 'Approved', exchange_book_id = %s WHERE request_id = %s", (selected_barcode, request_id))
    cursor.execute("UPDATE Copy SET status = 'Pending Handoff' WHERE item_barcode = %s", (selected_barcode,))
    cursor.execute("SELECT book_id, reader_id FROM Request WHERE request_id = %s", (request_id,))
    req = cursor.fetchone()
    
    cursor.execute("SELECT item_barcode FROM Copy WHERE book_id=%s AND owner_id=%s LIMIT 1", (req['book_id'], session['userid']))
    my_copy = cursor.fetchone()
    if my_copy: cursor.execute("UPDATE Copy SET status = 'Pending Handoff' WHERE item_barcode = %s", (my_copy['item_barcode'],))
    
    requester_id = req['reader_id']
    notif_subject = "Exchange Accepted!"
    notif_msg = "Your exchange request has been accepted! Please coordinate the handoff."
    cursor.execute("INSERT INTO Notification (subject, details, is_read, user_id) VALUES (%s, %s, FALSE, %s)", (notif_subject, notif_msg, requester_id))

    mysql.connection.commit()
    system_log("Requests", "INFO", "ExchangeService", f"Exchange request approved (request_id={request_id}).")
    flash("Exchange accepted!", "success")
    return redirect(url_for('main.my_books'))

@main_bp.route('/renew/<int:checkout_id>', methods=['POST'], endpoint='renew_checkout')
def renew_checkout(checkout_id):
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    user_id = session['userid']
    cursor = get_cursor()

    try:
        cursor.execute("""
            SELECT 
                c.checkout_id, c.renew_count, c.due_date, c.copy_id, 
                b.book_id,
                p.loan_period_days, p.renewals_allowed
            FROM Checkout c
            JOIN Copy cp ON c.copy_id = cp.item_barcode
            JOIN Book b ON cp.book_id = b.book_id
            JOIN Reader r ON c.reader_id = r.reader_id
            JOIN Policy p ON p.policy_id = r.policy_id
            WHERE c.checkout_id = %s AND c.reader_id = %s AND c.returned_date IS NULL
        """, (checkout_id, user_id))
        loan = cursor.fetchone()

        if not loan:
            flash("Error: Loan not found or already returned.", "danger")
            return redirect(url_for('main.my_checkouts'))

        if loan['due_date'] < datetime.now():
            flash("Renewal failed: This book is already overdue.", "warning")
            return redirect(url_for('main.my_checkouts'))
            
        if loan['renew_count'] >= loan['renewals_allowed']:
            flash(f"Renewal failed: You have reached the maximum renewal limit ({loan['renewals_allowed']}).", "warning")
            return redirect(url_for('main.my_checkouts'))

        cursor.execute("""
            SELECT COUNT(*) AS hold_count 
            FROM Request 
            WHERE book_id = %s 
              AND request_type = 'Hold' 
              AND status IN ('Pending', 'Approved')
        """, (loan['book_id'],))
        holds = cursor.fetchone()
        
        if holds['hold_count'] > 0:
            flash("Renewal failed: Another user has a hold request on this book.", "warning")
            return redirect(url_for('main.my_checkouts'))
        
        new_due_date = datetime.now() + timedelta(days=loan['loan_period_days'])
        
        cursor.execute("""
            UPDATE Checkout 
            SET due_date = %s, renew_count = renew_count + 1
            WHERE checkout_id = %s
        """, (new_due_date, checkout_id))
        
        mysql.connection.commit()
        system_log("Checkouts", "INFO", "CheckoutService", f"Checkout renewed (checkout_id={checkout_id}).")
        flash(f"Book renewed successfully! New due date: {new_due_date.strftime('%Y-%m-%d')}.", "success")

    except Exception as e:
        mysql.connection.rollback()
        system_log("Checkouts", "ERROR", "CheckoutService", f"Checkout renewal failed: {e}")
        print(f"Renewal Error: {e}")
        flash("An unexpected error occurred during renewal.", "danger")

    return redirect(url_for('main.my_checkouts'))

@main_bp.route('/my-holds', endpoint='my_holds')
def my_holds():
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    
    user_id = session['userid']
    cursor = get_cursor()

    query_holds = """
        SELECT 
            r.request_id, 
            r.request_date, 
            r.status, 
            b.title AS item_title,
            GROUP_CONCAT(DISTINCT a.author_name SEPARATOR ', ') AS item_author
        FROM Request r
        JOIN Book b ON r.book_id = b.book_id
        LEFT JOIN Book_Author ba ON b.book_id = ba.book_id
        LEFT JOIN Author a ON ba.author_id = a.author_id
        WHERE r.reader_id = %s AND r.request_type = 'Hold'
        GROUP BY r.request_id, b.title, r.request_date, r.status
        ORDER BY r.request_date DESC
    """
    cursor.execute(query_holds, (user_id,))
    holds = cursor.fetchall()

    return render_template('my-holds.html', holds=holds)

@main_bp.route('/cancel-hold/<int:request_id>', methods=['POST'], endpoint='cancel_hold')
def cancel_hold(request_id):
    if 'loggedin' not in session: return redirect(url_for('auth.login'))
    user_id = session['userid']
    cursor = get_cursor()

    try:
        cursor.execute("""
            SELECT status FROM Request 
            WHERE request_id = %s AND reader_id = %s AND request_type = 'Hold'
        """, (request_id, user_id))
        req = cursor.fetchone()

        if req and req['status'] == 'Pending':
            cursor.execute("DELETE FROM Request WHERE request_id = %s", (request_id,))
            mysql.connection.commit()
            system_log("Requests", "INFO", "RequestService", f"Hold request cancelled (request_id={request_id}).")
            flash("Hold request cancelled successfully.", "success")
        elif req and req['status'] != 'Pending':
            flash("Cannot cancel this hold; it may already be processed or approved.", "warning")
        else:
            flash("Error: Hold request not found.", "danger")

    except Exception as e:
        mysql.connection.rollback()
        system_log("Requests", "ERROR", "RequestService", f"Cancel hold failed: {e}")
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect(url_for('main.my_holds'))

@main_bp.route('/pay-fine', methods=['POST'])
def pay_fine():
    fine_id = request.form.get('fine_id')
    if not fine_id:
        flash("No fine selected for payment.", "error")
        return redirect(url_for('main.my_fines'))
    
    cursor = get_cursor()

    query = """
    UPDATE Fine
    SET status = 'Paid', payment_method = 'Credit Card', date_paid = NOW()
    WHERE fine_id = %s
    """
    cursor.execute(query, (fine_id,))
    mysql.connection.commit()
    cursor.close()
    system_log("Fines", "INFO", "FineService", f"Fine paid (fine_id={fine_id}).")

    return redirect(url_for('main.my_fines', success=1))
