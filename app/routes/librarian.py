from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import MySQLdb.cursors
from extensions import mysql
from math import ceil
import logging; 
librarian_bp = Blueprint("librarian", __name__, url_prefix="/librarian")

def get_cursor():
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)

def librarian_required():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    if session.get('user_type') != 'Librarian':
        return "Forbidden", 403
    return None

###---------------------------- AUTHORS MANAGEMENT----------------------------###
@librarian_bp.route("/authors", methods=["GET", "POST"], endpoint="authors")
def authors():
    check = librarian_required()
    if check:
        return check

    cursor = get_cursor()

    # ---------- CREATE (POST) ----------
    if request.method == "POST":
        author_name = (request.form.get("author_name") or "").strip()

        if not author_name:
            flash("Author name is required.", "danger")
        else:
            cursor.execute(
                "INSERT INTO Author (author_name) VALUES (%s)",
                (author_name,)
            )
            mysql.connection.commit()
            flash("Author created successfully.", "success")

        return redirect(url_for("librarian.authors"))

    # ---------- LIST + SEARCH (GET) ----------
    page = request.args.get("page", 1, type=int)
    per_page = 10

    # make sure they are strings, not None
    search_id = (request.args.get("search_id") or "").strip()
    search_name = (request.args.get("search_name") or "").strip()

    where = []
    params = []

    if search_id:
        where.append("CAST(author_id AS CHAR) LIKE %s")
        params.append(f"%{search_id}%")

    if search_name:
        where.append("author_name LIKE %s")
        params.append(f"%{search_name}%")

    where_sql = " WHERE " + " AND ".join(where) if where else ""
    logging.info("HELLO FROM DOCKER")
    # total count (for pagination)
    count_sql = f"SELECT COUNT(*) AS total FROM Author {where_sql}"
    cursor.execute(count_sql, params)
    row = cursor.fetchone()
    total = row["total"] if row else 0

    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    offset = (page - 1) * per_page

    # data query
    data_sql = f"""
        SELECT author_id, author_name
        FROM Author
        {where_sql}
        ORDER BY author_id
        LIMIT %s OFFSET %s
    """
    data_params = params + [per_page, offset]

    cursor.execute(data_sql, data_params)
    authors = cursor.fetchall()

    has_prev = page > 1
    has_next = page < total_pages

    return render_template(
        "authors.html",
        authors=authors,
        page=page,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        search_id=search_id,
        search_name=search_name,
    )

@librarian_bp.route("/authors/delete/<int:author_id>", methods=["POST"], endpoint="delete_author")
def delete_author(author_id):
    check = librarian_required()
    if check:
        return check

    cursor = get_cursor()
    cursor.execute("DELETE FROM Author WHERE author_id = %s", (author_id,))
    mysql.connection.commit()
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
    flash("Author updated successfully.", "success")

    return redirect(url_for("librarian.authors"))

###---------------------------- GENRE MANAGEMENT----------------------------###
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
            cursor.execute(
                "INSERT INTO Genre (genre_name) VALUES (%s)",
                (genre_name,)
            )
            mysql.connection.commit()
            flash("Genre created successfully.", "success")

        return redirect(url_for("librarian.genres"))

    # ---------- LIST + SEARCH (GET) ----------
    page = request.args.get("page", 1, type=int)
    per_page = 10

    # make sure they are strings, not None
    search_id = (request.args.get("search_id") or "").strip()
    search_name = (request.args.get("search_name") or "").strip()

    where = []
    params = []

    if search_id:
        where.append("CAST(genre_id AS CHAR) LIKE %s")
        params.append(f"%{search_id}%")

    if search_name:
        where.append("genre_name LIKE %s")
        params.append(f"%{search_name}%")

    where_sql = " WHERE " + " AND ".join(where) if where else ""
    logging.info("HELLO FROM DOCKER")
    # total count (for pagination)
    count_sql = f"SELECT COUNT(*) AS total FROM Genre {where_sql}"
    cursor.execute(count_sql, params)
    row = cursor.fetchone()
    total = row["total"] if row else 0

    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    offset = (page - 1) * per_page

    # data query
    data_sql = f"""
        SELECT genre_id, genre_name
        FROM Genre
        {where_sql}
        ORDER BY genre_id
        LIMIT %s OFFSET %s
    """
    data_params = params + [per_page, offset]

    cursor.execute(data_sql, data_params)
    genres = cursor.fetchall()

    has_prev = page > 1
    has_next = page < total_pages

    return render_template(
        "genres.html",
        genres=genres,
        page=page,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        search_id=search_id,
        search_name=search_name,
    )

@librarian_bp.route("/genres/delete/<int:genre_id>", methods=["POST"], endpoint="delete_genre")
def delete_genre(genre_id):
    check = librarian_required()
    if check:
        return check

    cursor = get_cursor()
    cursor.execute("DELETE FROM Genre WHERE genre_id = %s", (genre_id,))
    mysql.connection.commit()
    flash("Genre deleted successfully.", "success")

    return redirect(url_for("librarian.genres"))


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
    flash("Genre updated successfully.", "success")

    return redirect(url_for("librarian.genres"))