from extensions import mysql
import MySQLdb.cursors


def system_log(source, level, node, message):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        """
        INSERT INTO Log (log_date, source, log_level, log_node, log_message)
        VALUES (NOW(), %s, %s, %s, %s)
        """,
        (source, level, node, message)
    )
    mysql.connection.commit()
