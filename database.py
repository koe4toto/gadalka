import psycopg2
import constants

# Подключение к базам данных
class DBConnect(object):
    __instance = None

    @staticmethod
    def inst():
        if DBConnect.__instance == None:
            DBConnect.__instance = DBConnect()
        return DBConnect.__instance

    def __init__(self):
        self.conn = psycopg2.connect(
            database=constants.DATABASE_NAME,
            user=constants.DATABASE_USER,
            password=constants.DATABASE_PASSWORD,
            host=constants.DATABASE_HOST,
            port=constants.DATABASE_PORT
        )
        self.data_conn = psycopg2.connect(
            database=constants.USERS_DATABASE_NAME,
            user=constants.DATABASE_USER,
            password=constants.DATABASE_PASSWORD,
            host=constants.DATABASE_HOST,
            port=constants.DATABASE_PORT
        )
        self.queue_conn = psycopg2.connect(
            database=constants.QUEUE_DATABASE_NAME,
            user=constants.DATABASE_USER,
            password=constants.DATABASE_PASSWORD,
            host=constants.DATABASE_HOST,
            port=constants.DATABASE_PORT
        )

# Подключение к транзакционной базе
conn = DBConnect.inst().conn

# Курсор для транзакционной базы
cursor = conn.cursor()

# Подключение к хранилищу данных
data_conn = DBConnect.inst().data_conn

# Курсор для базы с данными
data_cursor = data_conn.cursor()

# Подключение к хранилищу очереди
queue_conn = DBConnect.inst().queue_conn

# Курсор для базы с данными очереди
queue_cursor = queue_conn.cursor()

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

    # Создание очереди
    def create_queue(self):
        # Создание таблицы
        queue_cursor.execute(
            '''
            CREATE SEQUENCE auto_id_data_queue;

            CREATE TABLE data_queue (
                "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_data_queue'), 
                "data_area_id" integer,
                "data_log_id" integer, 
                "data" varchar(600), 
                "type" varchar(30),
                "status" integer,
                "user_id" varchar(30),
                "register_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            '''
        )

        queue_conn.commit()

    # Создание задачи
    def create_task(self, data_area_id, data, type, user_id, log_id):
        status = 1
        queue_cursor.execute(
            '''
            INSERT INTO data_queue (
                data_area_id, 
                data_log_id,
                data, 
                type,
                status,
                user_id
            ) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}') RETURNING id;
            '''.format(
                data_area_id,
                log_id,
                data,
                type,
                status,
                user_id)
        )
        queue_conn.commit()
        task_id = cursor.fetchall()
        return task_id

    # Список задач
    def tasks(self):
        queue_cursor.execute(
            '''
            SELECT * FROM data_queue;
            ''')
        result = queue_cursor.fetchall()
        return result

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
            WHERE data_area.user_id='{0}'
            ORDER BY data_area.register_date DESC;
            '''.format(user)
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
            WHERE id={0};
            '''.format(id)
        )
        result = cursor.fetchall()
        return result

    # Создание предметной области
    def create_data_area(self, name, description, user_id, status):

        cursor.execute(
            '''
            INSERT INTO data_area (
                name, 
                description, 
                user_id, 
                status
            ) VALUES (%s, %s, %s, %s)
            RETURNING id;
            ''',
            (
                name,
                description,
                user_id,
                status
            ))
        conn.commit()
        data_base_id = cursor.fetchall()

        olap_name = 'olap_' + str(data_base_id[0][0]) + '_' +str(user_id)

        data_cursor.execute(
            '''
            CREATE SEQUENCE auto_id_{0};

            CREATE TABLE {0} (
                "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_{0}')
            );
            '''.format(olap_name))
        data_conn.commit()

        cursor.execute(
            '''
            UPDATE data_area SET
                database_table=%s
            WHERE id=%s;
            ''',
            (
                olap_name,
                data_base_id[0][0]
            ))
        conn.commit()

    # Редактирование предметной области
    def update_data_area(self, name, username, status, id):
        cursor.execute(
            '''
            UPDATE data_area SET
                name=%s, 
                description=%s, 
                status=%s
            WHERE id=%s;
            ''',
            (
                name,
                username,
                status,
                id
            ))
        conn.commit()

    # Удаление предметной области
    def delate_data_area(self, id):
        # Получение свдений о предметной области
        cursor.execute("SELECT database_table FROM data_area WHERE id = '{0}'".format(id))
        data_a = cursor.fetchall()

        # Удаление данных из таблиц
        cursor.execute(
            '''
            DELETE FROM measures WHERE data_area_id = '{0}';
            DELETE FROM data_area WHERE id = '{0}';
            DELETE FROM math_models WHERE data_area_id = '{0}';
            DELETE FROM data_log WHERE data_area_id = '{0}';
            '''.format(id)
        )
        conn.commit()

        # Удаление таблицы с данными
        data_cursor.execute(
            '''
                DROP TABLE {0}; 
                DROP SEQUENCE auto_id_{1};
            '''.format(data_a[0][0], data_a[0][0])
        )
        data_conn.commit()

# Параметры
class measures:

    def __init__(self):

        # Типы параметров
        self.types = {
            1: 'Количественные данные',
            2: 'Качественные данные',
            3: 'Данные по справочнику',
            4: 'Время',
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
                "data_area_id" int, 
                "type" int, 
                "status" int,
                "ref_id" int,  
                "len" varchar,
                "sum" varchar,
                "min" varchar,
                "max" varchar,
                "max_freq" varchar,
                "ptp" varchar,
                "mean" varchar,
                "median" varchar,
                "mode" varchar,
                "average" varchar,
                "std" varchar,
                "var" varchar,
                "sem" varchar,
                "iqr" varchar
                
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
            WHERE data_area_id.user_id='{0}'
            ORDER BY data_area.register_date DESC;
            '''.format(user)
        )
        result = cursor.fetchall()
        return result

    # Список измерений предметной области
    def select_measures_to_data_area(self, data_area_id):
        cursor.execute(
            '''
            SELECT 
                measures.id, 
                measures.column_name,
                measures.description, 
                ref_measures_type.name, 
                measures.status
            FROM 
                measures 
            LEFT JOIN ref_measures_type ON measures.type = ref_measures_type.id
            LEFT JOIN ref_measures_status ON measures.status = ref_measures_status.id
            WHERE measures.data_area_id='{0}'
            ORDER BY measures.type DESC;
            '''.format(data_area_id)
        )
        result = cursor.fetchall()
        return result

    def model(self, id):
        # Список пар
        cursor.execute(
            '''SELECT 
                    h.name, 
                    m1.r_value, 
                    a1.description, 
                    a2.description, 
                    m1.area_description_1, 
                    m1.area_description_2, 
                    m1.id 
                FROM 
                    math_models m1
                INNER JOIN 
                    hypotheses h on m1.hypothesis = h.id
                INNER JOIN 
                    measures a1 on m1.area_description_1 = a1.id
                INNER JOIN 
                    measures a2 on m1.area_description_2 = a2.id
                WHERE 
                    (m1.r_value IS NOT NULL) AND (m1.area_description_1 = '{0}' OR m1.area_description_2 = '{0}')
                ORDER BY m1.r_value DESC;'''.format(id))
        list = cursor.fetchall()
        return list

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
            SELECT * FROM users WHERE username = '{0}'
            '''.format(username)
            )
        result = cursor.fetchall()
        return result

# Заполнение справочника
def update_ref(ref, name):
    for i in ref:
        cursor.execute(
            '''
            INSERT 
            INTO '''+ name +''' (
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
        DELETE FROM {0};
        '''.format(name)
    )
    conn.commit()

"""
# Справочники
cursor.execute(
    '''
    CREATE SEQUENCE auto_id_refs;
    
    CREATE TABLE refs 
    (
        "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_refs'), 
        "name" varchar(100), 
        "description" varchar(600), 
        "user_id" varchar(30), 
        "data" varchar, 
        "register_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    '''
)

# Справочник гипотез моделей (заполняется разработчиком)
cursor.execute(
    '''
    CREATE TABLE hypotheses 
    (
        "id" integer PRIMARY KEY NOT NULL, 
        "name" varchar(300), 
        "description" varchar(300)
    );
    '''
)

# Модели
cursor.execute(
    '''
    CREATE SEQUENCE auto_id_math_models;
    
    CREATE TABLE math_models 
    (
        "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_math_models'), 
        "hypothesis" integer, 
        "slope" varchar(300), 
        "intercept" varchar(300), 
        "r_value" varchar(300), 
        "p_value" varchar(300), 
        "std_err" varchar(300),
        "xstat_div" varchar(300),
        "ystat_div" varchar(300),
        "data_area_id" integer,
        "area_description_1" integer, 
        "area_description_2" integer
    );
    '''
)
conn.commit()

# История загрузки данных
cursor.execute(
    '''
    CREATE SEQUENCE auto_id_data_log;
    
    CREATE TABLE data_log 
    (
        "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_data_log'), 
        "data_area_id" integer, 
        "errors" varchar(300), 
        "downloads" varchar(300), 
        "result" varchar(300), 
        "status" varchar(300),
        "register_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    '''
)
conn.commit()
"""








