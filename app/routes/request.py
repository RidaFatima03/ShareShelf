from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import MySQLdb.cursors
from extensions import mysql
from utils.system_log import system_log

request_bp = Blueprint("request", __name__, url_prefix="/request")

def get_cursor():
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)

@request_bp.route("/my_requests", methods=["GET"], endpoint="my_requests")
def my_requests():
    if "loggedin" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["userid"]
    cursor = get_cursor()

    tabs = ["holds", "borrows", "book_requests", "exchanges", "donations"]
    active_tab = (request.args.get("tab") or "borrows").strip() or "borrows"
    if active_tab not in tabs:
        active_tab = "borrows"

    def get_tab_values(tab):
        title_val = (request.args.get(f"search_title_{tab}") or "").strip()
        author_val = (request.args.get(f"search_author_{tab}") or "").strip()
        date_val = (request.args.get(f"search_date_{tab}") or "").strip()
        status_val = (request.args.get(f"search_status_{tab}") or "").strip()

        if tab == active_tab:
            if not title_val:
                title_val = (request.args.get("search_title") or "").strip()
            if not author_val:
                author_val = (request.args.get("search_author") or "").strip()
            if not date_val:
                date_val = (request.args.get("search_date") or "").strip()
            if not status_val:
                status_val = (request.args.get("search_status") or "").strip()

        return {
            "title": title_val,
            "author": author_val,
            "date": date_val,
            "status": status_val,
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

        where_sql = (" AND " + " AND ".join(where)) if where else ""
        return where_sql, params

    # HOLDS
    where_sql, params = build_request_filters("b.title", "a.author_name", search_values["holds"], active_tab == "holds")
    cursor.execute(f"""
        SELECT r.request_id, r.request_date, r.status, b.title AS item_title,
               GROUP_CONCAT(DISTINCT a.author_name SEPARATOR ', ') AS item_author
        FROM Request r
        JOIN Book b ON r.book_id = b.book_id
        LEFT JOIN Book_Author ba ON b.book_id = ba.book_id
        LEFT JOIN Author a ON ba.author_id = a.author_id
        WHERE r.reader_id = %s AND r.request_type = 'Hold'{where_sql}
        GROUP BY r.request_id, b.title, r.request_date, r.status
        ORDER BY r.request_date DESC
    """, [user_id] + params)
    holds = cursor.fetchall()

    # BORROWS
    where_sql, params = build_request_filters("b.title", "a.author_name", search_values["borrows"], active_tab == "borrows")
    cursor.execute(f"""
        SELECT r.request_id, r.request_date, r.status, b.title AS item_title,
               GROUP_CONCAT(DISTINCT a.author_name SEPARATOR ', ') AS item_author
        FROM Request r
        JOIN Book b ON r.book_id = b.book_id
        LEFT JOIN Book_Author ba ON b.book_id = ba.book_id
        LEFT JOIN Author a ON ba.author_id = a.author_id
        WHERE r.reader_id = %s AND r.request_type = 'Borrow'{where_sql}
        GROUP BY r.request_id, b.title, r.request_date, r.status
        ORDER BY r.request_date DESC
    """, [user_id] + params)
    borrows = cursor.fetchall()

    # EXCHANGES
    where_sql, params = build_request_filters("b.title", "a.author_name", search_values["exchanges"], active_tab == "exchanges")
    cursor.execute(f"""
        SELECT r.request_id, r.request_date, r.status, b.title AS item_title,
               GROUP_CONCAT(DISTINCT a.author_name SEPARATOR ', ') AS item_author
        FROM Request r
        JOIN Book b ON r.book_id = b.book_id
        LEFT JOIN Book_Author ba ON b.book_id = ba.book_id
        LEFT JOIN Author a ON ba.author_id = a.author_id
        WHERE r.reader_id = %s AND r.request_type = 'Exchange'{where_sql}
        GROUP BY r.request_id, b.title, r.request_date, r.status
        ORDER BY r.request_date DESC
    """, [user_id] + params)
    exchanges = cursor.fetchall()

    # DONATIONS (Book)
    where_sql, params = build_request_filters("b.title", "a.author_name", search_values["donations"], active_tab == "donations")
    cursor.execute(f"""
        SELECT r.request_id, r.request_date, r.status, b.isbn, b.title AS item_title, b.publisher, b.publication_date,
               GROUP_CONCAT(DISTINCT a.author_name SEPARATOR ', ') AS item_author
        FROM Request r
        JOIN Book b ON r.book_id = b.book_id
        LEFT JOIN Book_Author ba ON b.book_id = ba.book_id
        LEFT JOIN Author a ON ba.author_id = a.author_id
        WHERE r.reader_id = %s AND r.request_type = 'Donation' AND r.book_id IS NOT NULL{where_sql}
        GROUP BY r.request_id, b.title, r.request_date, r.status
    """, [user_id] + params)
    donations_books = cursor.fetchall()

    # DONATIONS (Material)
    where_sql, params = build_request_filters("m.title", "m.author", search_values["donations"], active_tab == "donations")
    cursor.execute(f"""
        SELECT r.request_id, r.request_date, r.status, m.isbn, m.title AS item_title, m.publisher, m.publication_date, m.author AS item_author
        FROM Request r
        JOIN Material m ON r.material_id = m.material_id
        WHERE r.reader_id = %s AND r.request_type = 'Donation' AND r.material_id IS NOT NULL{where_sql}
    """, [user_id] + params)
    donations_materials = cursor.fetchall()

    donations = list(donations_books) + list(donations_materials)
    donations.sort(key=lambda x: x["request_date"], reverse=True)

    # BOOK REQUESTS (Material)
    where_sql, params = build_request_filters("m.title", "m.author", search_values["book_requests"], active_tab == "book_requests")
    cursor.execute(f"""
        SELECT r.request_id, r.request_date, r.status, m.isbn, m.title AS item_title, m.publisher, m.publication_date, m.author AS item_author
        FROM Request r
        JOIN Material m ON r.material_id = m.material_id
        WHERE r.reader_id = %s AND r.request_type = 'Book Request'{where_sql}
        ORDER BY r.request_date DESC
    """, [user_id] + params)
    book_requests = cursor.fetchall()

    counts = {
        "holds": len(holds),
        "borrows": len(borrows),
        "book_requests": len(book_requests),
        "exchanges": len(exchanges),
        "donations": len(donations),
    }
    active_count = counts.get(active_tab, 0)

    return render_template(
        "my-requests.html",
        holds=holds,
        borrows=borrows,
        book_requests=book_requests,
        exchanges=exchanges,
        donations=donations,
        active_tab=active_tab,
        search_values=search_values,
        active_values=active_values,
        total_count=active_count
    )

@request_bp.route("/new_request", methods=["POST"], endpoint="new_request")
def new_request():
    if "loggedin" not in session:
        return redirect(url_for("auth.login"))

    cursor = get_cursor()

    add_request_type = (request.form.get("add_request_type") or "").strip()
    add_isbn = (request.form.get("add_isbn") or "").strip()
    add_title = (request.form.get("add_title") or "").strip()
    add_publisher = (request.form.get("add_publisher") or "").strip()
    add_publication_date = (request.form.get("add_publication_date") or "").strip()
    add_author = (request.form.get("add_author") or "").strip()

    allowed = {"Book Request", "Donation"}
    if add_request_type not in allowed:
        flash("Invalid request type.", "danger")
        return redirect(url_for("request.my_requests"))

    if not add_isbn or not add_title or not add_publisher or not add_publication_date or not add_author:
        flash("All fields are required.", "danger")
        return redirect(url_for("request.my_requests"))

    cursor.execute("""
        INSERT INTO Material (isbn, title, publisher, publication_date, author)
        VALUES (%s, %s, %s, %s, %s)
    """, (add_isbn, add_title, add_publisher, add_publication_date, add_author))
    mysql.connection.commit()

    material_id = cursor.lastrowid
    reader_id = session["userid"]

    cursor.execute("""
        INSERT INTO Request (request_type, material_id, reader_id, expire_date)
        VALUES (%s, %s, %s, DATE_ADD(NOW(), INTERVAL 14 DAY))
    """, (add_request_type, material_id, reader_id))
    mysql.connection.commit()

    request_id = cursor.lastrowid
    system_log(
        "Requests",
        "INFO",
        "RequestService",
        f"Request created (request_id={request_id}, material_id={material_id})."
    )
    flash("Request created successfully.", "success")
    return redirect(url_for("request.my_requests"))

@request_bp.route("/cancel_request/<int:request_id>", methods=["POST"], endpoint="cancel_request")
def cancel_request(request_id):
    if "loggedin" not in session:
        return redirect(url_for("auth.login"))

    reader_id = session["userid"]
    cursor = get_cursor()

    cursor.execute("""
        SELECT status
        FROM Request
        WHERE request_id = %s AND reader_id = %s
    """, (request_id, reader_id))
    req = cursor.fetchone()

    if not req:
        flash("Request not found.", "danger")
        return redirect(url_for("request.my_requests"))

    if req["status"] != "Pending":
        flash("Only pending requests can be cancelled.", "danger")
        return redirect(url_for("request.my_requests"))

    cursor.execute("""
        UPDATE Request
        SET status = 'Cancelled'
        WHERE request_id = %s
    """, (request_id,))
    mysql.connection.commit()

    system_log("Requests", "INFO", "RequestService", f"Request cancelled (request_id={request_id}).")
    flash("Request cancelled successfully.", "success")
    return redirect(url_for("request.my_requests"))

@request_bp.route("/history/<int:request_id>", methods=["GET"], endpoint="request_history")
def request_history(request_id):
    if "loggedin" not in session:
        return redirect(url_for("auth.login"))

    reader_id = session["userid"]
    cursor = get_cursor()
    cursor.execute("""
        SELECT r.request_id
        FROM Request r
        WHERE r.request_id = %s AND r.reader_id = %s
    """, (request_id, reader_id))
    req = cursor.fetchone()
    if not req:
        return jsonify([]), 404

    cursor.execute("""
        SELECT status, changed_at
        FROM Request_Status_History
        WHERE request_id = %s
        ORDER BY changed_at
    """, (request_id,))
    history = cursor.fetchall() or []
    return jsonify(history)
