import constants
import statistic_math as sm
import tools
import numpy as np
import random
import xlrd
import json
import datetime
import xlwt
import os
import psycopg2
import databases.db_app as db_app
import databases.db_data as db_data
import databases.db_queue as db_queue
from itertools import groupby
import math
import matplotlib.pyplot as plt
'''
Колонки для выгрузки из таблицы tmp_itmc_odli_diagnosis_mart
Только одна колонка соержит количественные данные

SELECT
  order_patient_age
FROM tmp_itmc_odli_diagnosis_mart
LIMIT 10;
'''

'''
Колонки для выгрузки из таблицы tmp_itmc_odli_observation_mart
Только одна колонка соержит количественные данные

SELECT
  diagnosticreport_patient_age
FROM tmp_itmc_odli_observation_mart
LIMIT 50;

'''

'''
Колонки для выгрузки из таблицы tmp_itmc_iemk_diagnosis_mart_short
Только одна колонка соержит количественные данные

Это похоже качественные данные: 
case_doctor_spec_code,
case_doctor_spec_high,
case_doctor_spec_okso

SELECT
  case_patient_age,
  case_doctor_spec_code,
  case_doctor_spec_high,
  case_doctor_spec_okso
FROM tmp_itmc_iemk_diagnosis_mart_short
LIMIT 50;
'''

'''
1. Преобразовывать качественные данные в количественные. 
Каким-то образом. Мало получится агрегатов. За три месяца около 100 штук на каждую колонку. 
Не очень эффектно может получиться.

2. Реализовать статистику качественных рядов. 
Это в принципе полезно. 

'''


# Количествно значений в выборке
N = int 

# Максимальное значение выборки
x_max = float

# Минимальное значение выборки
x_min = float

# Количествно интервалов на которые можно (нужно) разбить выборку. C округлением до целого.
#k = math.ceil(1 + math.log(N, [2]))

# Шаг разбиения выборки
#h = (x_max - x_min)/ k

# Первый и последний интервалы должны быть открытыми. То есть первы начинаться со значения менее x_min
# Последние должен заканчиваться значением больше x_max. Каждый следующий интервал имеет длинну h
# В итоге посчитав количество попаданий в интервалы можно построить частотную гистограмму

# Варианта - серезина интервала. Можно вычислить как сумму значения начала интервала и половины шага

# Среднее значение выборки или математическое ожидание
mean = float

# Среднее геометрическое. Корень по ооснованию N из произведения всех значения ряда.
# Прикладной смысл: среднее приращение величины
geo_mean = float

# Среднее квадратичесоке. Квадратный корень из суммы квадратов значений.
# Прикладной смысл: среднее квадратическое отклонение от среднего. Сигма.
std_mean = float

# График накопленной частоты. Комулята. Отображает сколько уникальных значений выборки имеет частоту ниже указанной.
# К прмиеру, показывает сколько людей моложе 18, далее сколько людей моложе 20
# и так далее согласно гистограмме распределения
# Прикладной смысл: помогает оценить равномерность распределения.
# Используя значения этого графика можено расчитать коффициент Джинни.
# Вычсляется как разница (половины квадрата максимальной накопленной частоты) и
# интеграла (площади) под графиокм накопленных частот
# Джинни показывает насколько неравномерно рапределение. К примеру как неравномерно распределены доходы.

# Моменты (центральные) распределения показывают силу отклоненияот нормального
# Первый центральный момент равен нулю
# Второй центральный момент равен дисперсии
# Третий центральный момент показывает насколько вершина распределения отклоняется от нормального по горизонтали.
# Положительное - смещение влево. Отрицательное - смещение вправо.
# Четверты центральный момент показывает насколько вершина распределения отклоняется от нормального по вертикали
# Моменты помогают оценить насколько распределение далеко от нормального.


# Вариация. Отношение Сигмы (среднеквадратичного отклодения или корня из дисперыии) к средней.
# Измеряется в процентах. Чем она меньше, тем меньше изменчивость, тем параметр стабильнее.
# Прикладной смысл: помогает оценить силу изменчивости наблюдаемого явления.


# Дисперсионная характеристика. Эмпирическое корреляционное соотношение.
# Показатель равен корню квадратному из отношения межгрупповой дисперсии к общей.
# Изменяется от 0 до 1. Чем больше, тем сильнее связь между количественным и качественным показателем.
# К примеру зависит ли средняя зарплата от района проживания.
#
# Общая дисперсия - это разброс всех значений количественного показателя.
#
# Межгрупповая дисперсия равна отношению (суммы произведений количества в каждой группе
# на (квадрат разницы среднего группы и общего среднего)) к (сумме всех значений выборки)
# Общая дисперсия складывается из суммы межгрупповой и внутрегрупповой дисперсий
#
# Следует расчитать дисперцию для наборов количественных данных каждого качественного значения,
# чтобы отыскать среднюю внутригрупповую дисперсию. В этом примере дисперсию в каждом районе.
# Средняя внутригрупповая дисперсия равна сумме произведений количества элементов в каждой группе (районе)
# поделенной на общее количество событий во всех группах


# Децильный коэффициент. Отношение начала последнего децияля к концу первого.
# В Дециль попадают десятая часть всех элементов выборки

# Фондовый коэффициент. Отношение суммы значений последнего децияля в сумме первого.
# В Дециль попадают десятая часть всех элементов выборки


from model_calculation import take_lines, search_model

models = np.array([
[2093, 115, 119],
[1665, 114, 115],
[1641, 106, 114],
[554, 61, 62],
[1711, 106, 115],
[1576, 110, 113],
[2018, 118, 119],
[1437, 106, 110],
[1571, 112, 113],
[1435, 108, 110],
[1567, 108, 113],
[1511, 110, 112],
[1572, 106, 113],
[1383, 106, 108],
[1659, 108, 115],
[34534, 112, 174],
[345345, 174, 205],
    [345345, 305, 205]
])

transp = models.transpose()
print(models)

hash = []
for i in models:
    if i[1] not in hash:
        hash.append(i[1])
    if i[2] not in hash:
        hash.append(i[2])


result = {}

for i in hash:
    result.setdefault(i, [[], [], []])
    for model in models:
        if i in model:
            result[i][0].append(model)
            if model[1] not in result[i][1]:
                result[i][1].append(model[1])
            if model[2] not in result[i][1]:
                result[i][1].append(model[2])
            if model[0] not in result[i][2]:
                result[i][2].append(model[0])
nemo = []
for i in hash:
    for t in result[i][1]:
        if i in result[i][1]:
            for to in result[i][1]:
                nemo.append(to)


# Поиск многомерной модели среди ряда пар
def agreg(m):
    # Список пар
    models = [[i[1], i[2]] for i in m]

    # Список сложных моделей
    result = []

    # Список идентицикатором парных моделей в многомерной модели
    ides = []

    # Список коэфициентов корреляции моделей
    measures = []

    # Поиск сложных свзяей в списке
    for i in models:
        # Для каждой простой модели в исходном спике собирается список моделей, вкоторой встретилось одно из измерений
        # Получается перечень связанных моделей по первым двум измерениям.
        model = [n for n in models if i[0] in n or i[1] in n]
        # Если есть ещё модели с такими же измерениями, то
        if len(model) >= 2:
            # Для каждой модели в получившейся сложной модели
            for i in model:
                # Снова перебираем все исходные модели
                for p in models:
                    # Если измерение есть в исходных моделях, но нет в текущей многомерной, то
                    if i[0] in p and p not in model:
                        # Добавляем модель в список
                        model.append(p)
                    if i[1] in p and p not in model:
                        # Добавляем модель в список
                        model.append(p)
            # Из списка пар исключаются те, что собрались в модель
            models = [t for t in models if t not in model]

            # Добавляем слождую модель в итоговый список
            if len(model) >=2:
                result.append(model)

    # Формирование списка идентификаторов парных моделей для каждой многомерной модели
    for i in result:
        ids = []
        mea = []
        for k in i:
            for p in m:
                p2 = [p[1], p[2]]
                if k == p2:
                    ids.append(p[0])
                    next1 = [p[0], p[1], p[2]]
                    if next1 not in mea:
                        mea.append(next1)
                    next2 = [p[0], p[1], p[2]]
                    if next2 not in mea:
                        mea.append(next2)

        ides.append(ids)
        measures.append(mea)

    return measures

for pop in result:
    print('result', pop, result[pop][1])

print(agreg(models))
