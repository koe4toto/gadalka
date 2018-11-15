import constants
import statistic_math as sm
import foo
import numpy as np
import random
import xlrd
import json
import database as db
import datetime
import xlwt
import os

cursor = db.cursor
conn = db.conn
data_cursor = db.data_cursor
data_conn = db.data_conn

# В начале я знаю идентификаторы измерений, которые нужно взять для анализа
def take_lines (line1, line2, len=100):
    # Измерения
    try:
        cursor.execute(
            '''
            SELECT 
                measures.column_name, 
                data_area.database_table 
            FROM 
                measures 
            LEFT JOIN data_area ON measures.data_area_id = data_area.id
            WHERE measures.id = '{0}' OR measures.id = '{1}';
            '''.format(line1, line2))
        measures = cursor.fetchall()
    except:
        return None

    # Название таблицы, в котрой хранятся данные
    database_table = measures[0][1]

    # Данные
    data_cursor.execute(
        '''
        SELECT {0}, {1} 
        from (select row_number() 
        over (order by {0}) num, count(*) over () as count, {0}, {1}   
        from {2} p)A where case when count > {3} then num %(count/{3}) = 0 else 1 = 1 end;
        '''.format(measures[0][0], measures[1][0], database_table, len)
    )
    measure_data = data_cursor.fetchall()
    return measure_data

# Рассчета свойств модели и запись результатов в базу данных
def search_model(hypothesis, adid1, adid2):
    print('Старт!')

    # Получение списков данных
    xy = take_lines(adid1, adid2)
    if xy != None:
        XY = np.array(xy)
        x = [float(i[0]) for i in XY]
        y = [float(i[1]) for i in XY]
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

    # Сохранение результатов в базу данных
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
        cursor.execute("SELECT * FROM math_models m1 WHERE NOT (m1.r_value IS NOT NULL) LIMIT 1;")
        model = cursor.fetchall()
        if len(model) > 0:
            search_model(model[0][1], model[0][7], model[0][8])

primal_calc()


def gen_line(x, slope, imtersept):
    y = slope * x + imtersept
    Y = [i + random.randint(-10, 15) for i in y]
    return Y

# Данные степенной модели
def gen_powerrege(x, slope, intercept):
    y = intercept * np.power(slope, x)
    Y = [i + random.randint(-10, 15) for i in y]
    return Y

# Данные показательной модели 1
def gen_exponentialreg1(x, slope, intercept):
    y = slope * np.power(x, intercept)
    Y = [i + random.randint(-10, 15) for i in y]
    return Y

# Данные гиперболической модели 1
def gen_hyperbolicreg1(x, slope, intercept):
    y = slope / x + intercept
    Y = [i + random.randint(-10, 15) for i in y]
    return Y

# Данные гиперболической модели 2
def gen_hyperbolicreg2(x, slope, intercept):
    y = 1 / (slope * x + intercept)
    Y = [i + random.randint(-10, 15) for i in y]
    return Y

# Данные гиперболической модели 3
def gen_hyperbolicreg3(x, slope, intercept):
    y = 1 / (slope / x + intercept)
    Y = [i + random.randint(-10, 15) for i in y]
    return Y

# Данные логарифмической модели
def gen_logarithmic(x, slope, intercept):
    y = slope * np.log10(x) + intercept
    Y = [i + random.randint(-10, 15) for i in y]
    return Y

# Данные экспоненциальной модели 2
def gen_exponentialreg2(x, slope, intercept):
    y = slope * np.power(x * intercept, 2.718)
    Y = [i + random.randint(-10, 15) for i in y]
    return Y

def gen_data():
    x = np.array([random.random() * 100 for i in range(90)])
    line_1 = gen_hyperbolicreg1(x, 3, 2)
    line_2 = gen_hyperbolicreg1(x, 2, 3)

    X = np.vstack((x, line_1, line_2))
    end = X.transpose()

    for i in end:
        # Подключение к базе данных
        cursor.execute('INSERT INTO test_data (x, line_1, line_2) VALUES (%s, %s, %s);',
                       (i[0], i[1], i[2]))
        conn.commit()
    return end
