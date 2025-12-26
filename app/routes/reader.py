from flask import Blueprint, request, redirect, url_for, flash, session
from extensions import mysql
from utils.system_log import system_log
from routes.notifications import notify_request_librarian

reader_bp = Blueprint("reader", __name__, url_prefix="/reader")

@reader_bp.route("/requests/create", methods=["POST"])
def create_request():
    check = reader_required()
    if check:
        return check
    
    reader_id = session.get("user_id")
    request_type = request.form.get("request_type")
    book_id = request.form.get("book_id")
    material_id = request.form.get("material_id")

    cursor = get_cursor()

    cursor.execute("""
        INSERT INTO Request (request_type, reader_id, book_id, material_id, status)
        VALUES (%s, %s, %s, %s, 'Pending')
    """, (request_type, reader_id, book_id, material_id))
    
    mysql.connection.commit()

    request_id = cursor.lastrowid

    notify_request_librarian(request_id)

    flash("Request submitted successfully.", "success")
    return redirect(url_for("reader.requests"))
