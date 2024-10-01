import mysql.connector

class DatabaseConnection:
    def __init__(self):
        self.connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="tr-sale-system"
        )

    def connect(self):
        self.connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="tr-sale-system"
        )

    def execute_query(self, query, fetch=True, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        if fetch:
            return cursor.fetchall()
        else:
            self.connection.commit()
            return cursor

    def close(self):
        self.connection.close()