import psycopg2
import constants
import statistic_math as sm
import foo
import numpy as np
import random
import xlrd
import json
import database as db


# Подключение к базе данных
conn = psycopg2.connect(
    database=constants.DATABASE_NAME,
    user=constants.DATABASE_USER,
    password=constants.DATABASE_PASSWORD,
    host=constants.DATABASE_HOST,
    port=constants.DATABASE_PORT)
cursor = conn.cursor()

data = 'edu_test'


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

#print(gen_data())
#primal_calc()


#print(foo.numline(70))

db = db.db_connection()

print(db.conn.cursor())



