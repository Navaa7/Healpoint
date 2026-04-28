import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="switchback.proxy.rlwy.net",   # from MYSQL_PUBLIC_URL
        user="root",                        # from MYSQLUSER
        password="ziYosEUbDsXUnJxViEMKoZZFkfOIkDJX",           # from MYSQL_ROOT_PASSWORD
        database="railway",                 # from MYSQLDATABASE
        port=31890                          # from MYSQLPORT
    )