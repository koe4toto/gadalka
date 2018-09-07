from flask import Blueprint, render_template, flash, redirect, url_for, session, request
from flask.json import JSONEncoder, JSONDecoder
import psycopg2
from decorators import is_logged_in
import constants
import foo
import json
import numpy as np

# Мои модули
from forms import *
#from app import conn, cursor
from statistic_math import Series

mod = Blueprint('measures', __name__)

# Подключение к базе данных
conn = psycopg2.connect(
    database=constants.DATABASE_NAME,
    user=constants.DATABASE_USER,
    password=constants.DATABASE_PASSWORD,
    host=constants.DATABASE_HOST,
    port=constants.DATABASE_PORT)
cursor = conn.cursor()

# Меры
@mod.route("/measures")
@is_logged_in
def measures():
    # Список справочников
    cursor.execute(
        '''SELECT * FROM area_description WHERE user_id=%s AND type=%s ORDER BY id DESC''',
        [str(session['user_id']), constants.AREA_DESCRIPTION_TYPE['Мера']])
    measures_list = cursor.fetchall()
    return render_template('measures.html', list = measures_list)

# Мера
@mod.route("/measure/<string:id>/<string:prob1>", methods =['GET', 'POST'])
@is_logged_in
def measure(id,prob1):
    # Получение данных о мере
    cursor.execute("SELECT * FROM area_description WHERE id = %s", [id])
    the_measure = cursor.fetchall()

    cursor.execute("SELECT * FROM data_area WHERE id = %s", [the_measure[0][4]])
    data_a = cursor.fetchall()
    conn.commit()

    database = data_a[0][4]
    database_user = data_a[0][5]
    database_password = data_a[0][6]
    database_host = data_a[0][7]
    database_port = data_a[0][8]
    database_table = data_a[0][9]

    probability = prob1.split('&')
    form1 = ProbabilityForm(request.form)
    form1.di_from.data = probability[0]
    form1.di_to.data = probability[1]
    form1.probability.data = probability[2]
    form1.exp_val.data = probability[3]

    form2 = MeFilterForm(request.form)
    form2.test1.data = probability[0]
    form2.test2.data = probability[1]

    # Данные
    try:
        conn2 = psycopg2.connect(
            database=database,
            user=database_user,
            password=database_password,
            host=database_host,
            port=database_port)
        cur = conn2.cursor()
        cur.execute('SELECT column_name FROM information_schema.columns WHERE table_name=%s;', [database_table])
        tc = cur.fetchall()

        if str(tc) == '[]':
            flash('Указаной таблицы нет в базе данных', 'danger')
        else:
            # Получение данных
            try:
                cur.execute('''SELECT ''' + the_measure[0][1] + ''' FROM ''' + database_table)
                measure_data = cur.fetchall()

                # Данные в список
                mline = [float(i[0]) for i in measure_data]

                # Получение экземпляра класса обработки данных
                to_print = Series(mline)

                # Получение частотного распределения для отображения в графике
                pre = to_print.freq_line_view(1000)
                stats = to_print.stats_line()

            except:
                pre = []
                stats = []
                flash(mline, 'danger')
    except:
        the_measure = None
        flash('Нет подключения', 'danger')

    return render_template('measure.html', id = id, the_measure = the_measure, sdata = pre, sd = stats, form1=form1, form2=form2, probability = probability)

# Пары
@mod.route("/pair_models")
def pair_models():
    # Список пар
    cursor.execute(
        '''select h.name, m1.kk, a1.description, a2.description, m1.area_description_1, m1.area_description_2 from math_models m1
            inner join hypotheses h on m1.hypothesis = h.id
            inner join area_description a1 on m1.area_description_1 = a1.id
            inner join area_description a2 on m1.area_description_2 = a2.id
            where hypothesis = '1';''')
    list = cursor.fetchall()
    return render_template('pair_models.html', list=list)

# Пара
@mod.route("/pair/<string:id1>/<string:id2>")
def pair(id1, id2):
    list = [id1, id2]
    pop = [["Age", "Weight"]]

    x = np.array(foo.numline(id1))
    y = np.array(foo.numline(id2))
    # Получение экземпляра класса обработки данных
    xy = np.vstack((x, y))
    for_graf = xy.transpose()

    for i in for_graf:
        pop.append([i[0], i[1]])

    popa = json.dumps(pop, ensure_ascii=False)
    str1 = ''.join(popa)



    return render_template('pair.html', list=list, for_graf=str1)


# Многомерная модель
@mod.route("/multiple_models")
def multiple_models():
    return render_template('multiple_models.html')