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



'''
1. Модели отбираются в рамках предметной области. Пока между областями модели построить не понятно как. 
Но об это следует подумать. Возможно следует измерения предметных областей связывать между собой 
и в результате агрегатно их анализировать
    
2. Выбираем три типа моделей: 
    1. Модели из пар с высокой (>0,8) корреляцийе, 
       1. Выбираем все подходящие модели
       2. Выбираем модели из пар и их измернения.
        3. Сохраняем многомерную модель, список её измерений, список парных 
       моделей
    2. Модели из пар со слабыми (>0,5) корреляциями, 
    3. Модели из всех пар
4. Состав данных многомерной модели
    id
    Список измерений
    Список парных моделей
    Тип (автоматическая, пользовательская)
    Название
    Комментарий
    Дата и время рассчета
    Коэффициент корреляции
5. Пока понятно как предсказать значения при фиксированном одном.
6. При пересчете парных моделей нужно пересчитывть многомерные
7. При удалении измерения (при удалении ПО так же), нужно обновлять многомерные модели. Удалить так же и отобранные 
модели 
'''

# Выбрать модели соответсвующие искомой корреляции: уучшие, средние, общая

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
            WHERE rating_in_section <= 1 AND abs(to_number(r_value, '9.999999999999')) >= '{0}'
            ORDER BY abs(to_number(r_value, '9.999999999999')) DESC;
            '''.format(limit))
    list = cursor.fetchall()
    return list
id1 = 6
id2 = 7

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

for i in list:
    print(i)