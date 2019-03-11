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


associations = [(157, 46, 44), (159, 46, 1000003)]

pairs = [[520, 57, 58], [326, 42, 43], [388, 47, 48], [524, 58, 59], [523, 57, 59], [552, 61, 62], [339, 42, 44], [374, 46, 47], [387, 46, 48], [340, 43, 44]]
# Определение множестенной связи
def multiple(models):
    hash = {}

    mms = {}

    model_list = {}
    for num, i in enumerate(models):
        if i[1] not in hash:
            hash.setdefault(i[1], num)
            mms.setdefault(num, [i[1], i[2]])
            model_list.setdefault(num, [i[0]])

        else:
            if i[2] not in mms[hash[i[1]]]:
                mms[hash[i[1]]].append(i[2])
                hash.setdefault(i[2], hash[i[1]])

            if i[0] not in model_list[hash[i[1]]]:
                model_list[hash[i[1]]].append(i[0])


        if i[2] not in hash:
            hash.setdefault(i[2], num)
            if num not in model_list:
                model_list.setdefault(num, [i[0]])
        else:
            if i[0] not in model_list[hash[i[1]]]:
                model_list[hash[i[1]]].append(i[0])

    result = [mms[i] for i in mms if len(mms[i])>2]
    models_id = [model_list[i] for i in model_list if len(model_list[i]) > 1]

    return result, models_id

# Поиск рядов ассоциированных измерений и подстановка их в список моделей
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
    print('Ассоциации: ', result)

    # Подстановка ассоциаций вместо измерений. Теперь они станут ключём для сбора множественной модели
    # с учетом дополнительных связей
    for num, i in enumerate(mod):
        if i[1] in hash2:
            list1 = result[hash2[i[1]]]
            str1 = ','.join(str(e) for e in list1)
            mod[num][1] = str1

        if i[2] in hash2:
            list1 = result[hash2[i[2]]]
            str1 = ','.join(str(e) for e in list1)
            mod[num][2] = str1

    return mod

# Итоговое получение сложных моделей выраженых в измерениях и простых связях
def count_measures(associations, pairs):

    # Для отчищения от лишних ассоциаций делается плоский список id измерений в выбранных моделях
    pi = [[i[1], i[2]] for i in pairs]
    p_list = np.array(pi)
    flot = p_list.ravel()

    # Избавляемся от ассоциаций, которых нет в списке моделей
    good_ass = []
    for i in associations:
        if i[1] in flot and i[2] in flot:
            good_ass.append(i)

    complex_models, complex_models_id = multiple(group_associations(good_ass, pairs))
    result = []
    for model in complex_models:
        new_model = []
        for i in model:
            item = str(i)
            list = item.split(',')
            for measure in list:
                if int(measure) not in new_model:
                    new_model.append(int(measure))
        result.append(new_model)

    return result, complex_models_id

print('Пары: ', pairs)
print('Сложные связи без ассоциаций: ', multiple(pairs))
complex_models, complex_models_id = count_measures(associations, pairs)
print('Сложные модели (измерениями): ', complex_models)
print('Сложные модели (идентификаторами): ', complex_models_id)
