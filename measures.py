from flask import Blueprint, render_template, flash, redirect, url_for, session, request
import psycopg2
from decorators import is_logged_in
import constants

# Мои модули
from foo import tryit, allowed_file, looking, sqllist, sqlvar
from forms import *
from app import conn, cursor
from statistic_math import Series

mod = Blueprint('measures', __name__)


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
@mod.route("/measure/<string:id>/")
@is_logged_in
def measure(id):
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

    return render_template('measure.html', id = id, the_measure = the_measure, sdata = pre, sd = stats)