import pymysql.cursors

# Connect to the database
def get_connection():
    connection = pymysql.connect(host='localhost',
                                user='root',
                                password='redbuds23',
                                database='timetable_db',
                                cursorclass=pymysql.cursors.DictCursor)
    return connection

