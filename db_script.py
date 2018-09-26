import psycopg2
import random
import itertools
import datetime

database = 'test111'
username = 'postgres'
password = 'gbcmrf'
host = 'localhost'
port = '5432'
table = 'edu_test'

# Указываем название файла базы данных


try:
    conn = psycopg2.connect(database=database, user=username, password=password, host=host, port=port)
    cursor = conn.cursor()
    #cursor.execute('''INSERT INTO edu_test (institution) VALUES ('12324');''')
    #cursor.execute('''SELECT * FROM edu_test;''')
    #proba = cursor.fetchall()
    #print(proba)
    conn.commit()

except:
    print('Нет подключения')


# Создаем таблицу для хранения данных
#cursor.execute('''CREATE SEQUENCE auto_id_statdata; ''')
#cursor.execute('''CREATE TABLE statdata ("id" integer NOT NULL DEFAULT nextval('auto_id_statdata'), "statisticdata" real);''')
#conn.commit()

# Тестовая таблица
"""
cursor.execute('''CREATE TABLE edu_test (
"institution" real,
"groups" real,
"job" real,
"pupil" real,
"date" date,
"level" int,
"region" int,
"age" int
);''')
"""

# Полезно для определения всех возможных связей в предметной области
data = list(itertools.combinations('WXYZ', 2))
#print(data)

# Использую для генерации данных в базу
level = [i for i in range(1, 5)]
region = [i for i in range(1, 19)]
age = [i for i in range(6,19)]


# Список из списков
arrays = [level, region, [1]]


# Генерирует кортэж из свех возможных уникальных комбинаций четырёх справочников выше
cp = list(itertools.product(*arrays))
#print(cp)
args_str = str(cp).strip('[]')
#print(args_str)

# Генератор тестовых данных
def generator():
    for n in cp:
        i = 0
        while i < 100:
            try:
                i += 1
                date1 = datetime.datetime(2013, 1, 1, 18, 56, 19, 612451)
                newdate = date1 + datetime.timedelta(days=i)
                institution = float(round(100*random.random()))
                group = float(round(institution*12 - 7*random.random()))
                job = float(round(323/(group-2*random.random()) + 2*random.random()))
                pupil = float(round(group*group - 500*random.random()))
                insert = [institution, group, job, pupil, '{:%Y.%m.%d}'.format(newdate), n[0], n[1], n[2]]
                cursor.execute('INSERT INTO edu_test (institution, groups, job, pupil, date, level, region, age) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);',(insert[0], insert[1], insert[2], insert[3], insert[4], insert[5], insert[6], insert[7]))
            except ZeroDivisionError:
                job = 4
                continue
    print('Готово!')

# Запуск генератора
generator()


#cursor.execute('INSERT INTO statdata (statisticdata) VALUES (2);')
#conn.commit()
"""
# Пользователи
cursor.execute('''CREATE SEQUENCE auto_id_users; ''')
cursor.execute('''CREATE TABLE users ("id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_users'), "name" varchar(100), "email" varchar(100), "username" varchar(30), "password" varchar, "register_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')

# Предметные области
cursor.execute('''CREATE SEQUENCE auto_id_data_area;''')
cursor.execute('''CREATE TABLE data_area ("id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_data_area'), "name" varchar(100), "description" varchar(600), "user_id" varchar(30), "database" varchar, "database_user" varchar, "database_password" varchar, "database_host" varchar, "database_port" varchar, "database_table" varchar, "register_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')

# Справочники
cursor.execute('''CREATE SEQUENCE auto_id_refs;''')
cursor.execute('''CREATE TABLE refs ("id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_refs'), "name" varchar(100), "description" varchar(600), "user_id" varchar(30), "data" varchar, "register_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP);''')

# Описание содержание предметной области
cursor.execute('''CREATE SEQUENCE auto_id_area_description;''')
cursor.execute('''CREATE TABLE area_description ("id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_area_description'), "column_name" varchar(300), "description" varchar(300), "user_id" varchar(30), "data_area_id" varchar(30), "type" int, "kind_of_metering" int, "ref_id" int);''')

# Справочник гипотез моделей (заполняется разработчиком)
cursor.execute('''CREATE TABLE hypotheses ("id" integer PRIMARY KEY NOT NULL, "name" varchar(300), "description" varchar(300));''')

# Модели
cursor.execute('''CREATE SEQUENCE auto_id_math_models;''')
cursor.execute('''
CREATE TABLE math_models 
("id" integer PRIMARY KEY NOT NULL DEFAULT nextval('auto_id_refs'), 
"hypothesis" integer, 
"slope" varchar(300), 
"intercept" varchar(300), 
"r_value" varchar(300), 
"p_value" varchar(300), 
"std_err" varchar(300),
"area_description_1" integer, 
"area_description_2" integer);
''')
"""


# Удаление табицы, если требуется
#cursor.execute('DROP TABLE test_data')

#cursor.execute('''CREATE TABLE test_data ("x" real, "line_1" real, "line_2" real);''')

#cursor.execute('select * from test_data')
#pik = cursor.fetchall()
#print(pik)

conn.commit()
cursor.close()
conn.close()








