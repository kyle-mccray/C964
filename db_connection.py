import psycopg2
from psycopg2.extras import DictCursor
import os


class Connection:
    def __init__(self):
        try:
            print("Trying Connection to DB")
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require', cursor_factory=DictCursor)
            # conn = psycopg2.connect(
            #     host="localhost",
            #     database="flask",
            #     user="server",
            #     password="admin",
            #     cursor_factory=DictCursor)
            cur = conn.cursor()
            self.cur = cur
            print("Successfully Connected")

        except Exception as e:
            print("An error has occurred " + str(e))
