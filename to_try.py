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

me2_alt = 'EXTRACT(EPOCH FROM {0})'.format('datetime')
me1_alt = 'groups'
database_table = 'olap_62_1'
ui_limit = 500

data_cursor.execute(
    '''
    SELECT B1, B2 
    from (
        select row_number() 
        over (order by {0}) num, count(*) over () as count, {0} as B1, {1} as B2   
        from {2} p WHERE {0} IS NOT NULL OR {1} IS NOT NULL)A 
    where case when count > {3} then num %(count/{3}) = 0 else 1 = 1 end; 
    '''.format(me1_alt, me2_alt, database_table, ui_limit)
)
measure_data = data_cursor.fetchall()
print('Пщщщщщщщщщщщщщ:', measure_data)
print('Пщщщщщщщщщщщщщ:', me2_alt)

print('Готово, епта!')