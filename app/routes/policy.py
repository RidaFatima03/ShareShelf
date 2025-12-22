from flask import Blueprint, render_template, request, redirect, url_for, session,flash
import MySQLdb.cursors
from extensions import mysql
from utils.system_log import system_log

policy_bp = Blueprint('policy', __name__)

def get_cursor():
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)

@policy_bp.route('/policy', methods=['GET'])
def policy():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = get_cursor()
    if session.get("user_type") == "Reader":
        cursor.execute("SELECT * FROM Policy WHERE applies_to_role = 'Reader'")
    elif session.get("user_type") == "Admin":
        cursor.execute("SELECT * FROM Policy WHERE applies_to_role = 'Admin'")
    else:
        cursor.execute("SELECT * FROM Policy")
    policies = cursor.fetchall()
    role = session.get('user_type')

    return render_template("policy.html", data=policies, role=role)

@policy_bp.route('/policy/edit/<int:id>', methods=['GET', 'POST'])
def edit_policy(id):
    if session.get('user_type') != 'Librarian':
        return "Unauthorized", 403

    cursor = get_cursor()

    if request.method == 'POST':
        name = request.form['name']
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
        applies = request.form['applies_to_role']

        cursor.execute("""
            INSERT INTO Policy (name, loan_period_days, renewals_allowed,
                                fine_per_day, max_concurrent_loans,
                                holds_limit_reservation, applies_to_role)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, period, renewals, fine, max_loans, holds, applies))

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
    cursor.execute("DELETE FROM Policy WHERE policy_id = %s", (id,))
    mysql.connection.commit()
    system_log("Policy", "INFO", "PolicyService", f"Policy deleted (policy_id={id}).")

    return redirect(url_for('policy.policy'))



