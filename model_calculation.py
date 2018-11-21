import statistic_math as sm
import numpy as np
import database as db

cursor = db.cursor
conn = db.conn
data_cursor = db.data_cursor
data_conn = db.data_conn

# Данные для анализа
def take_lines (line1, line2):

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
        return None, False, None

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
    print(measure_data)
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
def primal_calc(data_area_id):

    cursor.execute('''SELECT * FROM math_models WHERE data_area_id = '{0}';'''.format(data_area_id))
    model = cursor.fetchall()
    print(model)
    for i in model:

        hypothesis = i[1]
        line_id_1 = i[10]
        line_id_2 = i[11]
        print(line_id_1, line_id_2)
        # Получение данных
        xy, database_table, database_id = take_lines(line_id_1, line_id_2)
        print(xy, database_table, database_id)
        if xy == None:
            status = '4'
        else:
            XY = np.array(xy)
            x = [float(i[0]) for i in XY]
            y = [float(i[1]) for i in XY]

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
            UPDATE data_area 
            SET 
                status='{1}' 
            WHERE id = '{0}';
            '''.format(database_id, status)
        )
        conn.commit()

primal_calc(42)