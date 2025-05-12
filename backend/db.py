# db.py (example structure)
import mysql.connector

def get_connection():
    conn = mysql.connector.connect(
        host="localhost",       # e.g., 'localhost'
        user="root",
        password="",
        database="glean_netsuite_sync"  # <--- CORRECT THIS LINE
    )
    return conn