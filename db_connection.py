import psycopg2


class Con:
    def __init__(self):
        try:
            print("Connecting to DB")
            conn = psycopg2.connect(
                host="localhost",
                database="flask",
                user="server",
                password="password")
            cur = conn.cursor()
            self.cur = cur
        except Exception as e:
            print("An error has occurred " + str(e))
