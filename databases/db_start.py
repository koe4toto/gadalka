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

status = {
    1: 'Нет данных',
    2: 'Ожидает обработки',
    3: 'Обработка данных',
    4: 'Данных недостаточно для анализа',
    5: 'Поиск связей',
    6: 'Обработано'
}

measure_type = {
    1: 'Количественные данные',
    2: 'Качественные данные',
    3: 'Качественные данные по справочнику',
    4: 'Время',
    5: 'Дата',
    6: 'Дата и время'
}

statistics_type = {
    1: 'Порция',
    2: 'Генеральная выборка'
}

statistics_kind = {
    1: 'Размер выборки',
    2: 'Сумма',
    3: 'Минимум',
    4: 'Максимум',
    5: 'Максимальная частота',
    6: 'Размах',
    7: 'Среднее',
    8: 'Медиана',
    9: 'Мода',
    10: 'Средневзвешенное',
    11: 'Стандартное отклонение',
    12: 'Дисперсия',
    13: 'Стандартная ошибка средней',
    14: 'Межквартильный размах',
    15: 'Коэффициент Джини',
    16: 'Третий момент распределения',
    17: 'Четвертый момент распределения',
    18: 'Вариация',
    19: 'Последнее значение первого дециля',
    20: 'Первое значение последнего дециля',
    21: 'Децильный коэффициент',
    22: 'Сумма значений первого дециля',
    23: 'Сумма значений последнего дециля',
    24: 'Фондовый коэффициент',
    25: 'Оценка вероятности нормального распределения в выборке'
}


# Заполнение справочника
def update_ref(ref, name):
    for i in ref:
        cursor.execute(
            '''
            INSERT 
            INTO ''' + name + ''' (
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

# TODO перенести заполнение таблиц в start_app
# TODO создавать БД queue и создание таблицы
# TODO создавать БД user_data
# Создание таблиц
def start_app():

    # Ассоциации
    cursor.execute(
        '''
        CREATE SEQUENCE auto_id_association;

        CREATE TABLE association 
        (
            "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_association'), 
            "measure_id_1" integer, 
            "measure_id_2" integer
        );
        '''
    )

    # Сложные связи
    cursor.execute(
        '''
        CREATE SEQUENCE auto_id_complex_models;
        CREATE SEQUENCE auto_id_complex_model_measures;
        CREATE SEQUENCE auto_id_complex_model_pairs;

        CREATE TABLE complex_models 
        (
            "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_complex_models'), 
            "name" varchar(300), 
            "description" varchar(600), 
            "pairs" varchar,
            "type" integer, 
            "kind" integer,
            "register_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE complex_model_measures 
        (
            "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_complex_model_measures'), 
            "complex_model_id" integer, 
            "measure_id" integer, 
            "data_area_id" integer,
            "model_type" integer 
        );

        CREATE TABLE complex_model_pairs 
        (
            "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_complex_model_pairs'), 
            "complex_model_id" integer, 
            "pair_id" integer,
            "model_type" integer 
        );
        '''
    )

    # Предметные области
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
            "register_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            "partition_limit" integer
        );

        CREATE TABLE ref_status (
            "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_ref_status'), 
            "code" varchar(100), 
            "name" varchar(600)
        );
        '''
    )

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

    # Параметры
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
            "iqr" varchar,
            "unit_of_measurement" int

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

    # Пользователи
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

    # Единицы измерений
    cursor.execute(
        '''
        CREATE SEQUENCE auto_id_unit_of_measurement;

        CREATE TABLE unit_of_measurement (
            "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_unit_of_measurement'), 
            "name" varchar(100), 
            "short_name" varchar(100), 
            "type" int, 
            "register_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''
    )

    # Подтверждение
    conn.commit()

    # Отчеты
    cursor.execute(
        '''
        CREATE SEQUENCE auto_id_reports;

        CREATE TABLE reports (
            "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_reports'), 
            "name" varchar(300), 
            "description" varchar(600), 
            "type" int, 
            "register_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            "user_id" varchar(30),
            "data_area_id" int,
            "preset_id" integer 
        );
        '''
    )

    # Подтверждение
    conn.commit()

    # Колонки или параметры отчета
    cursor.execute(
        '''
        CREATE SEQUENCE auto_id_measurement_report;

        CREATE TABLE measurement_report (
            "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_measurement_report'), 
            "report_id" int,
            "measure_id" int,
            "next_measure" int,
            "style" int
        );
        '''
    )

    # Подтверждение
    conn.commit()

    # Персеты
    cursor.execute(
        '''
        CREATE SEQUENCE auto_id_reports_presets;

        CREATE TABLE reports_presets
        (
            "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_reports_presets'), 
            "report_id" integer, 
            "name" varchar(300), 
            "preset" varchar,
            "register_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''
    )
    # Подтверждение
    conn.commit()

    # Статистики
    cursor.execute(
        '''
        CREATE SEQUENCE auto_id_statistics;
        CREATE SEQUENCE auto_id_ref_measures_type;
        CREATE SEQUENCE auto_id_ref_measures_kind;

        CREATE TABLE statistics (
            "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_statistics'), 
            "measure_id" int,
            "data_log_id" int, 
            "type" int,  
            "kind" int, 
            "value" varchar
        );

        CREATE TABLE ref_statistics_type (
            "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_ref_measures_type'), 
            "code" varchar(100), 
            "name" varchar(600)
        );

        CREATE TABLE ref_statistics_kind (
            "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_ref_measures_kind'), 
            "code" varchar(100), 
            "name" varchar(600)
        );

        '''
    )

    # Подтверждение
    conn.commit()