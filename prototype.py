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


associations = [
    [1, 2, 6],
    [2, 5, 21],
    [3, 8, 25],
    [4, 2, 22],
    [5, 6, 7],
    [6, 21, 9],
    [7, 23, 24]
]

pairs = [
    [1, 1, 2],
    [2, 5, 2],
    [3, 3, 8],
    [4, 4, 6],
    [5, 7, 6],
    [6, 22, 21],
    [7, 21, 24],
    [8, 23, 25],
    [9, 5, 9]
]

def multiple(models):
    hash = {}

    mms = {}
    for num, i in enumerate(models):
        if i[1] not in hash:
            hash.setdefault(i[1], num)
            mms.setdefault(num, [i[1], i[2]])
        else:
            mms[hash[i[1]]].append(i[2])

        if i[2] not in hash:
            hash.setdefault(i[2], num)
        else:
            hash[i[1]] = hash[i[2]]
            mms[hash[i[2]]].append(i[1])

    result = [mms[i] for i in mms if len(mms[i])>2]

    return result

mms = multiple(pairs)
print('Сложные связи: ', mms)

# Поиск рядов ассоциированных измерений
def group_associations(associats, mod):
    pairs = [[i[1], i[2]] for i in associats]

    # Временнный словарь уникальных измерений
    hash = {}
    hash2 = {}

    # Временнный словарь ассоциированных измерений. Содержит списки без пар.
    result = {}
    for num, i in enumerate(pairs):
        if i[0] not in hash:
            hash.setdefault(i[0], num)
            result.setdefault(num, [i[0], i[1]])
            hash2.setdefault(i[0], num)
            hash2.setdefault(i[1], num)
        else:
            result[hash[i[0]]].append(i[1])
            hash2.setdefault(i[1], hash[i[0]])

        if i[1] not in hash:
            hash.setdefault(i[1], num)
            result.setdefault(num, [i[1]])
            hash2.setdefault(i[1], num)
        else:
            result[hash[i[0]]].append(i[0])
            hash2.setdefault(i[0], hash[i[0]])

    # Итоговая матрица наборов ассоциаций
    final = [result[i] for i in result if len(result[i])>1]

    # Подстановка ассоциаций вместо измерений. Теперь они станут ключём для сбора множественной модели
    # с учетом дополнительных связей
    for num, i in enumerate(mod):
        if i[1] in hash2:
            mod[num][1] = result[hash2[i[1]]]

        if i[2] in hash2:
            mod[num][2] = result[hash2[i[2]]]

    return mod


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
    # TODO переписать с помощью itertools
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

    # Формирование списка
    remod = []

    # Формирование списка идентификаторов парных моделей для каждой многомерной модели
    # TODO переписать с помощью itertools
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
        remod.append([mea, ids])
    return result
print('Пары: ', pairs)
multiple_models_si = agreg(pairs)
mod = group_associations(associations, pairs)

#multiple_models = agreg(mod)
print('Ассоциированные пары: ', mod)
print('')
#print('Сложные модели: ', multiple_models_si)
