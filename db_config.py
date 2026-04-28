import os
import mysql.connector
from urllib.parse import urlparse

def get_connection():
    db_url = os.getenv("MYSQL_PUBLIC_URL")

    if not db_url:
        raise Exception("Database URL not found")

    url = urlparse(db_url)

    return mysql.connector.connect(
        host=url.hostname,
        user=url.username,
        password=url.password,
        database=url.path[1:],  # remove '/'
        port=url.port
    )