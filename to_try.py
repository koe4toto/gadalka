import psycopg2
import constants
import statistic_math as sm

# Подключение к базе данных
conn = psycopg2.connect(
    database=constants.DATABASE_NAME,
    user=constants.DATABASE_USER,
    password=constants.DATABASE_PASSWORD,
    host=constants.DATABASE_HOST,
    port=constants.DATABASE_PORT)
cursor = conn.cursor()

data = 'edu_test'

def search_model(data):
    print('Старт!')

    cursor.execute("SELECT * FROM math_models m1 WHERE NOT (m1.kk IS NOT NULL) LIMIT 1;")
    model = cursor.fetchall()
    print(model)
    # Рассчитать знаяение параметров указанной модели, запистаь в базу и вывести в консоли

    '''
    # Выбрать значения первой переменной
    cursor.execute("SELECT * FROM math_models m1 WHERE NOT (m1.kk IS NOT NULL) LIMIT 1;")
    X = cursor.fetchall()
    print(X)

    # Выбрать значения второй переменной
    cursor.execute("SELECT * FROM math_models m1 WHERE NOT (m1.kk IS NOT NULL) LIMIT 1;")
    Y = cursor.fetchall()
    print(Y)

    # Рассчитать показатели
    slope, intercept, r_value, p_value, std_err = statistic_math.Pairs.linereg(X,Y)
    print(slope, intercept, r_value, p_value, std_err)
    '''

    x = [0.1, 1, 2, 3, 4, 5]
    y = [5, 4, 3, 2, 1, 0.1]
    pairs = sm.Pairs(x, y)
    slope, intercept, r_value, p_value, std_err = pairs.logarithmic()
    print(slope, intercept, r_value, p_value, std_err)

    slope, intercept, r_value, p_value, std_err = pairs.linereg()
    print(slope, intercept, r_value, p_value, std_err)

    print('Готово!')

#search_model('edu_test')

def t1():
    print('test 1')

def t2():
    print('test 2')

mig = {1:t1, 2:t2}

pik = mig[2]()

print(pik)
