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
import loading_from_file

cursor = db.cursor
conn = db.conn
data_cursor = db.data_cursor
data_conn = db.data_conn


# Рассчета свойств модели и запись результатов в базу данных
def search_model(hypothesis, adid1, adid2):
    print('Старт!')


    # Получение списков данных
    x = foo.numline(adid1, len=100)
    y = foo.numline(adid2, len=100)
    print(x)

    # Экземпляр класса обработки данных по парам
    pairs = sm.Pairs(x, y)

    # Справочник гипотез
    hypotheses = {
        1: pairs.linereg,
        2: pairs.powerreg,
        3: pairs.exponentialreg1,
        4: pairs.hyperbolicreg1,
        5: pairs.hyperbolicreg2,
        6: pairs.hyperbolicreg3,
        7: pairs.logarithmic,
        8: pairs.exponentialreg2
    }

    # Рассчета показателей по указанной в базе модели
    slope, intercept, r_value, p_value, std_err = hypotheses[hypothesis]()
    print(slope, intercept, r_value, p_value, std_err)

    # Сохранение результатов в базу данных
    cursor.execute('UPDATE math_models SET '
                   'slope=%s, '
                   'intercept=%s, '
                   'r_value=%s, '
                   'p_value=%s, '
                   'std_err=%s '
                   'WHERE '
                   'area_description_1 = %s '
                   'AND area_description_2 = %s '
                   'AND hypothesis = %s;',
                   (slope,
                    intercept,
                    r_value,
                    p_value,
                    std_err,
                    adid1,
                    adid2,
                    hypothesis
                    ))
    conn.commit()

    print('Готово!')


# Обработка моделей с пустыми значениями
def primal_calc():
    # Выбор модели для рассчета
    cursor.execute("SELECT * FROM math_models m1 WHERE NOT (m1.r_value IS NOT NULL) LIMIT 1;")
    model = cursor.fetchall()
    print(model)

    while model != '[]':
        search_model(model[0][1], model[0][7], model[0][8])

        # Выбор модели для рассчета
        cursor.execute("SELECT * FROM math_models m1 WHERE NOT (m1.r_value IS NOT NULL) LIMIT 1;")
        model = cursor.fetchall()
        print(model)


#primal_calc()


#print(gen_data())
#primal_calc()


#print(foo.numline(70))
data_cursor.execute('''SELECT * FROM data_queue LIMIT 1;''')
result = data_cursor.fetchall()
print(result)

id = result[0][0]
data_area_id = result[0][1]
filename = result[0][2]
type = result[0][3]
user = result[0][4]
fin = loading_from_file.start(id,data_area_id, filename, type)

# Удаление отработаной задачи
data_cursor.execute(
    '''
    DELETE 
    FROM 
        data_queue 
    WHERE id=%s;
    ''', [result[0][0]]
)
data_conn.commit()
print(fin)


