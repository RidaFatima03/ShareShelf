# routes/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, session
import math
import MySQLdb.cursors
from extensions import mysql

admin_bp = Blueprint('admin', __name__)

def get_cursor():
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)


def admin_required():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    if session.get('user_type') != 'Admin':
        return "Forbidden", 403
    return None


@admin_bp.route('/system_logs', methods=['GET'], endpoint='system_logs')
def system_logs():
    check = admin_required()
    if check:
        return check

    cursor = get_cursor()

    selected_source = request.args.get('source') or ''
    selected_level = request.args.get('log_level') or ''
    node_query = request.args.get('node_query') or ''
    message_query = request.args.get('message_query') or ''
    start_date = request.args.get('start_date') or ''
    end_date = request.args.get('end_date') or ''
    page = request.args.get('page', default=1, type=int)
    per_page = 10
    if page < 1:
        page = 1

    cursor.execute("SELECT DISTINCT source FROM Log ORDER BY source;")
    sources = [row['source'] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT log_level FROM Log ORDER BY log_level;")
    log_levels = [row['log_level'] for row in cursor.fetchall()]

    query = """
        SELECT
            log_id,
            log_date,
            source,
            log_level,
            log_node,
            log_message
        FROM Log
    """
    count_query = "SELECT COUNT(*) AS total FROM Log"
    conditions = []
    params = []

    if selected_source:
        conditions.append("source = %s")
        params.append(selected_source)

    if selected_level:
        conditions.append("log_level = %s")
        params.append(selected_level)

    if node_query:
        conditions.append("log_node LIKE %s")
        params.append(f"%{node_query}%")

    if message_query:
        conditions.append("log_message LIKE %s")
        params.append(f"%{message_query}%")

    if start_date:
        conditions.append("log_date >= %s")
        params.append(start_date)

    if end_date:
        conditions.append("log_date < DATE_ADD(%s, INTERVAL 1 DAY)")
        params.append(end_date)

    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)
        query += where_clause
        count_query += where_clause

    query += " ORDER BY log_date DESC LIMIT %s OFFSET %s"
    params_with_page = params + [per_page, (page - 1) * per_page]

    cursor.execute(count_query, tuple(params))
    total_count = cursor.fetchone().get('total', 0)
    total_pages = max(1, math.ceil(total_count / per_page)) if total_count else 1
    if page > total_pages:
        page = total_pages
        params_with_page = params + [per_page, (page - 1) * per_page]
    start_index = 0 if total_count == 0 else (page - 1) * per_page + 1
    end_index = 0 if total_count == 0 else min(page * per_page, total_count)

    cursor.execute(query, tuple(params_with_page))
    logs = cursor.fetchall()

    return render_template(
        'system_logs.html',
        logs=logs,
        sources=sources,
        log_levels=log_levels,
        selected_source=selected_source,
        selected_level=selected_level,
        start_date=start_date,
        end_date=end_date,
        node_query=node_query,
        message_query=message_query,
        total_count=total_count,
        start_index=start_index,
        end_index=end_index,
        page=page,
        total_pages=total_pages,
        has_prev=page > 1,
        has_next=page < total_pages
    )


@admin_bp.route('/user_activity', methods=['GET'], endpoint='user_activity')
def user_activity():
    check = admin_required()
    if check:
        return check

    cursor = get_cursor()

    action_type = request.args.get('action_type') or ''
    user_query = request.args.get('user_query') or ''
    description_query = request.args.get('description_query') or ''
    start_date = request.args.get('start_date') or ''
    end_date = request.args.get('end_date') or ''
    page = request.args.get('page', default=1, type=int)
    per_page = 10
    if page < 1:
        page = 1

    cursor.execute("SELECT DISTINCT action_type FROM user_activity_log ORDER BY action_type;")
    action_types = [row['action_type'] for row in cursor.fetchall()]

    query = """
        SELECT
          l.log_id,
          l.action_date,
          u.user_id,
          l.action_type,
          l.details
        FROM user_activity_log AS l
        JOIN User AS u ON u.user_id = l.user_id
    """

    count_query = """
        SELECT COUNT(*) AS total
        FROM user_activity_log AS l
        JOIN User AS u ON u.user_id = l.user_id
    """
    conditions = []
    params = []

    if action_type:
        conditions.append("l.action_type = %s")
        params.append(action_type)

    if user_query:
        conditions.append("u.user_id = %s")
        params.append(user_query)

    if description_query:
        conditions.append("l.details LIKE %s")
        params.append(f"%{description_query}%")

    if start_date:
        conditions.append("l.action_date >= %s")
        params.append(start_date)

    if end_date:
        conditions.append("l.action_date < DATE_ADD(%s, INTERVAL 1 DAY)")
        params.append(end_date)

    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)
        query += where_clause
        count_query += where_clause

    query += " ORDER BY l.action_date DESC LIMIT %s OFFSET %s"
    params_with_page = params + [per_page, (page - 1) * per_page]

    cursor.execute(count_query, params)
    total_count = cursor.fetchone().get('total', 0)
    total_pages = max(1, math.ceil(total_count / per_page)) if total_count else 1
    if page > total_pages:
        page = total_pages
        params_with_page = params + [per_page, (page - 1) * per_page]
    start_index = 0 if total_count == 0 else (page - 1) * per_page + 1
    end_index = 0 if total_count == 0 else min(page * per_page, total_count)

    cursor.execute(query, params_with_page)
    logs = cursor.fetchall()

    cursor.execute("""
        UPDATE User
        SET status = 'INACTIVE'
        WHERE user_id IN (
            SELECT user_id FROM (
                SELECT u.user_id
                FROM User u
                LEFT JOIN user_activity_log l
                ON u.user_id = l.user_id
                AND l.action_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)
                GROUP BY u.user_id
                HAVING COUNT(l.action_type) = 0
            ) AS inactive_users
        );
    """)

    return render_template(
        'user_activity.html',
        logs=logs,
        action_types=action_types,
        selected_action=action_type,
        user_query=user_query,
        description_query=description_query,
        start_date=start_date,
        end_date=end_date,
        total_count=total_count,
        start_index=start_index,
        end_index=end_index,
        page=page,
        total_pages=total_pages,
        has_prev=page > 1,
        has_next=page < total_pages
    )


@admin_bp.route('/reports', methods=['GET'], endpoint='reports')
def reports():
    check = admin_required()
    if check:
        return check

    cursor = get_cursor()

    cursor.execute("""
        SELECT g.genre_name, COUNT(*) AS borrow_count
        FROM Checkout co
        JOIN Copy c ON co.copy_id = c.item_barcode
        JOIN Book_Genre bg ON c.book_id = bg.book_id
        JOIN Genre g ON bg.genre_id = g.genre_id
        GROUP BY g.genre_id, g.genre_name
        ORDER BY borrow_count DESC
        LIMIT 10
    """)
    borrowed_genres = cursor.fetchall()

    cursor.execute("""
        SELECT u.user_id,
               CONCAT(u.user_first_name, ' ', u.user_last_name) AS user_name,
               COUNT(*) AS activity_count
        FROM user_activity_log l
        JOIN User u ON l.user_id = u.user_id
        GROUP BY u.user_id, u.user_first_name, u.user_last_name
        ORDER BY activity_count DESC
        LIMIT 10
    """)
    active_users = cursor.fetchall()

    cursor.execute("""
        SELECT DATE_FORMAT(due_date, '%Y-%m') AS period,
               COUNT(*) AS overdue_count
        FROM Checkout
        WHERE due_date < NOW() AND returned_date IS NULL
        GROUP BY period
        ORDER BY period DESC
        LIMIT 12
    """)
    overdue_rows = cursor.fetchall()
    overdue_rows = list(reversed(overdue_rows))

    cursor.execute("""
        SELECT SUM(status = 'Lost') AS lost_count,
               COUNT(*) AS total_count
        FROM Copy
    """)
    lost_overall = cursor.fetchone() or {"lost_count": 0, "total_count": 0}
    lost_total = lost_overall.get("total_count") or 0
    lost_rate = (lost_overall.get("lost_count") or 0) / lost_total if lost_total else 0

    cursor.execute("""
        SELECT g.genre_name,
               SUM(c.status = 'Lost') AS lost_count,
               COUNT(*) AS total_count
        FROM Copy c
        JOIN Book_Genre bg ON c.book_id = bg.book_id
        JOIN Genre g ON bg.genre_id = g.genre_id
        GROUP BY g.genre_id, g.genre_name
        ORDER BY lost_count DESC
    """)
    lost_by_genre = cursor.fetchall()
    for row in lost_by_genre:
        total = row.get("total_count") or 0
        row["lost_rate"] = (row.get("lost_count") or 0) / total if total else 0

    return render_template(
        'admin-reports.html',
        borrowed_genres=borrowed_genres,
        active_users=active_users,
        overdue_rows=overdue_rows,
        lost_overall=lost_overall,
        lost_rate=lost_rate,
        lost_by_genre=lost_by_genre
    )


