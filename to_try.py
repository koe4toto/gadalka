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
import psycopg2

cursor = db.cursor
conn = db.conn
data_cursor = db.data_cursor
data_conn = db.data_conn

queue_cursor = db.queue_cursor
queue_conn = db.queue_conn


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


me1 = 'date'
me1_alt = 'EXTRACT(EPOCH FROM {0} )'.format(me1)
me2 = 'students'
database_table = 'olap_62_1'

# Выборка всех данных
data_cursor.execute(
    '''
    SELECT {0}, {1}   
    FROM {2} WHERE {0} IS NOT NULL OR {0} IS NOT NULL;
    '''.format(me1_alt, me2, database_table)
)
measure_data = data_cursor.fetchall()

for i in measure_data:
    print(i)

line1 = 6
line2 = 7
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
date_conv = [(datetime.datetime.utcfromtimestamp(i[0]).strftime('%Y-%m-%d'), i[1]) for i in measure_data]
time_conv = [(datetime.datetime.utcfromtimestamp(i[0]).strftime('%H:%M:%S'), i[1]) for i in measure_data]
datetime_conv = [(datetime.datetime.utcfromtimestamp(i[0]).strftime('%H:%M:%S'), i[1]) for i in measure_data]
for i in time_conv:
    print(i)

x = [i[0] for i in measure_data]

x_stats = sm.Series(x).stats_line()


result = {'Размер выборки': x_stats['Размер выборки'],
          'Сумма': datetime.datetime.utcfromtimestamp(x_stats['Сумма']).strftime('%H:%M:%S'),
          'Минимум': datetime.datetime.utcfromtimestamp(x_stats['Минимум']).strftime('%H:%M:%S'),
          'Максимум': datetime.datetime.utcfromtimestamp(x_stats['Максимум']).strftime('%H:%M:%S'),
          'Максимальная частота': datetime.datetime.utcfromtimestamp(x_stats['Максимальная частота']).strftime('%H:%M:%S'),
          'Размах': datetime.datetime.utcfromtimestamp(x_stats['Размах']).strftime('%H:%M:%S'),
          'Среднее': datetime.datetime.utcfromtimestamp(x_stats['Среднее']).strftime('%H:%M:%S'),
          'Медиана': datetime.datetime.utcfromtimestamp(x_stats['Медиана']).strftime('%H:%M:%S'),
          'Мода': datetime.datetime.utcfromtimestamp(x_stats['Мода']).strftime('%H:%M:%S'),
          'Средневзвешенное': datetime.datetime.utcfromtimestamp(x_stats['Средневзвешенное']).strftime('%H:%M:%S'),
          'Стандартное отклонение': datetime.datetime.utcfromtimestamp(x_stats['Стандартное отклонение']).strftime('%H:%M:%S'),
          'Дисперсия': datetime.datetime.utcfromtimestamp(x_stats['Дисперсия']).strftime('%H:%M:%S'),
          'Стандартная ошибка средней': datetime.datetime.utcfromtimestamp(x_stats['Стандартная ошибка средней']).strftime('%H:%M:%S'),
          'Межквартильный размах': datetime.datetime.utcfromtimestamp(x_stats['Межквартильный размах']).strftime('%H:%M:%S')
          }

print(result)
