from flask import Blueprint, render_template, request, redirect, url_for, session
import MySQLdb.cursors
from extensions import mysql

policy_bp = Blueprint('policy', __name__)

def get_cursor():
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)

@policy_bp.route('/policy', methods=['GET'])
def policy():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = get_cursor()
    cursor.execute("SELECT * FROM Policy")
    policies = cursor.fetchall()
    role = session.get('role')

    return render_template("policy.html", data=policies, role=role)

@policy_bp.route('/policy/edit/<int:id>', methods=['GET', 'POST'])
def edit_policy(id):
    if session.get('role') != 'Librarian':
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

        return redirect(url_for('policy.policy'))

    cursor.execute("SELECT * FROM Policy WHERE policy_id=%s", (id,))
    policy = cursor.fetchone()

    return render_template("edit_policy.html", policy=policy)

@policy_bp.route('/policy/add', methods=['GET', 'POST'])
def add_policy():
    if session.get('role') not in ['Librarian', 'Admin']:
        return "Unauthorized", 403

    if request.method == 'POST':
        name = request.form['name']
        period = request.form['loan_period_days']
        renewals = request.form['renewals_allowed']
        fine = request.form['fine_per_day']
        max_loans = request.form['max_concurrent_loans']
        holds = request.form['holds_limit_reservation']
        applies = request.form['applies_to_role']

        cursor = get_cursor()
        cursor.execute("""
            INSERT INTO Policy (name, loan_period_days, renewals_allowed,
                                fine_per_day, max_concurrent_loans,
                                holds_limit_reservation, applies_to_role)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, period, renewals, fine, max_loans, holds, applies))

        mysql.connection.commit()

        return redirect(url_for('policy.policy'))

    return render_template("add-policy.html")

@policy_bp.route('/policy/delete/<int:id>', methods=['POST'])
def delete_policy(id):
    if session.get('role') not in ['Librarian', 'Admin']:
        return "Unauthorized", 403

    cursor = get_cursor()
    cursor.execute("DELETE FROM Policy WHERE policy_id = %s", (id,))
    mysql.connection.commit()

    return redirect(url_for('policy.policy'))



