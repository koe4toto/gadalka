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

# Подключение
conn = DBConnect.inst().conn

# Курсор
cursor = conn.cursor()


# Предметные оболасти
class data_area:

    def __init__(self):
        # Статусы
        self.status = {
            1: 'Нет данных',
            2: 'Ожидает обработки',
            3: 'Обработка данных',
            4: 'Данных недостаточно для анализа',
            5: 'Поиск связей',
            6: 'Обработано'
        }

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

        olap_name = 'olap_' + str(data_base_id[0][0]) + '_' + str(user_id)

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
                measures.status,
                measures.type
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

    def model(self, id1, id2):
        # Список пар
        try:
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
                        (m1.r_value IS NOT NULL) 
                        AND (m1.area_description_1 = '{0}' or m1.area_description_2 = '{0}') 
                        AND (m1.area_description_1 = '{1}' or m1.area_description_2 = '{1}')
                        AND (m1.r_value != 'None')
                    ORDER BY abs(m1.r_value::real) DESC;'''.format(id1, id2))
            list = cursor.fetchall()
        except:
            list = []
        return list


# Пользователи
class users:

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


def get_models(limit):
    cursor.execute(
        '''SELECT *
            FROM (
                SELECT
                    h.name, 
                    ml.r_value,
                    a1.description,
                    a2.description,
                    ml.area_description_1, 
                    ml.area_description_2,
                    ml.id, 
                    ml.hypothesis,
                    row_number() OVER (
                        PARTITION BY area_description_1::text || area_description_2::text 
                        ORDER BY abs(to_number(r_value, '9.999999999999')) DESC)  AS rating_in_section,
                    a1.column_name,
                    a2.column_name,
                    a1.data_area_id,
                    a2.data_area_id
                FROM 
                    math_models ml
                INNER JOIN 
                    measures a1 on ml.area_description_1 = a1.id
                INNER JOIN 
                    measures a2 on ml.area_description_2 = a2.id
                INNER JOIN 
                    hypotheses h on ml.hypothesis = h.id
                WHERE 
                    r_value != 'None'
                ORDER BY 
                    rating_in_section
            ) counted_news
            WHERE rating_in_section <= 1 AND abs(to_number(r_value, '9.999999999999')) >= '{0}'
            ORDER BY abs(to_number(r_value, '9.999999999999')) DESC;
            '''.format(limit))
    list = cursor.fetchall()
    return list











