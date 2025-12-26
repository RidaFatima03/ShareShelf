from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import MySQLdb
import MySQLdb.cursors
from extensions import mysql
from utils.system_log import system_log
from routes.notifications import NotificationService

policy_bp = Blueprint('policy', __name__)

def get_cursor():
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)

@policy_bp.route('/policy', methods=['GET'])
def policy():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = get_cursor()
    user_type = session.get("user_type")
    if user_type == "Reader":
        cursor.execute("""
            SELECT p.*
            FROM Policy p
            JOIN Reader r ON r.policy_id = p.policy_id
            WHERE r.reader_id = %s
        """, (session.get("userid"),))
    elif user_type == "Librarian":
        cursor.execute("SELECT * FROM Policy")
    else:
        return "Unauthorized", 403
    policies = cursor.fetchall()
    role = user_type

    return render_template("policy.html", data=policies, role=role)

@policy_bp.route('/policy/edit/<int:id>', methods=['GET', 'POST'])
def edit_policy(id):
    if session.get('user_type') != 'Librarian':
        return "Unauthorized", 403

    cursor = get_cursor()

    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        if not name:
            flash("Policy name is required.", "danger")
            return redirect(url_for('policy.add_policy'))
        period = request.form['loan_period_days']
        renewals = request.form['renewals_allowed']
        fine = request.form['fine_per_day']
        max_loans = request.form['max_concurrent_loans']
        holds = request.form['holds_limit_reservation']

        cursor.execute("""
            UPDATE Policy
            SET name=%s, loan_period_days=%s, renewals_allowed=%s,
                fine_per_day=%s, max_concurrent_loans=%s,
                holds_limit_reservation=%s
            WHERE policy_id=%s
        """, (name, period, renewals, fine, max_loans, holds, id))

        mysql.connection.commit()
        system_log("Policy", "INFO", "PolicyService", f"Policy updated (policy_id={id}).")

        if session.get('user_type') == 'Librarian':
            cursor.execute("""
                SELECT r.reader_id, COUNT(rq.request_id) AS hold_count
                FROM Reader r
                LEFT JOIN Request rq
                  ON rq.reader_id = r.reader_id
                 AND rq.request_type = 'Hold'
                 AND rq.status IN ('Pending', 'Approved')
                WHERE r.policy_id = %s
                GROUP BY r.reader_id
                HAVING hold_count > %s
            """, (id, holds))
            over_limit = cursor.fetchall()
            if over_limit:
                service = NotificationService(mysql.connection)
                for row in over_limit:
                    service.add_notification(
                        row["reader_id"],
                        "Hold limit updated",
                        f"Your policy hold limit is now {holds}. You currently have {row['hold_count']} active holds and cannot place new holds until you are within the limit."
                    )

        return redirect(url_for('policy.policy'))

    cursor.execute("SELECT * FROM Policy WHERE policy_id=%s", (id,))
    policy = cursor.fetchone()

    return render_template("edit-policy.html", policy=policy)

@policy_bp.route('/policy/add', methods=['GET', 'POST'])
def add_policy():
    if session.get('user_type') != 'Librarian':
        return "Unauthorized", 403

    if request.method == 'POST':
        name = request.form['name']

        cursor = get_cursor()
        cursor.execute("SELECT * FROM Policy WHERE name = %s", [name])
        existing = cursor.fetchone()

        if existing:
            flash("Policy name already exists!", "error")
            return redirect(url_for('policy.add_policy'))
        
        period = request.form['loan_period_days']
        renewals = request.form['renewals_allowed']
        fine = request.form['fine_per_day']
        max_loans = request.form['max_concurrent_loans']
        holds = request.form['holds_limit_reservation']

        cursor.execute("""
            INSERT INTO Policy (name, loan_period_days, renewals_allowed,
                                fine_per_day, max_concurrent_loans,
                                holds_limit_reservation)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, period, renewals, fine, max_loans, holds))

        mysql.connection.commit()
        policy_id = cursor.lastrowid
        system_log("Policy", "INFO", "PolicyService", f"Policy created (policy_id={policy_id}).")

        flash("Policy added successfully!", "success")
        return redirect(url_for('policy.policy'))

    return render_template('add-policy.html')

@policy_bp.route('/policy/delete/<int:id>', methods=['POST'])
def delete_policy(id):
    if session.get('user_type') != 'Librarian':
        return "Unauthorized", 403

    cursor = get_cursor()
    cursor.execute("SELECT name FROM Policy WHERE policy_id = %s", (id,))
    policy = cursor.fetchone()
    if policy and policy.get("name") == "Standard Policy":
        flash("Default policy cannot be deleted.", "danger")
        return redirect(url_for('policy.policy'))

    try:
        cursor.execute("DELETE FROM Policy WHERE policy_id = %s", (id,))
        mysql.connection.commit()
        system_log("Policy", "INFO", "PolicyService", f"Policy deleted (policy_id={id}).")
        flash("Policy deleted successfully.", "success")
    except MySQLdb.IntegrityError:
        mysql.connection.rollback()
        flash("Policy cannot be deleted because it is in use.", "danger")
    except Exception as exc:
        mysql.connection.rollback()
        system_log("Policy", "ERROR", "PolicyService", f"Policy delete failed (policy_id={id}): {exc}")
        flash("Policy could not be deleted.", "danger")

    return redirect(url_for('policy.policy'))



