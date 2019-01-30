import psycopg2
import constants
import databases.db_data as dbdata

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


status = {
    1: 'Нет данных',
    2: 'Ожидает обработки',
    3: 'Обработка данных',
    4: 'Данных недостаточно для анализа',
    5: 'Поиск связей',
    6: 'Обработано'
}

# Список предметных областей
def select_da(user):
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
def data_area(id):
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
def create_data_area(name, description, user_id, status):
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

    # Удаление таблицы с данными
    dbdata.create_olap(olap_name)

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
def update_data_area(name, username, status, id):
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
def delete_data_area(id):
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
    dbdata.delete_olap(data_a[0][0])


# Типы параметров
types = {
    1: 'Количественные данные',
    2: 'Качественные данные',
    3: 'Данные по справочнику',
    4: 'Время',
    5: 'Дата',
    6: 'Время и дата'
}

# Статусы параметров
status = {
    1: 'Нет данных',
    2: 'Обработано'
}

# Список измерений
def select_measures(user):
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
def select_measures_to_data_area(data_area_id):
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


# Список моделей пары
def select_pair_models(id1, id2):
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


# Параметры пары
def select_pairs_measures(id1, id2):
    cursor.execute(
        '''
        SELECT * FROM measures WHERE id='{0}' OR id='{1}';
        '''.format(id1, id2))
    maesures = cursor.fetchall()
    return maesures

# Создание пользователя
def create_user(name, username, email, password):
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
def user_search(username):
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

# Список правлчников
def ref_list():
    cursor.execute(
        '''
        SELECT * FROM refs ORDER BY register_date DESC;
        '''
    )
    result = cursor.fetchall()
    return result


# Справочник
def ref_data(id):
    cursor.execute(
        '''
        SELECT * FROM refs WHERE id = '{0}';
        '''.format(id)
    )
    result = cursor.fetchall()
    return result

# Запись о справочнике
def insert_ref(name, description, user, table_name):
    cursor.execute(
        '''
        INSERT INTO refs (name, description, user_id, data) VALUES ('{0}', '{1}', '{2}', '{3}');
        '''.format(name, description, user, table_name)
    )
    conn.commit()



# Удаление справочника
def delete_ref(id):
    cursor.execute('''SELECT * FROM refs WHERE id = '{0}';'''.format(id))
    the_ref = cursor.fetchall()

    # Имя справочника
    ref_name = the_ref[0][4]

    # Удаление записи о справочнике
    cursor.execute('''DELETE FROM refs WHERE id = '{0}';'''.format(id))
    conn.commit()

    # Удаление таблицы с данными
    dbdata.delete_table(ref_name)

    return ref_name

# Обновление описания справочника
def update_ref(name, description, id):
    cursor.execute(
        '''
        UPDATE refs SET name='{0}', description='{1}' WHERE id='{2}';
        '''.format(name, description, id)
    )
    conn.commit()

# Список простых связей
def select_pairs():
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
                    row_number() OVER (PARTITION BY area_description_1::text || area_description_2::text ORDER BY abs(to_number(r_value, '9.999999999999')) DESC)  AS rating_in_section
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
            WHERE rating_in_section <= 1
            ORDER BY abs(to_number(r_value, '9.999999999999')) DESC;
            ''')
    result = cursor.fetchall()
    return result


# Модель
def select_model(model_id):
    cursor.execute('''SELECT * FROM math_models WHERE id='{0}';'''.format(model_id))
    model = cursor.fetchall()

    return model

# Сложные связи
def select_complex_models(type):
    cursor.execute(
        '''
        SELECT * FROM complex_models WHERE type = {0} LIMIT 5;
        '''.format(type)
    )
    result = cursor.fetchall()
    return result

# Сведения о модели
def select_complex_model(model_id):
    cursor.execute(
        '''
        SELECT * FROM complex_models WHERE id = '{0}';
        '''.format(model_id)
    )
    result = cursor.fetchall()
    return result

# Измерения модели
def select_complex_model_measures(model_id):
    cursor.execute(
        '''
        SELECT * FROM complex_model_measures WHERE complex_model_id = '{0}';
        '''.format(model_id)
    )
    result = cursor.fetchall()
    return result


# Простые связи
def select_complex_model_pairs(model_id):
    cursor.execute(
        '''
        SELECT * FROM complex_model_pairs WHERE complex_model_id = '{0}';
        '''.format(model_id)
    )
    result = cursor.fetchall()
    return result

# Получение последнй операции загрузки данных
def select_data_log(id):
    cursor.execute(
        '''
        SELECT *
        FROM 
            data_log 
        WHERE data_area_id = '{0}'
        ORDER BY id DESC LIMIT 1;
        '''.format(id)
    )
    result = cursor.fetchall()
    return result