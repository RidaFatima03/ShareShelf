from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import MySQLdb.cursors
from extensions import mysql
from utils.system_log import system_log

copies_bp = Blueprint("copies", __name__, url_prefix="/librarian/copies")


def get_cursor():
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)


def librarian_required():
    if "loggedin" not in session:
        return redirect(url_for("auth.login"))
    if session.get("user_type") != "Librarian":
        return "Forbidden", 403
    return None


def paginate(page: int, per_page: int, total: int):
    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
    page = max(1, min(page, total_pages))
    offset = (page - 1) * per_page
    return page, total_pages, offset, (page > 1), (page < total_pages)


@copies_bp.route("/", methods=["GET", "POST"], endpoint="list")
def list_copies():
    check = librarian_required()
    if check:
        return check

    cursor = get_cursor()

    cursor.execute("SELECT book_id, title FROM Book ORDER BY title")
    all_books = cursor.fetchall()

    cursor.execute("""
        SELECT location_id, direction, collection, shelf_row
        FROM Location
        ORDER BY direction, collection, shelf_row
    """)
    all_locations = cursor.fetchall()

    cursor.execute("""
        SELECT u.user_id, CONCAT(u.user_first_name, ' ', u.user_last_name) AS name
        FROM User u
        WHERE u.user_type = 'Reader'
        ORDER BY u.user_first_name, u.user_last_name
    """)
    all_readers = cursor.fetchall()

    if request.method == "POST":
        item_barcode = (request.form.get("item_barcode") or "").strip()
        call_number = (request.form.get("call_number") or "").strip()
        acquisition_type = (request.form.get("acquisition_type") or "").strip()
        status = (request.form.get("status") or "").strip()
        book_id = (request.form.get("book_id") or "").strip()
        location_id = (request.form.get("location_id") or "").strip()
        owner_id = (request.form.get("owner_id") or "").strip()

        if not item_barcode:
            flash("Barcode is required.", "danger")
            return redirect(url_for("copies.list"))
        if not acquisition_type:
            flash("Acquisition type is required.", "danger")
            return redirect(url_for("copies.list"))
        if not status:
            flash("Status is required.", "danger")
            return redirect(url_for("copies.list"))
        if not book_id:
            flash("Book is required.", "danger")
            return redirect(url_for("copies.list"))

        cursor.execute("""
            INSERT INTO Copy (
                item_barcode, call_number, acquisition_type, status,
                book_id, location_id, owner_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            item_barcode,
            call_number or None,
            acquisition_type,
            status,
            book_id,
            location_id or None,
            owner_id or None,
        ))
        mysql.connection.commit()
        system_log("Catalog", "INFO", "CopyService", f"Copy created (barcode={item_barcode}).")
        flash("Copy created successfully.", "success")
        return redirect(url_for("copies.list"))

    page = request.args.get("page", 1, type=int)
    per_page = 10

    search_barcode = (request.args.get("search_barcode") or "").strip()
    search_title = (request.args.get("search_title") or "").strip()
    search_book_id = (request.args.get("search_book_id") or "").strip()
    search_status = (request.args.get("search_status") or "").strip()
    search_acquisition = (request.args.get("search_acquisition") or "").strip()
    search_call_number = (request.args.get("search_call_number") or "").strip()
    search_location = (request.args.get("search_location") or "").strip()
    search_owner = (request.args.get("search_owner") or "").strip()

    where = []
    params = []

    if search_barcode:
        where.append("c.item_barcode LIKE %s")
        params.append(f"%{search_barcode}%")
    if search_title:
        where.append("b.title LIKE %s")
        params.append(f"%{search_title}%")
    if search_book_id:
        where.append("CAST(c.book_id AS CHAR) LIKE %s")
        params.append(f"%{search_book_id}%")
    if search_status:
        where.append("c.status = %s")
        params.append(search_status)
    if search_acquisition:
        where.append("c.acquisition_type = %s")
        params.append(search_acquisition)
    if search_call_number:
        where.append("c.call_number LIKE %s")
        params.append(f"%{search_call_number}%")
    if search_location:
        where.append("c.location_id = %s")
        params.append(search_location)
    if search_owner:
        where.append("c.owner_id = %s")
        params.append(search_owner)

    where_sql = " WHERE " + " AND ".join(where) if where else ""

    cursor.execute(f"""
        SELECT COUNT(*) AS total
        FROM Copy c
        JOIN Book b ON c.book_id = b.book_id
        LEFT JOIN Location l ON c.location_id = l.location_id
        LEFT JOIN User u ON c.owner_id = u.user_id
        {where_sql}
    """, params)
    total = (cursor.fetchone() or {}).get("total", 0)

    page, total_pages, offset, has_prev, has_next = paginate(page, per_page, total)
    if total:
        start_item = (page - 1) * per_page + 1
        end_item = min(total, page * per_page)
    else:
        start_item = 0
        end_item = 0

    cursor.execute(f"""
        SELECT
            c.item_barcode,
            c.call_number,
            c.acquisition_type,
            c.status,
            c.added_date,
            c.book_id,
            b.title AS book_title,
            c.location_id,
            CONCAT(l.direction, ' / ', l.collection, ' / ', l.shelf_row) AS location_name,
            c.owner_id,
            CONCAT(u.user_first_name, ' ', u.user_last_name) AS owner_name
        FROM Copy c
        JOIN Book b ON c.book_id = b.book_id
        LEFT JOIN Location l ON c.location_id = l.location_id
        LEFT JOIN User u ON c.owner_id = u.user_id
        {where_sql}
        ORDER BY c.added_date DESC
        LIMIT %s OFFSET %s
    """, params + [per_page, offset])
    copies = cursor.fetchall()

    return render_template(
        "copies.html",
        copies=copies,
        page=page,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        total_count=total,
        start_item=start_item,
        end_item=end_item,
        all_books=all_books,
        all_locations=all_locations,
        all_readers=all_readers,
        search_barcode=search_barcode,
        search_title=search_title,
        search_book_id=search_book_id,
        search_status=search_status,
        search_acquisition=search_acquisition,
        search_call_number=search_call_number,
        search_location=search_location,
        search_owner=search_owner,
    )


@copies_bp.route("/edit", methods=["POST"], endpoint="edit")
def edit_copy():
    check = librarian_required()
    if check:
        return check

    cursor = get_cursor()

    item_barcode = (request.form.get("item_barcode") or "").strip()
    call_number = (request.form.get("call_number") or "").strip()
    acquisition_type = (request.form.get("acquisition_type") or "").strip()
    status = (request.form.get("status") or "").strip()
    book_id = (request.form.get("book_id") or "").strip()
    location_id = (request.form.get("location_id") or "").strip()
    owner_id = (request.form.get("owner_id") or "").strip()

    if not item_barcode:
        flash("Invalid copy.", "danger")
        return redirect(url_for("copies.list"))

    cursor.execute("""
        UPDATE Copy
        SET call_number = %s,
            acquisition_type = %s,
            status = %s,
            book_id = %s,
            location_id = %s,
            owner_id = %s
        WHERE item_barcode = %s
    """, (
        call_number or None,
        acquisition_type,
        status,
        book_id,
        location_id or None,
        owner_id or None,
        item_barcode,
    ))
    mysql.connection.commit()
    system_log("Catalog", "INFO", "CopyService", f"Copy updated (barcode={item_barcode}).")
    flash("Copy updated successfully.", "success")
    return redirect(url_for("copies.list"))


@copies_bp.route("/delete/<string:item_barcode>", methods=["POST"], endpoint="delete")
def delete_copy(item_barcode):
    check = librarian_required()
    if check:
        return check

    cursor = get_cursor()
    cursor.execute("DELETE FROM Copy WHERE item_barcode = %s", (item_barcode,))
    mysql.connection.commit()
    system_log("Catalog", "INFO", "CopyService", f"Copy deleted (barcode={item_barcode}).")
    flash("Copy deleted successfully.", "success")
    return redirect(url_for("copies.list"))
