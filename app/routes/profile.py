from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import MySQLdb.cursors
from extensions import mysql

profile_bp = Blueprint('profile', __name__)

def get_cursor():
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)

@profile_bp.route('/profile', methods=['GET'])
def userprofile():
    if 'userid' not in session:
        return redirect('/login')
    
    userid = session['userid']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        '''
        SELECT *
        FROM User
        WHERE user_id = %s
    ''', (userid,))

    myaccount = cursor.fetchone()

    if myaccount['user_middle_name'].strip() == '':
                session['username'] = myaccount['user_first_name'] + ' ' + myaccount['user_last_name']
    else:
        session['username'] = myaccount['user_first_name'] + ' ' + myaccount['user_middle_name'] + ' ' + myaccount['user_last_name']
    session['user_type'] = myaccount['user_type']   # 'Reader', 'Librarian', or 'Admin'

    cursor.execute(
        '''
        SELECT F.amount
        FROM Fine F, User U
        JOIN Checkout C on F.checkout_id = C.checkout_id
        JOIN Reader R on C.reader_id = R.reader_id
        JOIN User U on R.reader_id = U.user_id
        WHERE U.user_id = %s
    ''', (userid, ))

    fine = cursor.fetchone()

    cursor.close()

    return render_template('profile.html', username=session.get('username'), myaccount=myaccount, fine=fine)

@profile_bp.route('/profile/update', methods=['GET', 'POST'])
def updateprofile():
    if 'userid' not in session:
        return redirect('/login')

    userid = session['userid']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

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

    cursor.execute(
        '''
        SELECT * 
        FROM User 
        WHERE user_id = %s 
    ''', (userid,))
    
    user = cursor.fetchone()

    if current_password:
        if user['user_password'] != current_password:
            flash("Current password is incorrect!")
            return redirect('/updateprofile')

        if new_password != confirm_password:
            flash("New password does not match confirmation!")
            return redirect('/updateprofile')
    
    if new_email:
        if '@' not in new_email or not new_email.endswith('.com'):
            flash("Email not valid!")
            return redirect('/updateprofile')

        updates.append("user_email = %s")
        values.append(new_email)

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
        updates.append("user_password = %s")
        values.append(new_password)

    if not updates:
        flash("No changes made.")
        return redirect('/updateprofile')

    sql = "UPDATE User SET " + ", ".join(updates) + " WHERE user_id = %s"
    values.append(userid)

    cursor.execute(sql, tuple(values))
    mysql.connection.commit()
    cursor.close()

    flash("Profile updated successfully!")
    return redirect('/userprofile')
