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

def versions():
    good = get_models(0.8)
    norm = get_models(0.5)
    all = get_models(0)
    return good, norm, all

good, norm, all = versions()


for i in good:
    print('Хорошие:', i)

for i in norm:
    print('Посредственные:', i)

for i in all:
    print('Плохие:', i)

# Расчет корреляций моделей и запись в базу

# Поиск многомерной модели среди ряда пар
def agreg(m):
    # Список пар
    models = [[i[4], i[5]] for i in m]
    # Список сложных моделей
    result = []

    # Список идентицикатором парных моделей в многомерной модели
    ides = []

    # Список коэфициентов корреляции моделей
    koefs = []

    # Список названий измерений
    names = []

    # Поиск модели в списке
    for i in models:
        model = [n for n in models if i[0] in n or i[1] in n]
        for i in model:
            for o in i:
                for p in models:
                    if o in p and p not in model:
                        model.append(p)
        # Из списка пар исключаются те, что собрались в модель
        models = [t for t in models if t not in model]

        # Добавляем слождую модель в итоговый список
        if len(model) >=2:
            result.append(model)

    # Формирование списка идентификаторов парных моделей для каждой многомерной модели
    for i in result:
        ids = []
        for k in i:
            for p in m:
                p2 = [p[4], p[5]]
                if k == p2:
                    ids.append(p[6])

        ides.append(ids)

    # TODO нужно рассчет корреляции сделать отдельной функцией

    # Формирование списка корреляций моделей
    '''
    Для каждой многомерной модели необходимо составить корреляционную матрицу,
    где в каждой колонке корреляция каждого параметра с каждым
    
    Корреляция это корень из разницы единицы и отношения определителя матрицы к алгебраическому дополнению 
    самого дальнего первого элемента матрицы
    
    Алгебраическое дополнение (минор) элемента это определитель матрицы, где удалена строка и столбец данного элемента
    
    # Определитель матрицы
    np.linalg.det(a)
    
    Соответсвенно требуется:
    1. Собрать корреляционную матрицу
    2. Найти общий определитель
    3. Получить матрицу для минора перового элемента
    4. Найти определитель - минор
    5. Посчитать корреляцию множественной модели
    
    '''

    return ides

mg = agreg(good)
if len(mg) > 0:
    print('Найдены', len(mg),'модели', mg)

mn = agreg(norm)
if len(mn) > 0:
    print('Найдены', len(mn),'модели', mn)

ma = agreg(all)
if len(ma) > 0:
    print('Найдены', len(ma),'модели', ma)

x1 = np.array([0.9375, 0.75, 0.4375, 2.0])

# Корреляционная матрица
lenx1 = len(x1)+1
x2 = [ [ x1[i-1-j] if j<i else x1[-i-1+j] for j in range(lenx1) ] for i in range(lenx1) ]
x2 = [ [ 1 if i==j else x2[i][j] for j in range(lenx1) ] for i in range(lenx1) ]
x3 = [ i for i in x2 if x2.index(i) != 0]
t = [1, 0.9375, 0.75, 0.4375, 2.0]
n = [i for i in t if i ]


# Определитель матрицы
mka = np.linalg.det(x2)
print('Определитель матрицы x2:', mka)
print('Матрица x2:')
for el in x2:
    print(el)


print('Матрица x3:')
for el in x4:
    print(el)

minor = np.linalg.det(x3)
print('Минор:', minor)