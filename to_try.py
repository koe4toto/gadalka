import psycopg2
import constants
import statistic_math

# Подключение к базе данных
conn = psycopg2.connect(
    database=constants.DATABASE_NAME,
    user=constants.DATABASE_USER,
    password=constants.DATABASE_PASSWORD,
    host=constants.DATABASE_HOST,
    port=constants.DATABASE_PORT)
cursor = conn.cursor()

data = 'edu_test'

def search_models(data):
    print('Старт!')
    # Пока есть строки с пустым значением kk, то выбрать первую
    t = 1
    while t >= 1:
        cursor.execute("SELECT * FROM math_models m1 WHERE NOT (m1.kk IS NOT NULL) LIMIT 1;")
        model = cursor.fetchall()
        t = len(model)
        print(model)
        # Рассчитать знаяение параметров указанной модели, запистаь в базу и вывести в консоли

        # Выбрать значения первой переменной
        cursor.execute("SELECT * FROM math_models m1 WHERE NOT (m1.kk IS NOT NULL) LIMIT 1;")
        X = cursor.fetchall()

        # Выбрать значения второй переменной
        cursor.execute("SELECT * FROM math_models m1 WHERE NOT (m1.kk IS NOT NULL) LIMIT 1;")
        Y = cursor.fetchall()

        # Рассчитать показатели
        slope, intercept, r_value, p_value, std_err = statistic_math.Pairs.linereg(X,Y)
        print(slope, intercept, r_value, p_value, std_err)

    print('Готово!')

search_models(data)





