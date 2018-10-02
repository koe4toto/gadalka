import psycopg2
import constants

# Подключение
conn = psycopg2.connect(
    database=constants.DATABASE_NAME,
    user=constants.DATABASE_USER,
    password=constants.DATABASE_PASSWORD,
    host=constants.DATABASE_HOST,
    port=constants.DATABASE_PORT
)

# Курсор
cursor = conn.cursor()

# Предметные оболасти
class data_area:

    # Создание таблицы
    def create_table(self):
        # Генератор идентификаторов
        cursor.execute('''CREATE SEQUENCE auto_id_data_area;''')

        # Создание таблицы
        cursor.execute(
            '''CREATE TABLE data_area (
            "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_data_area'), 
            "name" varchar(100), 
            "description" varchar(600), 
            "user_id" varchar(30), 
            "status" varchar,
            "database_table" varchar,
            "register_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );''')
        conn.commit()

    # Удаление табицы
    def delate_table(self):
        cursor.execute('''DROP SEQUENCE auto_id_data_area;''')
        cursor.execute('''DROP TABLE data_area''')
        conn.commit()

    # Удаление данных из таблицы
    def delate_data(self):
        cursor.execute('DELETE FROM data_area')
        conn.commit()

    # Тестовая функция
    def test_select(self):
        cursor.execute('SELECT * FROM data_area')
        data = cursor.fetchall()
        return data


# Пользователи
class users:

    # Создание таблицы
    def create_table(self):
        # Генератор идентификаторов
        cursor.execute('''CREATE SEQUENCE auto_id_users;''')

        # Создание таблицы
        cursor.execute(
            '''CREATE TABLE users (
            "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_users'), 
            "name" varchar(100), 
            "email" varchar(100), 
            "username" varchar(30), 
            "password" varchar, 
            "register_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );''')
        conn.commit()

    # Удаление табицы
    def delate_table(self):
        cursor.execute('DROP TABLE users')

    # Удаление данных из таблицы
    def delate_data(self):
        cursor.execute('DELETE FROM users')

    # Создание пользователя
    def create(self, name, username, email, password):

        cursor.execute(
            '''INSERT INTO users (
            name, 
            username, 
            email, 
            password
            ) VALUES (%s, %s, %s, %s);''',
            (
                name,
                username,
                email,
                password
            ))
        conn.commit()

    # Поиск пользователя в базе по значению username
    def search(self, username):
        cursor.execute(
            '''SELECT * FROM users WHERE username = %s''',
            [username]
            )
        result = cursor.fetchall()
        return result

"""
# Пользователи
cursor.execute('''CREATE SEQUENCE auto_id_users; ''')
cursor.execute('''CREATE TABLE users ("id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_users'), "name" varchar(100), "email" varchar(100), "username" varchar(30), "password" varchar, "register_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')

# Предметные области
cursor.execute('''CREATE SEQUENCE auto_id_data_area;''')
cursor.execute('''CREATE TABLE data_area ("id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_data_area'), "name" varchar(100), "description" varchar(600), "user_id" varchar(30), "database" varchar, "database_user" varchar, "database_password" varchar, "database_host" varchar, "database_port" varchar, "database_table" varchar, "register_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')

# Справочники
cursor.execute('''CREATE SEQUENCE auto_id_refs;''')
cursor.execute('''CREATE TABLE refs ("id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_refs'), "name" varchar(100), "description" varchar(600), "user_id" varchar(30), "data" varchar, "register_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')

# Описание содержание предметной области
cursor.execute('''CREATE SEQUENCE auto_id_area_description;''')
cursor.execute('''CREATE TABLE area_description ("id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_area_description'), "column_name" varchar(300), "description" varchar(300), "user_id" varchar(30), "data_area_id" varchar(30), "type" int, "kind_of_metering" int, "ref_id" int);''')

# Справочник гипотез моделей (заполняется разработчиком)
cursor.execute('''CREATE TABLE hypotheses ("id" integer PRIMARY KEY NOT NULL, "name" varchar(300), "description" varchar(300));''')

# Модели
cursor.execute('''CREATE SEQUENCE auto_id_math_models;''')
cursor.execute('''
CREATE TABLE math_models 
("id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_refs'), 
"hypothesis" integer, 
"slope" varchar(300), 
"intercept" varchar(300), 
"r_value" varchar(300), 
"p_value" varchar(300), 
"std_err" varchar(300),
"area_description_1" integer, 
"area_description_2" integer);
''')
"""


# Удаление табицы, если требуется
#cursor.execute('DROP TABLE data_area')

#cursor.execute('''CREATE TABLE test_data ("x" real, "line_1" real, "line_2" real);''')

#cursor.execute('select * from test_data')
#pik = cursor.fetchall()
#print(pik)

#conn.commit()
#cursor.close()
#conn.close()








