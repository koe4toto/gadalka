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
            database=constants.USERS_DATABASE_NAME,
            user=constants.DATABASE_USER,
            password=constants.DATABASE_PASSWORD,
            host=constants.DATABASE_HOST,
            port=constants.DATABASE_PORT
        )

# Подключение
conn = DBConnect.inst().conn

# Курсор
cursor = conn.cursor()

# Создание хранилища данных предметной области
def create_olap(olap_name):
    cursor.execute(
        '''
        CREATE SEQUENCE auto_id_{0};
    
        CREATE TABLE {0} (
            "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_{0}')
        );
        '''.format(olap_name))
    conn.commit()

# Удаление таблицы с данными
def delete_olap(olap_name):
    cursor.execute(
        '''
            DROP TABLE {0}; 
            DROP SEQUENCE auto_id_{0};
        '''.format(olap_name)
    )
    conn.commit()

# Содержание справочника
def ref_data(ref_name):
    cursor.execute(
        '''SELECT * FROM {0} ;
        '''.format(ref_name)
    )
    result = cursor.fetchall()
    return result

# Создание таблицы для хранения данных
def create_ref_table(table_name):
    cursor.execute(
        '''
        CREATE TABLE {0} ("code" varchar primary key, "value" varchar, "parent_value" varchar);
        '''.format(table_name)
    )
    conn.commit()

# Добавление данных в справочник
def insert_data_in_ref(table_name, row1, row2, row3):
    cursor.execute(
        '''
        INSERT INTO {0} (code, value, parent_value) VALUES ('{1}', '{2}', '{3}');
        '''.format(table_name, row1, row2, row3)
    )
    conn.commit()

# Удаление таблицы хранения данных
def delete_table(table_name):
    cursor.execute('''DROP TABLE {0}'''.format(table_name))
    conn.commit()

# Удаление таблицы хранения данных
def delete_from_table(table_name):
    cursor.execute(
        '''
        DELETE FROM '{0}';
        '''.format(table_name))
    conn.commit()

# Данные для графика распределения
def distribution(column_name, olap_nmae, ui_limit):
    cursor.execute(
        '''
        SELECT {0}
            FROM (
                SELECT 
                    row_number() over (order by {0}) as num,
                    count(*) over () as count,
                    {0}  
                FROM {1}
                WHERE {0} IS NOT NULL
                ) selected
        WHERE (case when count > {2} then num %(count/{2}) = 0 else 1 = 1 end);
        '''.format(column_name, olap_nmae, ui_limit))
    result = cursor.fetchall()
    return result

# Данные для графика распределения
def time_distribution(data_column, olap_name, ui_limit):
    cursor.execute(
        '''
        SELECT result
            FROM (
                SELECT 
                    row_number() over (order by {0}) as num,
                    count(*) over () as count,
                    {0} as result  
                FROM {1}
                WHERE {0} IS NOT NULL
                ) selected
        WHERE (case when count > {2} then num %(count/{2}) = 0 else 1 = 1 end);
        '''.format(data_column, olap_name, ui_limit)
    )
    result = cursor.fetchall()
    return result

# Сооздание колонки по справочнику
def add_ref_column(olap_name, column_name, type_of_measure, ref_name):
    cursor.execute(
        '''
        ALTER TABLE 
        {0} 
        ADD COLUMN 
        {1} {2} {3}(code);
        '''.format(
            olap_name,
            column_name,
            type_of_measure,
            ref_name
        )
    )
    conn.commit()

# Сооздание колонки
def add_column(olap_name, column_name, type_of_measure):
    cursor.execute(
        '''
        ALTER TABLE 
        {0} 
        ADD COLUMN 
        {1} {2};
        '''.format(
            olap_name,
            column_name,
            type_of_measure
        )
    )
    conn.commit()

# Сооздание колонки
def update_column(olap_name, old_column_name, new_column_name):
    cursor.execute(
        '''
        ALTER TABLE {0} RENAME COLUMN {1} TO {2};
        '''.format(
            olap_name,
            old_column_name,
            new_column_name
        )
    )
    conn.commit()

# Удаление колонки
def delete_column(olap_name, column_name):
    cursor.execute(
        '''
        ALTER TABLE {0} DROP COLUMN {1};
        '''.format(
            olap_name,
            column_name
        )
    )
    conn.commit()

# Запись данных в куб
def insret_data_to_olap(table_name, names_to_record, data_to_record):
    cursor.execute(
        '''
        INSERT INTO {0} (
            {1}
        ) VALUES ({2});
        '''.format(table_name, names_to_record, data_to_record)
    )
    conn.commit()

# Удаление данных из таблицы
def delete_data_from_olap(table_name):
    cursor.execute(
            '''
            DELETE FROM {0};
            '''.format(table_name)
        )
    conn.commit()