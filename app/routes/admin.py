# routes/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, session
import MySQLdb.cursors
from extensions import mysql

admin_bp = Blueprint('admin', __name__)

def get_cursor():
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)


def admin_required():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
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
    start_date = request.args.get('start_date') or ''
    end_date = request.args.get('end_date') or ''

    cursor.execute("SELECT DISTINCT source FROM Log ORDER BY source;")
    sources = [row['source'] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT log_level FROM Log ORDER BY log_level;")
    log_levels = [row['log_level'] for row in cursor.fetchall()]

    query = """
        SELECT
            log_date,
            source,
            log_level,
            log_node,
            log_message
        FROM Log
    """
    conditions = []
    params = []

    if selected_source:
        conditions.append("source = %s")
        params.append(selected_source)

    if selected_level:
        conditions.append("log_level = %s")
        params.append(selected_level)

    if start_date:
        conditions.append("log_date >= %s")
        params.append(start_date)

    if end_date:
        conditions.append("log_date < DATE_ADD(%s, INTERVAL 1 DAY)")
        params.append(end_date)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY log_date DESC;"

    cursor.execute(query, tuple(params))
    logs = cursor.fetchall()

    return render_template(
        'system_logs.html',
        logs=logs,
        sources=sources,
        log_levels=log_levels,
        selected_source=selected_source,
        selected_level=selected_level,
        start_date=start_date,
        end_date=end_date
    )


@admin_bp.route('/user_activity', methods=['GET'], endpoint='user_activity')
def user_activity():
    check = admin_required()
    if check:
        return check

    cursor = get_cursor()

    action_type = request.args.get('action_type') or ''
    user_query = request.args.get('user_query') or ''
    start_date = request.args.get('start_date') or ''
    end_date = request.args.get('end_date') or ''

    cursor.execute("SELECT DISTINCT action_type FROM user_activity_log ORDER BY action_type;")
    action_types = [row['action_type'] for row in cursor.fetchall()]

    query = """
        SELECT
          l.action_date,
          u.user_id,
          l.action_type,
          l.details
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

    if start_date:
        conditions.append("l.action_date >= %s")
        params.append(start_date)

    if end_date:
        conditions.append("l.action_date < DATE_ADD(%s, INTERVAL 1 DAY)")
        params.append(end_date)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY l.action_date DESC"

    cursor.execute(query, params)
    logs = cursor.fetchall()

    return render_template(
        'user_activity.html',
        logs=logs,
        action_types=action_types,
        selected_action=action_type,
        user_query=user_query,
        start_date=start_date,
        end_date=end_date
    )
