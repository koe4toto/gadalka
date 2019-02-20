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


def TextAreaField(x):
    print('Текстовое поле: ', x)

def StringField(x, choices=None):
    print('Строка: ', x, choices)

def SubmitField(x):
    print('Сохранить: ', x)

# Классы полей ввода
forrms = {
    'TextAreaField':TextAreaField,
    'StringField':StringField
}

# Генератор формы принимает количество полей и список параметров для отображения
def Form(n, *args):
    class FormGenerator():
        pass

    for i in range(n):
        if args[i][1] == 'StringField':
            setattr(
                    FormGenerator, args[i][0], forrms[args[i][1]](args[i][2], choices=args[i][3])
            )
        else:
            setattr(
                FormGenerator, args[i][0], forrms[args[i][1]](args[i][2])
            )
    return FormGenerator()

# Список измерений пользователя
measures = [
    (1, 'Струлья', 'first', 'Первая', 4),
    (4, 'Люди', 'second', 'Вторая', 7),
    (2, 'Время', 'first', 'Первая', 4),
    (5, 'njnj', 'first', 'Первая', 4)
]

sorted_vehicles = sorted(measures, key=lambda x:x[2])
fin = []

for key, group in groupby(sorted_vehicles, lambda x: x[2]):
    choices = []
    for thing in group:
        choices.append((thing[0], thing[1]))
    item = [key, 'StringField', thing[3], choices]
    fin.append(item)

# Список полей для формы и их значений
for i in fin:
    print(i)
print('')

# Форма
Form(2, *fin)