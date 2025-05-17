import db_connection


connection = db_connection.get_connection()
cursor = connection.cursor()

query = '''
create table year (
id int auto_increment primary key,
name varchar(255) not null
);
'''
cursor.execute(query)
connection.commit()
connection.close()
