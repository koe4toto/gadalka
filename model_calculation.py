import statistic_math as sm
import numpy as np
import database as db

cursor = db.cursor
conn = db.conn
data_cursor = db.data_cursor
data_conn = db.data_conn

# Определение типа измерения и вывод строчки для соответствуующего запроса
def time_to_num(measure):
    if measure[3] == 4 or measure[3] == 5 or measure[3] == 6:
        result = 'EXTRACT(EPOCH FROM {0} )'.format(measure[0])
    else:
        result = measure[0]
    return result


# Данные для анализа
def take_lines (line1, line2, limit=None):

    # Измерения
    try:
        cursor.execute(
            '''
            SELECT 
                measures.column_name, 
                data_area.database_table,
                data_area.id,
                measures.type
            FROM 
                measures 
            LEFT JOIN data_area ON measures.data_area_id = data_area.id
            WHERE measures.id = '{0}' OR measures.id = '{1}';
            '''.format(line1, line2))
        measures = cursor.fetchall()
    except:
        return None, False, None

    # Название таблицы, в котрой хранятся данные
    database_table = measures[0][1]
    database_id = measures[0][2]

    me1_alt = time_to_num(measures[0])
    me2_alt = time_to_num(measures[1])

    # Данные
    # Выборка всех данных
    if limit == None:
        data_cursor.execute(
            '''
            SELECT {0} as A, {1} as B  
            FROM {2} WHERE {0} IS NOT NULL OR {1} IS NOT NULL;
            '''.format(me1_alt, me2_alt, database_table)
        )
        measure_data = data_cursor.fetchall()
    else:
        data_cursor.execute(
            '''
            SELECT B1, B2 
            from (
                select row_number() 
                over (order by {0}) num, count(*) over () as count, {0} as B1, {1} as B2   
                from {2} p WHERE {0} IS NOT NULL OR {1} IS NOT NULL)A 
            where case when count > {3} then num %(count/{3}) = 0 else 1 = 1 end; 
            '''.format(me1_alt, me2_alt, database_table, limit)
        )
        measure_data = data_cursor.fetchall()
    return measure_data, database_table, database_id

def measure_stats(x, id):
    x_stats = sm.Series(x).stats_line()

    # Сохранение результатов в базу данных. Записываются данные по модели.
    cursor.execute(
        '''
        UPDATE 
            measures 
        SET 
            len='{1}',
            sum='{2}',
            min='{3}',
            max='{4}',
            max_freq='{5}',
            ptp='{6}',
            mean='{7}',
            median='{8}',
            mode='{9}',
            average='{10}',
            std='{11}',
            var='{12}',
            sem='{13}',
            iqr='{14}'
        WHERE 
            id = '{0}';
        '''.format(
            id,
            x_stats['Размер выборки'],
            x_stats['Сумма'],
            x_stats['Минимум'],
            x_stats['Максимум'],
            x_stats['Максимальная частота'],
            x_stats['Размах'],
            x_stats['Среднее'],
            x_stats['Медиана'],
            x_stats['Мода'],
            x_stats['Средневзвешенное'],
            x_stats['Стандартное отклонение'],
            x_stats['Дисперсия'],
            x_stats['Стандартная ошибка средней'],
            x_stats['Межквартильный размах']
        )
    )
    conn.commit()

# Рассчета свойств модели и запись результатов в базу данных
def search_model(hypothesis, x, y, adid1, adid2):
    print('Старт!')

    # Экземпляр класса обработки данных по парам
    pairs = sm.Pairs(x, y)

    # Справочник гипотез
    hypotheses = {
        1: pairs.linereg,
        2: pairs.powerreg,
        3: pairs.exponentialreg1,
        4: pairs.hyperbolicreg1,
        5: pairs.hyperbolicreg2,
        6: pairs.hyperbolicreg3,
        7: pairs.logarithmic,
        8: pairs.exponentialreg2
    }

    # Рассчета показателей по указанной в базе модели
    slope, intercept, r_value, p_value, std_err = hypotheses[hypothesis]()
    print(slope, intercept, r_value, p_value, std_err, pairs.xstat_div, pairs.ystat_div)

    # Сохранение результатов в базу данных. Записываются данные по модели.
    cursor.execute(
        '''
        UPDATE 
            math_models 
        SET 
            slope='{0}', 
            intercept='{1}', 
            r_value='{2}', 
            p_value='{3}', 
            std_err='{4}', 
            xstat_div='{5}',
            ystat_div='{6}'
        WHERE area_description_1 = '{7}' AND area_description_2 = '{8}' AND hypothesis = '{9}';'''.format(
            slope,
            intercept,
            r_value,
            p_value,
            std_err,
            pairs.xstat_div,
            pairs.ystat_div,
            adid1,
            adid2,
            hypothesis

        )
    )
    conn.commit()

    print('Готово!')

# Обработка моделей с пустыми значениями
def primal_calc(data_area_id, log_id):

    # Список моделей
    cursor.execute('''SELECT * FROM math_models WHERE data_area_id = '{0}';'''.format(data_area_id))
    model = cursor.fetchall()

    if len(model) <= 1:
        # Изменить статус предметной области, измерений
        cursor.execute(
            '''
            UPDATE data_log 
            SET 
                status='{1}' 
            WHERE id = '{0}';
            '''.format(log_id, '6')
        )
        conn.commit()
        return True

    for i in model:

        hypothesis = i[1]
        line_id_1 = i[10]
        line_id_2 = i[11]
        # Получение данных
        xy, database_table, database_id = take_lines(line_id_1, line_id_2)
        if xy == None:
            status = '4'
        else:
            XY = np.array(xy)
            x = [float(i[0]) for i in XY]
            y = [float(i[1]) for i in XY]

            # Рассчет статистки рядов
            measure_stats(x, line_id_1)
            measure_stats(y, line_id_2)

            # Рассчет параметров модели и запись их в базу
            search_model(hypothesis, x, y, line_id_1, line_id_2)
            status = '6'

            # Изменить статус предметной области, измерений
            cursor.execute(
                '''
                UPDATE measures 
                SET 
                    status='{3}'
                WHERE id = '{1}' OR id = '{2}';
                '''.format(database_id, line_id_1, line_id_2, status)
            )
            conn.commit()

        # Изменить статус предметной области, измерений
        cursor.execute(
            '''
            UPDATE data_log 
            SET 
                status='{1}' 
            WHERE id = '{0}';
            '''.format(log_id, status)
        )
        conn.commit()

# Определение сложных связей
def multiple_models_calc(data_area_id):

    # Выбирается три группы моделей по силе связи
    g = db.get_models(0.8)
    n = db.get_models(0.5)
    a = db.get_models(0)

    # Поиск сложных связей в каждой группе
    good = sm.agreg(g)
    norm = sm.agreg(n)
    all = sm.agreg(a)

    print('Хорошие', good)
    print('Пойдёт', norm)
    print('Плохие', all)

    # Удаление старых связей
    # TODO так как модель может состоять из измерений разных ПО, то удалять старые модели нужно внимательно
    '''
    try:
        cursor.execute(
            '''
    '''DELATE FROM complex_model_measures WHERE id = '{0}';'''
    '''.format(good)
        )
    except:
        pass
    '''
    # Запись новых связей в базу данных

    return True

# primal_calc(42)