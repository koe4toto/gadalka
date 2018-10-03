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

    def __init__(self):

        # Статусы
        self.status = {
            1:'Нет данных',
            2:'Ожидает обработки',
            3:'Обработка данных',
            4:'Данных недостаточно для анализа',
            5:'Поиск связей',
            6:'Обработано'
        }

    # Создание таблицы
    def create_table(self):
        # Создание таблицы
        cursor.execute(
            '''
            CREATE SEQUENCE auto_id_data_area;
            CREATE SEQUENCE auto_id_ref_status;
            
            CREATE TABLE data_area (
                "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_data_area'), 
                "name" varchar(100), 
                "description" varchar(600), 
                "user_id" varchar(30), 
                "status" varchar,
                "database_table" varchar,
                "register_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE ref_status (
                "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_ref_status'), 
                "code" varchar(100), 
                "name" varchar(600)
            );
            '''
        )

        conn.commit()

    # Список предметных областей
    def select_da(self, user):
        cursor.execute(
            '''
            SELECT 
                data_area.id, 
                data_area.name, 
                data_area.register_date, 
                data_area.description, 
                data_area.status 
            FROM 
                data_area 
            WHERE data_area.user_id=%s
            ORDER BY data_area.register_date DESC;
            ''', user
        )
        result = cursor.fetchall()
        return result

    # Предметная область
    def data_area(self, id):
        cursor.execute(
            '''
            SELECT 
                *
            FROM 
                data_area 
            WHERE id=%s;
            ''', id
        )
        result = cursor.fetchall()
        return result

    # Создание предметной области
    def create_data_area(self, name, username, email, status):

        cursor.execute(
            '''
            INSERT INTO data_area (
                name, 
                description, 
                user_id, 
                status
            ) VALUES (%s, %s, %s, %s);
            ''',
            (
                name,
                username,
                email,
                status
            ))
        conn.commit()

# Параметры
class measures:

    def __init__(self):

        # Типы параметров
        self.types = {
            1: 'Количественные',
            2: 'Качественные',
            3: 'По справочнику',
            4: 'Времмя',
            5: 'Дата',
            6: 'Время и дата'
        }

        # Статусы параметров
        self.status = {
            1: 'Нет данных',
            2: 'Обработано'
        }

    # Создание таблицы
    def create_table(self):
        # Создание таблицы
        cursor.execute(
            '''
            CREATE SEQUENCE auto_id_measures;
            CREATE SEQUENCE auto_id_ref_measures_type;
            CREATE SEQUENCE auto_id_ref_measures_status;

            CREATE TABLE measures (
                "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_measures'), 
                "column_name" varchar(300), 
                "description" varchar(300), 
                "data_area_id" varchar(300), 
                "type" int, 
                "status" int, 
                "ref_id" int
            );

            CREATE TABLE ref_measures_type (
                "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_ref_measures_type'), 
                "code" varchar(100), 
                "name" varchar(600)
            );
            
            CREATE TABLE ref_measures_status (
                "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_ref_measures_status'), 
                "code" varchar(100), 
                "name" varchar(600)
            );
            '''
        )

        conn.commit()

    # Список измерений
    def select_measures(self, user):
        cursor.execute(
            '''
            SELECT 
                measures.id, 
                measures.description, 
                measures.type, 
                measures.status
            FROM 
                measures 
            LEFT JOIN data_area ON measures.data_area_id = data_area.id
            WHERE data_area_id.user_id=%s
            ORDER BY data_area.register_date DESC;
            ''', user
        )
        data = cursor.fetchall()
        return data


# Пользователи
class users:

    # Создание таблицы
    def create_table(self):

        # Создание таблицы
        cursor.execute(
            '''
            CREATE SEQUENCE auto_id_users;
            
            CREATE TABLE users (
                "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_users'), 
                "name" varchar(100), 
                "email" varchar(100), 
                "username" varchar(30), 
                "password" varchar, 
                "register_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            '''
        )
        conn.commit()

    # Создание пользователя
    def create(self, name, username, email, password):

        cursor.execute(
            '''
            INSERT INTO users (
                name, 
                username, 
                email, 
                password
            ) VALUES (%s, %s, %s, %s);
            ''',
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
            '''
            SELECT * FROM users WHERE username = %s
            ''', username
            )
        result = cursor.fetchall()
        return result


# Заполнение справочника
def update_ref(ref):
    for i in ref:
        cursor.execute(
            '''
            INSERT 
            INTO ref_status (
                code, 
                name
                ) 
            VALUES (%s, %s);''', (
                str(i),
                ref[i]
            )
        )
    conn.commit()

# Удаление табицы
def delate_table(name):
    cursor.execute(
        '''
        DROP TABLE %s;
        DROP SEQUENCE auto_id_%s;
        ''', (name, name)
    )
    conn.commit()

# Удаление данных из таблицы
def delate_data(name):
    cursor.execute(
        '''
        DELETE FROM %s;
        ''', name
    )
    conn.commit()

"""
# Справочники
cursor.execute('''CREATE SEQUENCE auto_id_refs;''')
cursor.execute('''CREATE TABLE refs ("id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_refs'), "name" varchar(100), "description" varchar(600), "user_id" varchar(30), "data" varchar, "register_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')

# Описание содержание предметной области
cursor.execute('''CREATE SEQUENCE auto_id_area_description;''')
cursor.execute('''CREATE TABLE area_description ("id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_area_description'), 
"column_name" varchar(300), 
"description" varchar(300), 
"data_area_id" varchar(30), 
"type" int, 
"status" int, 
"ref_id" int);''')

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
#cursor.execute('DROP SEQUENCE auto_id_data_area')
#cursor.execute('select * from test_data')
#pik = cursor.fetchall()
#print(pik)

#conn.commit()
#cursor.close()
#conn.close()








