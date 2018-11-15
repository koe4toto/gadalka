import statistic_math as sm
import numpy as np
import database as db

cursor = db.cursor
conn = db.conn
data_cursor = db.data_cursor
data_conn = db.data_conn

# Данные для анализа
def take_lines (line1, line2, len=100):
    # Измерения
    try:
        cursor.execute(
            '''
            SELECT 
                measures.column_name, 
                data_area.database_table,
                data_area.id 
            FROM 
                measures 
            LEFT JOIN data_area ON measures.data_area_id = data_area.id
            WHERE measures.id = '{0}' OR measures.id = '{1}';
            '''.format(line1, line2))
        measures = cursor.fetchall()
    except:
        return None, False

    # Название таблицы, в котрой хранятся данные
    database_table = measures[0][1]
    database_id = measures[0][2]

    # Данные
    # Выборка данных по распределению
    '''
    SELECT {0}, {1} 
    from (select row_number() 
    over (order by {0}) num, count(*) over () as count, {0}, {1}   
    from {2} p)A where case when count > {3} then num %(count/{3}) = 0 else 1 = 1 end;
    '''
    # Выборка всех данных
    data_cursor.execute(
        '''
        SELECT {0}, {1}   
        FROM {2} WHERE {0} IS NOT NULL OR {0} IS NOT NULL;
        '''.format(measures[0][0], measures[1][0], database_table)
    )
    measure_data = data_cursor.fetchall()
    return measure_data, database_table, database_id

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
    print(slope, intercept, r_value, p_value, std_err)

    # Сохранение результатов в базу данных. Записываются данные по модели.
    cursor.execute('UPDATE math_models SET '
                   'slope=%s, '
                   'intercept=%s, '
                   'r_value=%s, '
                   'p_value=%s, '
                   'std_err=%s '
                   'WHERE '
                   'area_description_1 = %s '
                   'AND area_description_2 = %s '
                   'AND hypothesis = %s;',
                   (slope,
                    intercept,
                    r_value,
                    p_value,
                    std_err,
                    adid1,
                    adid2,
                    hypothesis
                    ))
    conn.commit()

    print('Готово!')

# Обработка моделей с пустыми значениями
def primal_calc():
    model = [1]
    while len(model) > 0:
        cursor.execute('''SELECT * FROM math_models m1 WHERE NOT (m1.r_value IS NOT NULL) LIMIT 1;''')
        model = cursor.fetchall()
        hypothesis = model[0][1]
        line_id_1 = model[0][7]
        line_id_2 = model[0][8]
        if len(model) > 0:
            # Получение списков данных
            xy, database_table, database_id = take_lines(line_id_1, line_id_2)
            if xy != None:
                XY = np.array(xy)
                x = [float(i[0]) for i in XY]
                y = [float(i[1]) for i in XY]

            search_model(hypothesis, x, y, line_id_1, line_id_2)

    # Изменить статус предметной области, измерений
    cursor.execute(
        '''
        UPDATE data_area 
        SET 
            status='6' 
        WHERE id = '{0}';
        '''.format(database_id)
    )
    conn.commit()

#primal_calc()