from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import MySQLdb.cursors
from extensions import mysql
from routes.notifications import NotificationService
from routes.auth import user_log_activity
from utils.system_log import system_log
from werkzeug.security import generate_password_hash
librarian_bp = Blueprint("librarian", __name__, url_prefix="/librarian")

#notify users
def notify_all_users(subject, details):
    notification_service = NotificationService(mysql.connection)
    cursor = get_cursor()
    cursor.execute("SELECT user_id FROM User")
    users = cursor.fetchall()

    for user in users:
        notification_service.add_notification(
            user["user_id"],
            subject,
            details
        )

def get_cursor():
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)

def librarian_required():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    if session.get('user_type') != 'Librarian':
        return "Forbidden", 403
    return None



@librarian_bp.route("/requests", methods=["GET"], endpoint="requests")
def requests():
    check = librarian_required()
    if check:
        return check

    cursor = get_cursor()

    tabs = ["borrows", "book_requests", "exchanges", "donations"]
    active_tab = (request.args.get("tab") or "borrows").strip() or "borrows"
    if active_tab not in tabs:
        active_tab = "borrows"

    def get_tab_values(tab):
        title_val = (request.args.get(f"search_title_{tab}") or "").strip()
        author_val = (request.args.get(f"search_author_{tab}") or "").strip()
        date_val = (request.args.get(f"search_date_{tab}") or "").strip()
        status_val = (request.args.get(f"search_status_{tab}") or "").strip()
        user_id_val = (request.args.get(f"search_user_id_{tab}") or "").strip()
        user_name_val = (request.args.get(f"search_user_name_{tab}") or "").strip()

        if tab == active_tab:
            if not title_val:
                title_val = (request.args.get("search_title") or "").strip()
            if not author_val:
                author_val = (request.args.get("search_author") or "").strip()
            if not date_val:
                date_val = (request.args.get("search_date") or "").strip()
            if not status_val:
                status_val = (request.args.get("search_status") or "").strip()
            if not user_id_val:
                user_id_val = (request.args.get("search_user_id") or "").strip()
            if not user_name_val:
                user_name_val = (request.args.get("search_user_name") or "").strip()

        return {
            "title": title_val,
            "author": author_val,
            "date": date_val,
            "status": status_val,
            "user_id": user_id_val,
            "user_name": user_name_val,
        }

    search_values = {tab: get_tab_values(tab) for tab in tabs}
    active_values = search_values[active_tab]

    def build_request_filters(title_col, author_col, values, apply_filters):
        if not apply_filters:
            return "", []

        where = []
        params = []

        if values["title"]:
            where.append(f"{title_col} LIKE %s")
            params.append(f"%{values['title']}%")

        if values["author"]:
            where.append(f"{author_col} LIKE %s")
            params.append(f"%{values['author']}%")

        if values["date"]:
            where.append("DATE(r.request_date) = %s")
            params.append(values["date"])

        if values["status"]:
            where.append("r.status = %s")
            params.append(values["status"])

        if values["user_id"]:
            where.append("CAST(r.reader_id AS CHAR) LIKE %s")
            params.append(f"%{values['user_id']}%")

        if values["user_name"]:
            where.append("CONCAT_WS(' ', u.user_first_name, u.user_middle_name, u.user_last_name) LIKE %s")
            params.append(f"%{values['user_name']}%")

        where_sql = (" AND " + " AND ".join(where)) if where else ""
        return where_sql, params

    # BORROWS
    where_sql, params = build_request_filters("b.title", "a.author_name", search_values["borrows"], active_tab == "borrows")
    cursor.execute(f"""
        SELECT r.request_id, r.request_date, r.status, r.reader_id AS user_id,
               CONCAT_WS(' ', u.user_first_name, u.user_middle_name, u.user_last_name) AS user_full_name,
               b.title AS item_title,
               GROUP_CONCAT(DISTINCT a.author_name SEPARATOR ', ') AS item_author
        FROM Request r
        JOIN User u ON r.reader_id = u.user_id
        JOIN Copy cp ON r.copy_id = cp.item_barcode
        JOIN Book b ON cp.book_id = b.book_id
        LEFT JOIN Book_Author ba ON b.book_id = ba.book_id
        LEFT JOIN Author a ON ba.author_id = a.author_id
        WHERE r.request_type = 'Borrow'{where_sql}
        GROUP BY r.request_id, r.reader_id, u.user_first_name, u.user_middle_name, u.user_last_name,
                 b.title, r.request_date, r.status
        ORDER BY r.request_date DESC
    """, params)
    borrows = cursor.fetchall()

    # EXCHANGES
    where_sql, params = build_request_filters("b.title", "a.author_name", search_values["exchanges"], active_tab == "exchanges")
    cursor.execute(f"""
        SELECT r.request_id, r.request_date, r.status, r.reader_id AS user_id,
               CONCAT_WS(' ', u.user_first_name, u.user_middle_name, u.user_last_name) AS user_full_name,
               b.title AS item_title,
               GROUP_CONCAT(DISTINCT a.author_name SEPARATOR ', ') AS item_author
        FROM Request r
        JOIN User u ON r.reader_id = u.user_id
        JOIN Copy cp ON r.copy_id = cp.item_barcode
        JOIN Book b ON cp.book_id = b.book_id
        LEFT JOIN Book_Author ba ON b.book_id = ba.book_id
        LEFT JOIN Author a ON ba.author_id = a.author_id
        WHERE r.request_type = 'Exchange'{where_sql}
        GROUP BY r.request_id, r.reader_id, u.user_first_name, u.user_middle_name, u.user_last_name,
                 b.title, r.request_date, r.status
        ORDER BY r.request_date DESC
    """, params)
    exchanges = cursor.fetchall()

    # DONATIONS (Material only)
    where_sql, params = build_request_filters("m.title", "m.author", search_values["donations"], active_tab == "donations")
    cursor.execute(f"""
        SELECT r.request_id, r.request_date, r.status, r.reader_id AS user_id,
               CONCAT_WS(' ', u.user_first_name, u.user_middle_name, u.user_last_name) AS user_full_name,
               m.isbn, m.title AS item_title, m.publisher, m.publication_date, m.author AS item_author
        FROM Request r
        JOIN User u ON r.reader_id = u.user_id
        JOIN Material m ON r.material_id = m.material_id
        WHERE r.request_type = 'Donation'{where_sql}
    """, params)
    donations = cursor.fetchall()
    donations.sort(key=lambda x: x["request_date"], reverse=True)

    # BOOK REQUESTS (Material)
    where_sql, params = build_request_filters("m.title", "m.author", search_values["book_requests"], active_tab == "book_requests")
    cursor.execute(f"""
        SELECT r.request_id, r.request_date, r.status, r.reader_id AS user_id,
               CONCAT_WS(' ', u.user_first_name, u.user_middle_name, u.user_last_name) AS user_full_name,
               m.isbn, m.title AS item_title, m.publisher, m.publication_date, m.author AS item_author
        FROM Request r
        JOIN User u ON r.reader_id = u.user_id
        JOIN Material m ON r.material_id = m.material_id
        WHERE r.request_type = 'Book Request'{where_sql}
        ORDER BY r.request_date DESC
    """, params)
    book_requests = cursor.fetchall()

    return render_template(
        "librarian-requests.html",
        borrows=borrows,
        book_requests=book_requests,
        exchanges=exchanges,
        donations=donations,
        active_tab=active_tab,
        search_values=search_values,
        active_values=active_values
    )

@librarian_bp.route("/requests/approve/<int:request_id>", methods=["POST"], endpoint="approve_request")
def approve_request(request_id):
    check = librarian_required()
    if check:
        return check

    cursor = get_cursor()
    cursor.execute("SELECT status, request_type, copy_id FROM Request WHERE request_id = %s", (request_id,))
    req = cursor.fetchone()

    if not req:
        flash("Request not found.", "danger")
    elif req["status"] != "Pending":
        flash("Only pending requests can be approved.", "warning")
    else:
        if req["request_type"] == "Exchange":
            cursor.execute("UPDATE Copy SET status = 'Available' WHERE item_barcode = %s", (req["copy_id"],))
            cursor.execute("UPDATE Request SET status = 'Completed' WHERE request_id = %s", (request_id,))
        else:
            cursor.execute("UPDATE Request SET status = 'Approved' WHERE request_id = %s", (request_id,))
        mysql.connection.commit()
        system_log("Requests", "INFO", "RequestService", f"Request approved (request_id={request_id}).")
        flash("Request approved successfully.", "success")

    return redirect(request.referrer or url_for("librarian.requests"))

@librarian_bp.route("/requests/reject/<int:request_id>", methods=["POST"], endpoint="reject_request")
def reject_request(request_id):
    check = librarian_required()
    if check:
        return check

    cursor = get_cursor()
    cursor.execute("SELECT status, request_type, copy_id FROM Request WHERE request_id = %s", (request_id,))
    req = cursor.fetchone()

    if not req:
        flash("Request not found.", "danger")
    elif req["status"] != "Pending":
        flash("Only pending requests can be rejected.", "warning")
    else:
        if req["request_type"] == "Exchange":
            cursor.execute("DELETE FROM Copy WHERE item_barcode = %s", (req["copy_id"],))
            mysql.connection.commit()
            system_log("Requests", "INFO", "RequestService", f"Exchange approval rejected (request_id={request_id}).")
            flash("Exchange approval rejected. Copy removed.", "success")
        else:
            cursor.execute("UPDATE Request SET status = 'Rejected' WHERE request_id = %s", (request_id,))
            mysql.connection.commit()
            system_log("Requests", "INFO", "RequestService", f"Request rejected (request_id={request_id}).")
            flash("Request rejected successfully.", "success")

    return redirect(request.referrer or url_for("librarian.requests"))

@librarian_bp.route("/requests/complete/<int:request_id>", methods=["POST"], endpoint="complete_request")
def complete_request(request_id):
    check = librarian_required()
    if check:
        return check

    cursor = get_cursor()
    cursor.execute("SELECT status, request_type, copy_id FROM Request WHERE request_id = %s", (request_id,))
    req = cursor.fetchone()

    if not req:
        flash("Request not found.", "danger")
    elif req["status"] != "Approved":
        flash("Only approved requests can be completed.", "warning")
    else:
        if req["request_type"] == "Exchange":
            cursor.execute("UPDATE Copy SET status = 'Available' WHERE item_barcode = %s", (req["copy_id"],))
        cursor.execute("UPDATE Request SET status = 'Completed' WHERE request_id = %s", (request_id,))
        mysql.connection.commit()
        system_log("Requests", "INFO", "RequestService", f"Request completed (request_id={request_id}).")
        flash("Request completed successfully.", "success")

    return redirect(request.referrer or url_for("librarian.requests"))

@librarian_bp.route("/requests/cancel/<int:request_id>", methods=["POST"], endpoint="cancel_request")
def cancel_request(request_id):
    check = librarian_required()
    if check:
        return check

    cursor = get_cursor()
    cursor.execute("SELECT status FROM Request WHERE request_id = %s", (request_id,))
    req = cursor.fetchone()

    if not req:
        flash("Request not found.", "danger")
    elif req["status"] != "Approved":
        flash("Only approved requests can be cancelled.", "warning")
    else:
        cursor.execute("UPDATE Request SET status = 'Cancelled' WHERE request_id = %s", (request_id,))
        mysql.connection.commit()
        system_log("Requests", "INFO", "RequestService", f"Request cancelled (request_id={request_id}).")
        flash("Request cancelled successfully.", "success")

    return redirect(request.referrer or url_for("librarian.requests"))

@librarian_bp.route("/requests/history/<int:request_id>", methods=["GET"], endpoint="request_history")
def request_history(request_id):
    check = librarian_required()
    if check:
        return check

    cursor = get_cursor()
    cursor.execute("""
        SELECT status, changed_at
        FROM Request_Status_History
        WHERE request_id = %s
        ORDER BY changed_at
    """, (request_id,))
    history = cursor.fetchall() or []
    return jsonify(history)

###---------------------------- AUTHORS MANAGEMENT----------------------------###
@librarian_bp.route("/authors", methods=["GET", "POST"], endpoint="authors")
def authors():
    check = librarian_required()
    if check: return check

    cursor = get_cursor()

    # ---------- CREATE (POST) ----------
    if request.method == "POST":
        author_name = (request.form.get("author_name") or "").strip()
        if not author_name:
            flash("Author name is required.", "danger")
        else:
            cursor.execute("INSERT INTO Author (author_name) VALUES (%s)", (author_name,))
            mysql.connection.commit()
            author_id = cursor.lastrowid
            system_log("Catalog", "INFO", "AuthorService", f"Author created (author_id={author_id}).")
            flash("Author created successfully.", "success")
        return redirect(url_for("librarian.authors"))

    # ---------- LIST + SEARCH (GET) ----------
    # pagination
    page = request.args.get("page", 1, type=int)
    per_page = 10

    where_sql, params, v = build_like_filters([
        ("search_id",   "CAST(author_id AS CHAR)", True),
        ("search_name", "author_name", False),
    ], request.args)

    cursor.execute(f"SELECT COUNT(*) AS total FROM Author {where_sql}", params)
    total = (cursor.fetchone() or {}).get("total", 0)

    page, total_pages, offset, has_prev, has_next = paginate(page, per_page, total)

    # data query
    cursor.execute(f"""
        SELECT author_id, author_name
        FROM Author
        {where_sql}
        ORDER BY author_id
        LIMIT %s OFFSET %s
    """, params + [per_page, offset])

    return render_template(
        "authors.html",
        authors=cursor.fetchall(),
        page=page, total_pages=total_pages, has_prev=has_prev, has_next=has_next,
        search_id=v["search_id"], search_name=v["search_name"],
    )

@librarian_bp.route("/authors/delete/<int:author_id>", methods=["POST"], endpoint="delete_author")
def delete_author(author_id):
    check = librarian_required()
    if check:
        return check

    cursor = get_cursor()
    cursor.execute("DELETE FROM Author WHERE author_id = %s", (author_id,))
    mysql.connection.commit()
    system_log("Catalog", "INFO", "AuthorService", f"Author deleted (author_id={author_id}).")
    flash("Author deleted successfully.", "success")

    return redirect(url_for("librarian.authors"))


@librarian_bp.route("/authors/edit", methods=["POST"], endpoint="edit_author")
def edit_author():
    check = librarian_required()
    if check:
        return check

    author_id = request.form.get("author_id")
    name = (request.form.get("author_name") or "").strip()

    if not author_id or not name:
        flash("Author name is required.", "danger")
        return redirect(url_for("librarian.authors"))

    cursor = get_cursor()
    cursor.execute(
        "UPDATE Author SET author_name = %s WHERE author_id = %s",
        (name, author_id)
    )
    mysql.connection.commit()
    system_log("Catalog", "INFO", "AuthorService", f"Author updated (author_id={author_id}).")
    flash("Author updated successfully.", "success")

    return redirect(url_for("librarian.authors"))

###---------------------------- GENRE MANAGEMENT----------------------------###
# NEW GENRE METHOD
@librarian_bp.route("/genres", methods=["GET", "POST"], endpoint="genres")
def genres():
    check = librarian_required()
    if check:
        return check

    cursor = get_cursor()

    # ---------- CREATE (POST) ----------
    if request.method == "POST":
        genre_name = (request.form.get("genre_name") or "").strip()
        if not genre_name:
            flash("Genre name is required.", "danger")
        else:
            cursor.execute("INSERT INTO Genre (genre_name) VALUES (%s)", (genre_name,))
            mysql.connection.commit()
            genre_id = cursor.lastrowid
            system_log("Catalog", "INFO", "GenreService", f"Genre created (genre_id={genre_id}).")
            flash("Genre created successfully.", "success")
        return redirect(url_for("librarian.genres"))

    # ---------- LIST + SEARCH (GET) ----------
    # pagination
    page = request.args.get("page", 1, type=int)
    per_page = 10

    where_sql, params, v = build_like_filters([
        ("search_id",   "CAST(genre_id AS CHAR)", True),
        ("search_name", "genre_name", False),
    ], request.args)

    cursor.execute(f"SELECT COUNT(*) AS total FROM Genre {where_sql}", params)
    total = (cursor.fetchone() or {}).get("total", 0)

    page, total_pages, offset, has_prev, has_next = paginate(page, per_page, total)

    # data query
    cursor.execute(f"""
        SELECT genre_id, genre_name
        FROM Genre
        {where_sql}
        ORDER BY genre_id
        LIMIT %s OFFSET %s
    """, params + [per_page, offset])

    return render_template(
        "genres.html",
        genres=cursor.fetchall(),
        page=page, total_pages=total_pages, has_prev=has_prev, has_next=has_next,
        search_id=v["search_id"], search_name=v["search_name"],
    )


@librarian_bp.route("/genres/delete/<int:genre_id>", methods=["POST"], endpoint="delete_genre")
def delete_genre(genre_id):
    check = librarian_required()
    if check:
        return check

    cursor = get_cursor()
    cursor.execute("DELETE FROM Genre WHERE genre_id = %s", (genre_id,))
    mysql.connection.commit()
    system_log("Catalog", "INFO", "GenreService", f"Genre deleted (genre_id={genre_id}).")
    flash("Genre deleted successfully.", "success")

    return redirect(url_for("librarian.genres"))

###---------------------------- LOCATION MANAGEMENT----------------------------###
@librarian_bp.route("/locations", methods=["GET", "POST"], endpoint="locations")
def locations():
    check = librarian_required()
    if check:
        return check

    cursor = get_cursor()

    # ---------- CREATE (POST) ----------
    if request.method == "POST":
        direction = (request.form.get("direction") or "").strip()
        collection = (request.form.get("collection") or "").strip()
        shelf_row = (request.form.get("shelf_row") or "").strip()

        if not direction:
            flash("Direction is required.", "danger")
        elif not collection:
            flash("Collection is required.", "danger")
        elif not shelf_row:
            flash("Shelf row is required.", "danger")
        else:
            cursor.execute(
                "INSERT INTO Location (direction, collection, shelf_row) VALUES (%s, %s, %s)",
                (direction, collection, shelf_row)
            )
            mysql.connection.commit()
            location_id = cursor.lastrowid
            system_log("Catalog", "INFO", "LocationService", f"Location created (location_id={location_id}).")
            flash("Location created successfully.", "success")
        return redirect(url_for("librarian.locations"))

    # ---------- LIST + SEARCH (GET) ----------
    page = request.args.get("page", 1, type=int)
    per_page = 10

    where_sql, params, v = build_like_filters([
        ("search_id", "CAST(location_id AS CHAR)", True),
        ("search_direction", "direction", False),
        ("search_collection", "collection", False),
        ("search_shelf_row", "shelf_row", False),
    ], request.args)

    cursor.execute(f"SELECT COUNT(*) AS total FROM Location {where_sql}", params)
    total = (cursor.fetchone() or {}).get("total", 0)

    page, total_pages, offset, has_prev, has_next = paginate(page, per_page, total)

    cursor.execute(f"""
        SELECT location_id, direction, collection, shelf_row
        FROM Location
        {where_sql}
        ORDER BY location_id
        LIMIT %s OFFSET %s
    """, params + [per_page, offset])

    return render_template(
        "locations.html",
        locations=cursor.fetchall(),
        page=page, total_pages=total_pages, has_prev=has_prev, has_next=has_next,
        search_id=v["search_id"],
        search_direction=v["search_direction"],
        search_collection=v["search_collection"],
        search_shelf_row=v["search_shelf_row"],
    )


@librarian_bp.route("/locations/delete/<int:location_id>", methods=["POST"], endpoint="delete_location")
def delete_location(location_id):
    check = librarian_required()
    if check:
        return check

    cursor = get_cursor()
    cursor.execute("DELETE FROM Location WHERE location_id = %s", (location_id,))
    mysql.connection.commit()
    system_log("Catalog", "INFO", "LocationService", f"Location deleted (location_id={location_id}).")
    flash("Location deleted successfully.", "success")

    return redirect(url_for("librarian.locations"))


@librarian_bp.route("/locations/edit", methods=["POST"], endpoint="edit_location")
def edit_location():
    check = librarian_required()
    if check:
        return check

    location_id = request.form.get("location_id")
    direction = (request.form.get("direction") or "").strip()
    collection = (request.form.get("collection") or "").strip()
    shelf_row = (request.form.get("shelf_row") or "").strip()

    if not location_id or not direction or not collection or not shelf_row:
        flash("All location fields are required.", "danger")
        return redirect(url_for("librarian.locations"))

    cursor = get_cursor()
    cursor.execute(
        "SELECT direction, collection, shelf_row FROM Location WHERE location_id = %s",
        (location_id,)
    )
    current = cursor.fetchone()
    if not current:
        flash("Location not found.", "danger")
        return redirect(url_for("librarian.locations"))

    if (
        current.get("direction") == direction
        and current.get("collection") == collection
        and current.get("shelf_row") == shelf_row
    ):
        flash("No changes to save.", "info")
        return redirect(url_for("librarian.locations"))

    cursor.execute(
        """
        SELECT location_id
        FROM Location
        WHERE direction = %s AND collection = %s AND shelf_row = %s
          AND location_id <> %s
        LIMIT 1
        """,
        (direction, collection, shelf_row, location_id)
    )
    duplicate = cursor.fetchone()
    if duplicate:
        flash("Location with the same direction, collection, and shelf row already exists.", "danger")
        return redirect(url_for("librarian.locations"))

    cursor.execute(
        """
        UPDATE Location
        SET direction = %s, collection = %s, shelf_row = %s
        WHERE location_id = %s
        """,
        (direction, collection, shelf_row, location_id)
    )
    mysql.connection.commit()
    system_log("Catalog", "INFO", "LocationService", f"Location updated (location_id={location_id}).")
    flash("Location updated successfully.", "success")

    return redirect(url_for("librarian.locations"))


@librarian_bp.route("/genres/edit", methods=["POST"], endpoint="edit_genre")
def edit_genre():
    check = librarian_required()
    if check:
        return check

    genre_id = request.form.get("genre_id")
    name = (request.form.get("genre_name") or "").strip()

    if not genre_id or not name:
        flash("Genre name is required.", "danger")
        return redirect(url_for("librarian.genres"))

    cursor = get_cursor()
    cursor.execute(
        "UPDATE Genre SET genre_name = %s WHERE genre_id = %s",
        (name, genre_id)
    )
    mysql.connection.commit()
    system_log("Catalog", "INFO", "GenreService", f"Genre updated (genre_id={genre_id}).")
    flash("Genre updated successfully.", "success")

    return redirect(url_for("librarian.genres"))

###---------------------------- BOOK MANAGEMENT----------------------------###
@librarian_bp.route("/books", methods=["GET", "POST"], endpoint="books")
def books():
    check = librarian_required()
    if check:
        return check

    cursor = get_cursor()

    # Load all genres for dropdown
    cursor.execute("SELECT genre_id, genre_name FROM Genre ORDER BY genre_name")
    all_genres = cursor.fetchall()

    # Load all authors for dropdown
    cursor.execute("SELECT author_id, author_name FROM Author ORDER BY author_name")
    all_authors = cursor.fetchall()

    # ---------- CREATE (POST) ----------
    if request.method == "POST":
        isbn = (request.form.get("isbn") or "").strip()
        title = (request.form.get("title") or "").strip()
        publisher = (request.form.get("publisher") or "").strip()
        publication_date = (request.form.get("publication_date") or "").strip()
        language = (request.form.get("language") or "").strip()
        physical_description = (request.form.get("physical_description") or "").strip()
        summary = (request.form.get("summary") or "").strip()
        page_number = (request.form.get("page_number") or "").strip()
        genre_ids = request.form.getlist("genre_ids")
        author_ids = request.form.getlist("author_ids")

        if not isbn:
            flash("ISBN is required.", "danger")
        elif not title:
            flash("Title is required.", "danger")
        elif not publisher:
            flash("Publisher is required.", "danger")
        elif not publication_date:
            flash("Publication date is required.", "danger")
        elif not language:
            flash("Language is required.", "danger")
        elif not physical_description:
            flash("Physical description is required.", "danger")
        elif not summary:
            flash("Summary is required.", "danger")
        elif not page_number:
            flash("Page number is required.", "danger")
        elif not genre_ids:
            flash("Genre is required.", "danger")
        elif not author_ids:
            flash("Author is required.", "danger")
        else:
            cursor.execute("""
                INSERT INTO Book (title, isbn, publisher, publication_date, language, physical_description, summary, page_number)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (title, isbn, publisher, publication_date, language, physical_description, summary, page_number))
            mysql.connection.commit()

            book_id = cursor.lastrowid

            if genre_ids:
                cursor.executemany(
                    "INSERT INTO Book_Genre (book_id, genre_id) VALUES (%s, %s)",
                    [(book_id, gid) for gid in genre_ids]
                )
                mysql.connection.commit()

            if author_ids:
                cursor.executemany(
                    "INSERT INTO Book_Author (book_id, author_id) VALUES (%s, %s)",
                    [(book_id, aid) for aid in author_ids]
                )
                mysql.connection.commit()

            system_log("Catalog", "INFO", "BookService", f"Book created (book_id={book_id}).")
            flash("Book created successfully.", "success")

        return redirect(url_for("librarian.books"))

    # ---------- LIST + SEARCH (GET) ----------
    page = request.args.get("page", 1, type=int)
    per_page = 10

    # make sure they are strings, not None
    search_id = (request.args.get("search_id") or "").strip()
    search_isbn = (request.args.get("search_isbn") or "").strip()
    search_title = (request.args.get("search_title") or "").strip()
    search_publisher = (request.args.get("search_publisher") or "").strip()
    search_publication_date = (request.args.get("search_publication_date") or "").strip()
    search_language = (request.args.get("search_language") or "").strip()
    search_physical_description = (request.args.get("search_physical_description") or "").strip()
    search_summary = (request.args.get("search_summary") or "").strip()
    search_page_number = (request.args.get("search_page_number") or "").strip()
    search_genre = (request.args.get("search_genre") or "").strip()
    search_author = (request.args.get("search_author") or "").strip()

    where = []
    params = []

    if search_id:
        where.append("CAST(b.book_id AS CHAR) LIKE %s")
        params.append(f"%{search_id}%")

    if search_isbn:
        where.append("isbn LIKE %s")
        params.append(f"%{search_isbn}%")

    if search_title:
        where.append("title LIKE %s")
        params.append(f"%{search_title}%")

    if search_publisher:
        where.append("publisher LIKE %s")
        params.append(f"%{search_publisher}%")

    if search_publication_date:
        where.append("publication_date LIKE %s")
        params.append(f"%{search_publication_date}%")

    if search_language:
        where.append("language LIKE %s")
        params.append(f"%{search_language}%")

    if search_physical_description:
        where.append("physical_description LIKE %s")
        params.append(f"%{search_physical_description}%")

    if search_summary:
        where.append("summary LIKE %s")
        params.append(f"%{search_summary}%")

    if search_page_number:
        where.append("CAST(page_number AS CHAR) LIKE %s")
        params.append(f"%{search_page_number}%")

    if search_genre:
        where.append("""
            EXISTS (
                SELECT 1
                FROM Book_Genre bgf
                JOIN Genre gf ON gf.genre_id = bgf.genre_id
                WHERE bgf.book_id = b.book_id
                AND gf.genre_id = %s
            )
        """)
        params.append(search_genre)

    if search_author:
        where.append("""
            EXISTS (
                SELECT 1
                FROM Book_Author baf
                JOIN Author af ON af.author_id = baf.author_id
                WHERE baf.book_id = b.book_id
                AND af.author_id = %s
            )
        """)
        params.append(search_author)



    where_sql = " WHERE " + " AND ".join(where) if where else ""
    # total count (for pagination)
    count_sql = f"""
    SELECT COUNT(DISTINCT b.book_id) AS total
    FROM Book b
    {where_sql}
    """

    cursor.execute(count_sql, params)
    row = cursor.fetchone()
    total = row["total"] if row else 0

    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    offset = (page - 1) * per_page

    if total:
        start_item = (page - 1) * per_page + 1
        end_item = min(total, page * per_page)
    else:
        start_item = 0
        end_item = 0

    if total:
        start_item = (page - 1) * per_page + 1
        end_item = min(total, page * per_page)
    else:
        start_item = 0
        end_item = 0

    if total:
        start_item = (page - 1) * per_page + 1
        end_item = min(total, page * per_page)
    else:
        start_item = 0
        end_item = 0
    

    # data query
    data_sql = f"""
        SELECT 
            b.book_id,
            b.isbn,
            b.title,
            b.publisher,
            b.publication_date,
            b.language,
            b.physical_description,
            b.summary,
            b.page_number,
            GROUP_CONCAT(DISTINCT g.genre_name ORDER BY g.genre_name SEPARATOR ', ') AS genres,
            GROUP_CONCAT(DISTINCT a.author_name ORDER BY a.author_name SEPARATOR ', ') AS authors
        FROM Book b
        LEFT JOIN Book_Genre bg   ON bg.book_id = b.book_id
        LEFT JOIN Genre g         ON g.genre_id = bg.genre_id
        LEFT JOIN Book_Author ba  ON ba.book_id = b.book_id
        LEFT JOIN Author a        ON a.author_id = ba.author_id
        {where_sql}
        GROUP BY b.book_id
        ORDER BY b.book_id
        LIMIT %s OFFSET %s
    """


    data_params = params + [per_page, offset]

    cursor.execute(data_sql, data_params)
    books = cursor.fetchall()

    has_prev = page > 1
    has_next = page < total_pages

    return render_template(
        "books.html",
        books=books,
        page=page,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        search_id=search_id,
        search_isbn=search_isbn,
        search_title=search_title,
        search_publisher=search_publisher,
        search_publication_date=search_publication_date,
        search_language=search_language,
        search_physical_description=search_physical_description,
        search_summary=search_summary,
        search_page_number=search_page_number,
        search_genre=search_genre,
        all_genres=all_genres,
        all_authors=all_authors
    )

@librarian_bp.route("/books/delete/<int:book_id>", methods=["POST"], endpoint="delete_book")
def delete_book(book_id):
    check = librarian_required()
    if check:
        return check

    cursor = get_cursor()
    cursor.execute("DELETE FROM Book WHERE book_id = %s", (book_id,))
    mysql.connection.commit()
    system_log("Catalog", "INFO", "BookService", f"Book deleted (book_id={book_id}).")
    flash("Book deleted successfully.", "success")

    return redirect(url_for("librarian.books"))

@librarian_bp.route("/books/edit", methods=["POST"], endpoint="edit_book")
def edit_book():
    check = librarian_required()
    if check:
        return check

    book_id = request.form.get("book_id")
    isbn = (request.form.get("isbn") or "").strip()
    title = (request.form.get("title") or "").strip()
    publisher = (request.form.get("publisher") or "").strip()
    publication_date = (request.form.get("publication_date") or "").strip()
    language = (request.form.get("language") or "").strip()
    physical_description = (request.form.get("physical_description") or "").strip()
    summary = (request.form.get("summary") or "").strip()
    page_number = (request.form.get("page_number") or "").strip()
    genre_ids = request.form.getlist("genre_ids")
    author_ids = request.form.getlist("author_ids")

    if not book_id:
        flash("Invalid book.", "danger")
        return redirect(url_for("librarian.books"))

    if not isbn:
        flash("ISBN is required.", "danger")
        return redirect(url_for("librarian.books"))
    elif not title:
        flash("Title is required.", "danger")
        return redirect(url_for("librarian.books"))
    elif not publisher:
        flash("Publisher is required.", "danger")
        return redirect(url_for("librarian.books"))
    elif not publication_date:
        flash("Publication date is required.", "danger")
        return redirect(url_for("librarian.books"))
    elif not language:
        flash("Language is required.", "danger")
        return redirect(url_for("librarian.books"))
    elif not physical_description:
        flash("Physical description is required.", "danger")
        return redirect(url_for("librarian.books"))
    elif not summary:
        flash("Summary is required.", "danger")
        return redirect(url_for("librarian.books"))
    elif not page_number:
        flash("Page number is required.", "danger")
        return redirect(url_for("librarian.books"))
    elif not genre_ids:
        flash("At least one genre is required.", "danger")
        return redirect(url_for("librarian.books"))
    elif not author_ids:
        flash("At least one author is required.", "danger")
        return redirect(url_for("librarian.books"))

    cursor = get_cursor()

    # Update Book
    cursor.execute(
        """
        UPDATE Book
        SET isbn=%s,
            title=%s,
            publisher=%s,
            publication_date=%s,
            language=%s,
            physical_description=%s,
            summary=%s,
            page_number=%s
        WHERE book_id = %s
        """,
        (isbn, title, publisher, publication_date, language,
         physical_description, summary, page_number, book_id)
    )

    # Remove old genres & authors
    cursor.execute(
        "DELETE FROM Book_Genre WHERE book_id = %s",
        (book_id,)
    )
    cursor.execute(
        "DELETE FROM Book_Author WHERE book_id = %s",
        (book_id,)
    )

    # Insert new genres & authors
    cursor.executemany(
        "INSERT INTO Book_Genre (book_id, genre_id) VALUES (%s, %s)",
        [(book_id, gid) for gid in genre_ids]
    )
    cursor.executemany(
        "INSERT INTO Book_Author (book_id, author_id) VALUES (%s, %s)",
        [(book_id, aid) for aid in author_ids]
    )

    mysql.connection.commit()
    system_log("Catalog", "INFO", "BookService", f"Book updated (book_id={book_id}).")
    flash("Book updated successfully.", "success")

    return redirect(url_for("librarian.books"))


# Helpers
def paginate(page: int, per_page: int, total: int):
    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
    page = max(1, min(page, total_pages))
    offset = (page - 1) * per_page
    return page, total_pages, offset, (page > 1), (page < total_pages)

def build_like_filters(spec, args, table_alias=""):
    """
    spec: list of tuples -> (arg_name, sql_expr, cast_int_to_char_bool)
    returns: (where_sql, params, values_dict)
    """
    where, params, values = [], [], {}
    for arg_name, sql_expr, _cast in spec:
        val = (args.get(arg_name) or "").strip()
        values[arg_name] = val
        if not val:
            continue
        where.append(f"{sql_expr} LIKE %s")
        params.append(f"%{val}%")
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    return where_sql, params, values


###---------------------------- USER MANAGEMENT SYSTEM ----------------------------###
@librarian_bp.route("/user_management", methods=["GET", "POST"], endpoint="user_management")
def user_management():
    check = librarian_required()
    if check:
        return check
    
    cursor = get_cursor()

    # Load all policies for dropdown
    cursor.execute("SELECT policy_id, name FROM Policy ORDER BY name")
    all_policies = cursor.fetchall()
    start_item = 0
    end_item = 0

    # ---------- CREATE (POST) ----------
    if request.method == "POST":
        add_first_name = (request.form.get("add_first_name") or "").strip()
        add_middle_name = (request.form.get("add_middle_name") or "").strip()
        add_last_name = (request.form.get("add_last_name") or "").strip()
        add_phone_number = (request.form.get("add_phone_number") or "").strip()
        add_email = (request.form.get("add_email") or "").strip()
        add_password = request.form.get("add_password") or ""
        add_confirm_password = request.form.get("add_confirm_password") or ""
        add_status = (request.form.get("add_status") or "").strip()
        add_user_type = (request.form.get("add_user_type") or "").strip()
        add_policy = (request.form.get("add_policy") or "").strip()

        if not add_first_name:
            flash("First name is required.", "danger")
            return redirect(url_for("librarian.user_management"))
        if not add_last_name:
            flash("Last name is required.", "danger")
            return redirect(url_for("librarian.user_management"))
        if not add_phone_number:
            flash("Phone number is required.", "danger")
            return redirect(url_for("librarian.user_management"))
        if not add_email:
            flash("Email is required.", "danger")
            return redirect(url_for("librarian.user_management"))
        if not add_password.strip():
            flash("Password is required.", "danger")
            return redirect(url_for("librarian.user_management"))
        if add_password != add_confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("librarian.user_management"))
        if len(add_password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return redirect(url_for("librarian.user_management"))
        if not add_status:
            flash("Status is required.", "danger")
            return redirect(url_for("librarian.user_management"))
        if not add_user_type:
            flash("User type is required.", "danger")
            return redirect(url_for("librarian.user_management"))
        if add_user_type == "Reader" and not add_policy:
            flash("Policy is required for readers.", "danger")
            return redirect(url_for("librarian.user_management"))

        # Duplicate checks (like your register)
        cursor.execute("SELECT 1 FROM User WHERE user_email = %s", (add_email,))
        if cursor.fetchone():
            flash("Email already used.", "danger")
            return redirect(url_for("librarian.user_management"))

        if add_phone_number:
            cursor.execute("SELECT 1 FROM User WHERE user_phone_number = %s", (add_phone_number,))
            if cursor.fetchone():
                flash("Phone number already used.", "danger")
                return redirect(url_for("librarian.user_management"))

        # IMPORTANT: store hashed password to match your login SHA2 check
        cursor.execute("""
            INSERT INTO User (
                user_first_name, user_middle_name, user_last_name,
                user_phone_number, user_email, user_password,
                status, user_type
            )
            VALUES (%s, %s, %s, %s, %s, SHA2(%s, 256), %s, %s)
        """, (
            add_first_name, add_middle_name, add_last_name,
            add_phone_number, add_email, add_password,
            add_status, add_user_type
        ))
        mysql.connection.commit()
        new_user_id = cursor.lastrowid
        if add_user_type == "Reader":
            cursor.execute(
                "INSERT INTO Reader (reader_id, policy_id) VALUES (%s, %s)",
                (new_user_id, add_policy)
            )
            mysql.connection.commit()
        system_log("Users", "INFO", "UserService", f"User created (user_id={new_user_id}).")

        flash("User created successfully.", "success")
        return redirect(url_for("librarian.user_management"))

    # ---------- LIST + SEARCH (GET) ----------
    page = request.args.get("page", 1, type=int)
    per_page = 10

    # make sure they are strings, not None
    search_id = (request.args.get("search_id") or "").strip()
    search_full_name = (request.args.get("search_full_name") or "").strip()
    search_email = (request.args.get("search_email") or "").strip()
    search_status = request.args.get("search_status")
    search_user_type = request.args.get("search_user_type")
    search_policy = (request.args.get("search_policy") or "").strip()
    where = []
    params = []

    if search_id:
        where.append("CAST(u.user_id AS CHAR) LIKE %s")
        params.append(f"%{search_id}%")

    if search_full_name:
        where.append("CONCAT(u.user_first_name, ' ', IFNULL(u.user_middle_name, ''), ' ', u.user_last_name) LIKE %s")
        params.append(f"%{search_full_name}%")

    if search_email:
        where.append("CAST(u.user_email AS CHAR) LIKE %s")
        params.append(f"%{search_email}%")

    if search_status:
        where.append("u.status = %s")
        params.append(search_status)

    if search_user_type:
        where.append("u.user_type = %s")
        params.append(search_user_type)

    if search_policy:
        where.append("p.policy_id = %s")
        params.append(search_policy)

    where_sql = " WHERE " + " AND ".join(where) if where else ""
    # total count (for pagination)
    count_sql = f"""
    SELECT COUNT(DISTINCT u.user_id) AS total
    FROM User u
    LEFT JOIN Reader r ON r.reader_id = u.user_id
    LEFT JOIN Policy p ON p.policy_id = r.policy_id
    {where_sql}
    """

    cursor.execute(count_sql, params)
    row = cursor.fetchone()
    total = row["total"] if row else 0

    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    offset = (page - 1) * per_page

    if total:
        start_item = (page - 1) * per_page + 1
        end_item = min(total, page * per_page)
    else:
        start_item = 0
        end_item = 0
    
    # data query
    data_sql = f"""
        SELECT 
            u.user_id,
            u.user_first_name,
            u.user_middle_name,
            u.user_last_name,
            u.user_phone_number,
            u.user_email,
            u.status,
            u.user_type,
            r.policy_id,
            p.name AS policy_name
        FROM User u
        LEFT JOIN Reader r ON r.reader_id = u.user_id
        LEFT JOIN Policy p ON p.policy_id = r.policy_id
        {where_sql}
        ORDER BY u.user_id
        LIMIT %s OFFSET %s
    """

    data_params = params + [per_page, offset]

    cursor.execute(data_sql, data_params)
    users = cursor.fetchall()

    has_prev = page > 1
    has_next = page < total_pages

    return render_template(
            "user_management.html",
            users=users,
            page=page,
            total_pages=total_pages,
            has_prev=has_prev,
            has_next=has_next,
            search_id=search_id,
            search_full_name=search_full_name,
            search_email=search_email,
            search_status=search_status,
            search_user_type=search_user_type,
            search_policy=search_policy,
            all_policies=all_policies,
            total_count=total,
            start_item=start_item,
            end_item=end_item
        )

@librarian_bp.route("/user_management/delete/<int:user_id>", methods=["POST"], endpoint="delete_user")
def delete_user(user_id):
    check = librarian_required()
    if check:
        return check

    cursor = get_cursor()
    cursor.execute("DELETE FROM User WHERE user_id = %s", (user_id,))
    mysql.connection.commit()
    system_log("Users", "INFO", "UserService", f"User deleted (user_id={user_id}).")
    flash("User deleted successfully.", "success")

    return redirect(url_for("librarian.user_management"))

@librarian_bp.route("/user_management/edit", methods=["POST"], endpoint="edit_user")
def edit_user():
    check = librarian_required()
    if check:
        return check

    user_id = request.form.get("user_id")

    first_name = (request.form.get("first_name") or "").strip()
    middle_name = (request.form.get("middle_name") or "").strip()
    last_name = (request.form.get("last_name") or "").strip()
    phone_number = (request.form.get("phone_number") or "").strip()
    email = (request.form.get("email") or "").strip()
    status = (request.form.get("status") or "").strip()
    user_type = (request.form.get("user_type") or "").strip()
    policy_id = (request.form.get("policy_id") or "").strip()

    password = request.form.get("password") or ""
    confirm_password = request.form.get("confirm_password") or ""

    if not user_id:
        flash("Invalid user.", "danger")
        return redirect(url_for("librarian.user_management"))
    if not first_name:
        flash("First name is required.", "danger")
        return redirect(url_for("librarian.user_management"))
    if not last_name:
        flash("Last name is required.", "danger")
        return redirect(url_for("librarian.user_management"))
    if not phone_number:
        flash("Phone number is required.", "danger")
        return redirect(url_for("librarian.user_management"))
    if not email:
        flash("Email is required.", "danger")
        return redirect(url_for("librarian.user_management"))
    if not status:
        flash("Status is required.", "danger")
        return redirect(url_for("librarian.user_management"))
    if not user_type:
        flash("User type is required.", "danger")
        return redirect(url_for("librarian.user_management"))
    if user_type == "Reader" and not policy_id:
        flash("Policy is required for readers.", "danger")
        return redirect(url_for("librarian.user_management"))

    # If password was provided, validate it
    should_update_password = bool(password.strip())
    if should_update_password:
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("librarian.user_management"))
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return redirect(url_for("librarian.user_management"))

    cursor = get_cursor()

    # Duplicate checks (like your register)
    cursor.execute("SELECT 1 FROM User WHERE user_email = %s AND user_id != %s", (email, user_id))
    if cursor.fetchone():
        flash("Email already used.", "danger")
        return redirect(url_for("librarian.user_management"))

    cursor.execute("SELECT 1 FROM User WHERE user_phone_number = %s AND user_id != %s", (phone_number, user_id))
    if cursor.fetchone():
        flash("Phone number already used.", "danger")
        return redirect(url_for("librarian.user_management"))

    if should_update_password:
        cursor.execute("""
            UPDATE User
            SET user_first_name=%s,
                user_middle_name=%s,
                user_last_name=%s,
                user_phone_number=%s,
                status=%s,
                user_type=%s,
                user_password=SHA2(%s, 256)
            WHERE user_id=%s
        """, (first_name, middle_name, last_name, phone_number, status, user_type, password, user_id))
    else:
        cursor.execute("""
            UPDATE User
            SET user_first_name=%s,
                user_middle_name=%s,
                user_last_name=%s,
                user_phone_number=%s,
                status=%s,
                user_type=%s
            WHERE user_id=%s
        """, (first_name, middle_name, last_name, phone_number, status, user_type, user_id))

    if user_type == "Reader":
        cursor.execute("""
            INSERT INTO Reader (reader_id, policy_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE policy_id = VALUES(policy_id)
        """, (user_id, policy_id))

    user_log_activity(
        session.get("userid"),
        "Update User",
        f"Librarian {session.get('username', '')} updated user ID {user_id}."
    )

    mysql.connection.commit()
    system_log("Users", "INFO", "UserService", f"User updated (user_id={user_id}).")
    flash("User updated successfully.", "success")
    return redirect(url_for("librarian.user_management"))
