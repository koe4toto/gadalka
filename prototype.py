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

from model_calculation import take_lines, measure_stats
xy, database_table, database_id = take_lines(115, 110)
x = [float(i[0]) for i in xy]
y = [float(i[1]) for i in xy]

x_stats = sm.Series(x).stats_line()
y_stats = sm.Series(y).stats_line()
measure_stats(x, 115)
measure_stats(y, 110)
print(xy)
print(x)
print(y)
print(x_stats)
print(y_stats)