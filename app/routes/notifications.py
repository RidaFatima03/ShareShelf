import MySQLdb.cursors

class NotificationService:
    def __init__(self, db):
        self.db = db

    def add_notification(self, user_id, subject, details):
        cursor = self.db.cursor()
        cursor.execute(
            """
            INSERT INTO Notification (user_id, subject, details)
            VALUES (%s, %s, %s)
            """,
            (user_id, subject, details)
        )
        self.db.commit()

    def get_unread_notifications(self, user_id):
        cursor = self.db.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            """
            SELECT notification_id, subject, details, notification_date
            FROM Notification
            WHERE user_id = %s AND is_read = FALSE
            ORDER BY notification_date DESC
            """,
            (user_id,)
        )
        return cursor.fetchall()

    def get_read_notifications(self, user_id):
        cursor = self.db.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            """
            SELECT notification_id, subject, details, notification_date
            FROM Notification
            WHERE user_id = %s AND is_read = TRUE
            ORDER BY notification_date DESC
            """,
            (user_id,)
        )
        return cursor.fetchall()

    def mark_as_read(self, notification_id, user_id):
        cursor = self.db.cursor()
        cursor.execute(
            """
            UPDATE Notification
            SET is_read = TRUE
            WHERE notification_id = %s AND user_id = %s
            """,
            (notification_id, user_id)
        )
        self.db.commit()
