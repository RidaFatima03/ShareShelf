from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import MySQLdb.cursors
from extensions import mysql

profile_bp = Blueprint('profile', __name__)

def get_cursor():
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)

@profile_bp.context_processor
def inject_notification_count_profile():
    from flask import session  
    if 'loggedin' in session:
        user_id = session['userid']
        cursor = get_cursor()
        cursor.execute("SELECT COUNT(*) as count FROM Notification WHERE user_id = %s AND is_read = FALSE", (user_id,))
        result = cursor.fetchone()
        count = result['count'] if result else 0
        return dict(unread_notifications_count=count)
    return dict(unread_notifications_count=0)

@profile_bp.route('/profile', methods=['GET'])
def userprofile():
    if 'userid' not in session:
        return redirect(url_for('auth.login'))
    
    userid = session['userid']
    cursor = get_cursor()
    
    cursor.execute('SELECT * FROM User WHERE user_id = %s', (userid,))
    myaccount = cursor.fetchone()

    if not myaccount:
        return redirect(url_for('auth.login'))

    if myaccount['user_middle_name'] and myaccount['user_middle_name'].strip():
        session['username'] = f"{myaccount['user_first_name']} {myaccount['user_middle_name']} {myaccount['user_last_name']}"
    else:
        session['username'] = f"{myaccount['user_first_name']} {myaccount['user_last_name']}"
    
    session['user_type'] = myaccount['user_type']

    cursor.execute('''
        SELECT SUM(f.amount) as amount
        FROM Fine f
        JOIN Checkout c ON f.checkout_id = c.checkout_id
        WHERE c.reader_id = %s AND f.status = 'Unpaid'
    ''', (userid, ))

    fine = cursor.fetchone()
    
    if not fine or fine['amount'] is None:
        fine = {'amount': 0.00}

    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM Request 
        WHERE status = 'Completed' 
          AND (reader_id = %s OR 
               book_id IN (SELECT book_id FROM Copy WHERE owner_id = %s))
    """, (userid, userid))
    exchange_data = cursor.fetchone()
    exchange_count = exchange_data['count'] if exchange_data else 0

    cursor.close()

    return render_template('personal-information.html', username=session.get('username'), myaccount=myaccount, fine=fine, exchange_count=exchange_count)
@profile_bp.route('/profile/update', methods=['GET', 'POST'], endpoint='updateprofile')
def updateprofile():
    if 'userid' not in session: return redirect(url_for('auth.login'))
    userid = session['userid']
    cursor = get_cursor()

    if request.method == 'GET':
        cursor.execute("SELECT * FROM User WHERE user_id = %s", (userid,))
        user = cursor.fetchone()
        return render_template('updateprofile.html', user=user)

    new_first_name = request.form.get('firstname', '').strip()
    new_middle_name = request.form.get('middlename', '').strip()
    new_last_name = request.form.get('lastname', '').strip()
    new_email = request.form.get('email', '').strip()
    new_phone = request.form.get('phone', '').strip()
    
    current_password = request.form.get('currentpassword', '').strip()
    new_password = request.form.get('newpassword', '').strip()
    confirm_password = request.form.get('confirmpassword', '').strip()

    updates = []
    values = []

    if new_first_name: 
        updates.append("user_first_name = %s")
        values.append(new_first_name)
    if new_middle_name:
        updates.append("user_middle_name = %s")
        values.append(new_middle_name)
    if new_last_name:
        updates.append("user_last_name = %s")
        values.append(new_last_name)
    if new_email:
        updates.append("user_email = %s")
        values.append(new_email)
    if new_phone:
        updates.append("user_phone_number = %s")
        values.append(new_phone)

    if new_password:
        if not current_password:
            flash("You must enter your current password to set a new one.", "danger")
            return redirect(url_for('profile.updateprofile'))
        
        cursor.execute("SELECT user_id FROM User WHERE user_id = %s AND user_password = SHA2(%s, 256)", (userid, current_password))
        if not cursor.fetchone():
            flash("Incorrect current password!", "danger")
            return redirect(url_for('profile.updateprofile'))

        if new_password != confirm_password:
            flash("New password does not match confirmation!", "danger")
            return redirect(url_for('profile.updateprofile'))
            
        updates.append("user_password = SHA2(%s, 256)")
        values.append(new_password)

    if not updates:
        flash("No changes made.", "info")
        return redirect(url_for('profile.updateprofile'))

    sql = "UPDATE User SET " + ", ".join(updates) + " WHERE user_id = %s"
    values.append(userid)

    cursor.execute(sql, tuple(values))
    mysql.connection.commit()
    cursor.close()

    flash("Profile updated successfully!", "success")
    return redirect(url_for('profile.userprofile'))