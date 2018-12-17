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

models = [[12,3],[10,2],[1,2],[1,4],[11,7],[4,2],[5,8],[9,2],[3,6],[2,5]]
etalon = [1,2,4,5,7,8,9,10]

# Поиск многомерной модели среди ряда пар
item = [8,5]
models2 = [[1,2],[3,1],[3,4],[3,8],[8,5],[5,15],[15,7], [10,9],[9,11], [6,12], [16,17],[17,19],[34,19], [0,14]]

# Поиск многомерной модели среди ряда пар
def agreg(m):
    models = m
    result = []
    for i in models:
        model = [n for n in models if i[0] in n or i[1] in n]
        for i in model:
            for o in i:
                for p in models:
                    if o in p:
                        if p not in model:
                            model.append(p)
        models = [t for t in models if t not in model]
        if len(model) >=2:
            result.append(model)
    return result

re = agreg(models2)
for i in re:
    print('Модели:', i)
