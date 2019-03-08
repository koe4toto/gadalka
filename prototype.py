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
            try:
                mms[hash[i[1]]].append(i[2])
            except:
                pass

        if i[2] not in hash:
            hash.setdefault(i[2], num)
        else:
            hash[i[1]] = hash[i[2]]
            mms[hash[i[2]]].append(i[1])

    result = [mms[i] for i in mms if len(mms[i])>2]

    return result

# Поиск рядов ассоциированных измерений
def group_associations(associats, mod):
    pair = [[i[1], i[2]] for i in associats]

    # Временнный словарь уникальных измерений
    hash = {}
    hash2 = {}

    # Временнный словарь ассоциированных измерений. Содержит списки без пар.
    result = {}
    for num, i in enumerate(pair):
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
            hash2.setdefault(i[1], num)
        else:
            hash[i[0]] = hash[i[1]]
            result[hash[i[1]]].append(i[0])
            hash2.setdefault(i[0], hash[i[0]])

    # Подстановка ассоциаций вместо измерений. Теперь они станут ключём для сбора множественной модели
    # с учетом дополнительных связей
    komp = [i for i in mod]
    for num, i in enumerate(komp):
        if i[1] in hash2:
            list1 = result[hash2[i[1]]]
            str1 = ','.join(str(e) for e in list1)
            komp[num][1] = str1

        if i[2] in hash2:
            list1 = result[hash2[i[2]]]
            str1 = ','.join(str(e) for e in list1)
            komp[num][2] = str1

    return komp


print('Пары: ', pairs)
print('Сложные связи без ассоциаций: ', multiple(pairs))
print('Ассоциированные пары: ', group_associations(associations, pairs))
print('Сложные модели: ', multiple(group_associations(associations, pairs)))
