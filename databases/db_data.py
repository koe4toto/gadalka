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
            "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_{0}'),
            "data_log_id" integer
        );
        
        CREATE SEQUENCE auto_id_{0}_elements;

        CREATE TABLE {0}_elements (
            "id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_{0}_elements'), 
            "measure_id" int,
            "data_log_id" int,
            "value_id" varchar,
            "value_name" varchar,
            "value_max" varchar,
            "value_min" varchar,
            "frequency" varchar,  
            "mean" varchar
        );

        '''.format(olap_name))
    conn.commit()

# Удаление таблицы с данными
def delete_olap(olap_name):
    cursor.execute(
        '''
            DROP TABLE {0}; 
            DROP TABLE {0}_elements; 
            DROP SEQUENCE auto_id_{0};
             DROP SEQUENCE auto_id_{0}_elements;
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

# Удаление данных
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
def insret_data_to_olap(table_name, names_to_record, data_to_record, log_id):
    cursor.execute(
        '''
        INSERT INTO {0} (
            data_log_id,
            {1}
        ) VALUES ({3}, {2});
        '''.format(table_name, names_to_record, data_to_record, log_id)
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

# Выборка всех данных
def select_data_from_olap(me1_alt, me2_alt, database_table, limit):
    # Выборка всех данных
    if limit == None:
        cursor.execute(
            '''
            SELECT {0} as A, {1} as B  
            FROM {2} WHERE {0} IS NOT NULL OR {1} IS NOT NULL;
            '''.format(me1_alt, me2_alt, database_table)
        )
        measure_data = cursor.fetchall()
    else:
        cursor.execute(
            '''
            SELECT B1, B2 
            from (
                select row_number() 
                over (order by {0}) num, count(*) over () as count, {0} as B1, {1} as B2   
                from {2} p WHERE {0} IS NOT NULL OR {1} IS NOT NULL)A 
            where case when count > {3} then num %(count/{3}) = 0 else 1 = 1 end; 
            '''.format(me1_alt, me2_alt, database_table, limit)
        )
        measure_data = cursor.fetchall()
    return measure_data

def measure_data_set(table, column):
    cursor.execute(
        '''
        SELECT {1}  
        FROM {0} 
        WHERE {1} IS NOT NULL;
        '''.format(table, column)
    )
    measure_data = cursor.fetchall()
    return measure_data


# Статистики ряда
def select_stats_general_line(table, column, log_id):
    log = str

    if log_id != '':
        log = 'AND data_log_id = {0}'.format(log_id)
    else:
        log = ''

    cursor.execute(
    '''
    SELECT 
        count(A) as len,
        sum(A) as sum,
        max(A) as max,
        min(A) as min,
        max(A)-min(A) as ptp,
        avg(A) as mean,
        percentile_cont(0.5) within group (order by A) as median,
        percentile_cont(0.1) within group (order by A) as first_decil,
        percentile_cont(0.9) within group (order by A) as last_decil,
        percentile_cont(0.9) within group (order by A)/percentile_cont(0.1) within group (order by A) as decil_koef,
        percentile_cont(0.75) within group (order by A)-percentile_cont(0.25) within group (order by A) as iqr,
        mode() within group (order by A) as mode,
        (SELECT COUNT(*) FROM {0} WHERE {1} IS NOT NULL {2} GROUP BY {1} LIMIT 1) as frq,
        var_pop(A) as var,
        stddev_pop(A) as pop,
        stddev_pop(A)/(|/count(A)) as sem,
        variance(A) as variance
    FROM 
        (
            SELECT {1} as A
            FROM {0} 
            WHERE {1} IS NOT NULL {2}
        )B; 
    '''.format(table, column, log)
    )
    result = cursor.fetchall()[0]
    return result

# Выборка всех данных
def select_columns_to_simple_report(columns, database_table, limit, offset, order_by, left_join, where):
    # Выборка всех данных
    cursor.execute(
        '''
        SELECT {0}  
        FROM {1}
        {5}
        {6}
        ORDER BY {4}
        LIMIT {2} OFFSET {3}
        ;
        '''.format(columns, database_table, limit, offset, order_by, left_join, where)
    )
    measure_data = cursor.fetchall()

    return measure_data

# Получение общего количества записей
def select_data_count(columns, database_table, left_join, where):
    # Выборка всех данных
    cursor.execute(
        '''
        SELECT count(*) 
        FROM (
            SELECT {0}  
            FROM {1}
            {2}
            {3}
            )A;
        '''.format(columns, database_table, left_join, where)
    )
    measure_data = cursor.fetchall()

    return measure_data

# Удаление данных из оперативной БД
def delete_oldest_partitions(olap, limit):
    try:
        cursor.execute(
        '''
            with linmit_num as (
                select DISTINCT data_log_id as data_log_ids 
                from {0}
                ORDER BY data_log_ids 
            )
            delete from {0} 
            WHERE data_log_id in (
            select * 
            from linmit_num 
            limit 
                (case 
                 when (select count(data_log_ids) from linmit_num) >= {1} 
                 then {1}-(select count(data_log_ids) from linmit_num)+1 
                 else 0 
                 end
            ));
        '''.format(olap, limit)
        )
        conn.commit()
    except:
        pass

# Расчет и запись частотных характеристик выборки
def insert_stat_freqs():
    try:
        cursor.execute(
        # Пример запроса для качественных данных
        '''
        insert into items_ver (item_group, name, item_id)
        select item_id, name as z, item_group from items;
        '''
        )
        conn.commit()
    except:
        pass

def agr_freq_table_for_numeric_measure(olap, meeasure_id, data_log_id, measure_name):
    try:
        cursor.execute(
        '''
        with step as(
            SELECT
                (max({3})- min({3}))/round(1+ |/COUNT(*)) as h
            FROM {0}
        ),
        freq as(
        SELECT 
            '{1}'::integer as measure_id,
            '{2}'::integer as data_log_id,
            min({3}) || '-' || max({3}) as value_name,
            min({3}) as value_min,
            max({3}) as value_max,
            count(*) as frequency,
            avg({3}) as mean 
        FROM {0}
        group by round({3} / (select h from step)))
        INSERT INTO {0}_elements (measure_id, data_log_id, value_name, value_min, value_max, frequency, mean) 
            select measure_id, data_log_id, value_name, value_min, value_max, frequency, mean from freq;
        '''.format(olap, meeasure_id, data_log_id, measure_name)
        )
        conn.commit()
    except:
        pass

def agr_freq_table_for_ref_quantitative_measure(olap, meeasure_id, data_log_id, measure_name):
    try:
        cursor.execute(
        '''
        with freq as(
            SELECT 
                '{1}'::integer as measure_id,
                '{2}'::integer as data_log_id,
                {3} as value_id,
                count(*) as frequency
            FROM {0}
            group by {3})
        INSERT INTO {0}_elements (measure_id, data_log_id, value_id, frequency) 
            select measure_id, data_log_id, value_id,frequency from freq;
        '''.format(olap, meeasure_id, data_log_id, measure_name)
        )
        conn.commit()
    except:
        pass


def agr_freq_table_for_quantitative_measure(olap, meeasure_id, data_log_id, measure_name):
    try:
        cursor.execute(
        '''
        with freq as(
            SELECT 
                '{1}'::integer as measure_id,
                '{2}'::integer as data_log_id,
                {3} as value_name,
                count(*) as frequency
            FROM {0}
            group by {3})
        INSERT INTO {0}_elements (measure_id, data_log_id, value_name, frequency) 
            select measure_id, data_log_id, value_name, frequency from freq;
        '''.format(olap, meeasure_id, data_log_id, measure_name)
        )
        conn.commit()
    except:
        pass