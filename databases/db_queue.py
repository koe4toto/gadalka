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
            database=constants.QUEUE_DATABASE_NAME,
            user=constants.DATABASE_USER,
            password=constants.DATABASE_PASSWORD,
            host=constants.DATABASE_HOST,
            port=constants.DATABASE_PORT
        )


# Подключение
conn = DBConnect.inst().conn

# Курсор
cursor = conn.cursor()

# Создание очереди
def create_queue(self):
    # Создание таблицы
    cursor.execute(
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

    conn.commit()

# Создание задачи
def create_task(self, data_area_id, data, type, user_id, log_id):
    status = 1
    cursor.execute(
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
    conn.commit()
    task_id = cursor.fetchall()
    return task_id

# Список задач
def tasks(self):
    cursor.execute(
        '''
        SELECT * FROM data_queue;
        ''')
    result = cursor.fetchall()
    return result