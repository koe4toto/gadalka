from flask import Blueprint, render_template, flash, redirect, url_for, session, request
import psycopg2
from decorators import is_logged_in
import constants
import itertools
import foo
import json
import numpy as np
import statistic_math as sm
import database as db

# Мои модули
from forms import *
from statistic_math import Series

mod = Blueprint('measures', __name__)

# работа с базой данных
db_measures = db.measures()
db_data_area = db.data_area()

conn = db.conn
cursor = db.cursor

data_conn = db.data_conn
data_cursor = db.data_cursor

# Параметры
@mod.route("/measures")
@is_logged_in
def measures():
    # Список справочников
    cursor.execute(
        '''SELECT * FROM measures WHERE status='6' ORDER BY id DESC''')
    measures_list = cursor.fetchall()
    return render_template('measures.html', list = measures_list)

# Карточка параметра
@mod.route("/data_area/<string:data_asrea_id>/measure/<string:id>/", methods =['GET', 'POST'])
@is_logged_in
def measure(data_asrea_id, id):
    # Получение данных о мере
    cursor.execute("SELECT * FROM measures WHERE id = %s", [id])
    the_measure = cursor.fetchall()

    cursor.execute("SELECT * FROM data_area WHERE id = %s", [data_asrea_id])
    data_a = cursor.fetchall()
    conn.commit()
    proba1 = '20&60&22&23'

    # Строка из URL разбивается на список
    probability = proba1.split('&')

    # Передача данных на страницу
    # Форма расчета фероятностив интервале
    form1 = IntervalForm(request.form)
    form1.di_from.data = probability[0]
    form1.di_to.data = probability[1]

    # Форма расчета доверительного интервала по значению вероятности
    form2 = ProbabilityForm(request.form)
    form2.probability.data = probability[2]

    # Форма фильтра
    form3 = MeFilterForm(request.form)
    form3.test1.data = probability[0]
    form3.test2.data = probability[1]

    return render_template('measure.html',
                           id = id,
                           the_measure = the_measure,
                           form1=form1,
                           form2=form2,
                           form3=form3,
                           probability = proba1,
                           data_area = data_a
                           )

# Добавление параметра
@mod.route("/data_area/<string:data_area_id>/add_measure_type_<string:type>", methods =['GET', 'POST'] )
@is_logged_in
def add_measure(data_area_id, type):

    data_area = db_data_area.data_area(data_area_id)

    if type == '3':
        # Список справочников пользователя
        cursor.execute("SELECT id, name FROM refs WHERE user_id = '{0}'".format(str(session['user_id'])))
        result = cursor.fetchall()
        dif = [(str(i[0]), str(i[1])) for i in result]
        form = RefMeasureForm(request.form)
        form.ref.choices = dif
    else:
        form = MeasureForm(request.form)


    if request.method == 'POST' and form.validate():
        column_name = form.column_name.data
        description = form.description.data

        status = '1'

        # Проверка уникальности имени колонки
        cursor.execute(
            '''
            SELECT 
                * 
            FROM  
                measures
            WHERE
                column_name = '{0}';
            '''.format(
                column_name
            )
        )
        check = cursor.fetchall()

        if len(check) >= 1:
            flash('Колонка с таким именем уже существует. Придумайте, пожалуйста новое', 'danger')
            return redirect(request.url)
        else:

            if type == '3':
                ref = form.ref.data

                # Сохранение данных
                try:
                    cursor.execute(
                        '''
                        INSERT INTO measures (
                            column_name, 
                            description, 
                            data_area_id, 
                            type, 
                            status,
                            ref_id) 
                        VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}');
                        '''.format(
                            column_name,
                            description,
                            data_area_id,
                            type,
                            status,
                            ref
                        )
                    )
                    conn.commit()
                except:
                    flash('Колонка с таким именем уже существует', 'success')
                    return redirect(url_for('data_areas.data_area', id=data_area_id))

            else:
                # Сохранение данных
                cursor.execute(
                    '''
                    INSERT INTO measures (
                        column_name, 
                        description, 
                        data_area_id, 
                        type, 
                        status) 
                    VALUES ('{0}', '{1}', '{2}', '{3}', '{4}');
                    '''.format(
                        column_name,
                        description,
                        data_area_id,
                        type,
                        status
                    )
                )
                conn.commit()

            # Сооздание колонки
            data_cursor.execute(
                '''
                ALTER TABLE 
                {0} 
                ADD COLUMN 
                {1} {2};
                '''.format(
                    data_area[0][5],
                    column_name,
                    constants.TYPE_OF_MEASURE[int(type)]
                )
            )
            data_conn.commit()


            flash('Параметр добавлен', 'success')
            return redirect(url_for('data_areas.data_area', id=data_area_id))
    return render_template('add_measure.html', form=form, data_area=data_area[0], title = db_measures.types[int(type)])

# Редактирование параметра
@mod.route("/data_area/<string:id>/edit_measure_<string:measure_id>", methods =['GET', 'POST'] )
@is_logged_in
def edit_measure(id, measure_id):

    data_area = db_data_area.data_area(id)

    # Достаётся предметная область из базы по идентификатору
    cursor.execute("SELECT * FROM measures WHERE id = %s", [measure_id])
    result = cursor.fetchone()

    # Форма заполняется данными из базы
    if result[4] == '3':
        # Список справочников пользователя
        cursor.execute("SELECT id, name FROM refs WHERE user_id = %s", [str(session['user_id'])])
        ref_list = cursor.fetchall()
        dif = [(str(i[0]), str(i[1])) for i in ref_list]
        form = RefMeasureForm(request.form)
        form.ref.choices = dif
        form.ref.defaul = result[6]
    else:
        form = MeasureForm(request.form)

    form.description.default = result[2]
    form.column_name.default = result[1]
    form.process()


    if request.method == 'POST':
        # Получение данных из формы
        form.description.data = request.form['description']
        form.column_name.data = request.form['column_name']

        if result[4] == '3':
            ref = request.form['ref']
        else:
            ref = None

        # Если данные из формы валидные
        if form.validate():

            # Обновление базе данных
            cursor.execute('UPDATE measures SET description=%s, column_name=%s, ref_id=%s WHERE id=%s;',
                           (form.description.data, form.column_name.data, ref, measure_id))
            conn.commit()

            flash('Данные обновлены', 'success')
            return redirect(url_for('data_areas.data_area', id=id))

    return render_template('edit_measure.html', form=form, data_area=data_area[0])


# Удаление измерения
@mod.route('/delete_data_measure/<string:id>?data_area_id=<string:data_area_id>', methods=['POST'])
@is_logged_in
def delete_data_measure(id, data_area_id):

    # Получение данных о мере
    cursor.execute("SELECT column_name FROM measures WHERE id = '{0}'".format(id))
    the_measure = cursor.fetchall()

    # Получение данных о мере
    cursor.execute("SELECT database_table FROM data_area WHERE id = '{0}'".format(data_area_id))
    data_area = cursor.fetchall()

    # Execute
    cursor.execute("DELETE FROM measures WHERE id = '{0}'".format(id))
    cursor.execute("DELETE FROM math_models WHERE area_description_2 = '{0}' OR area_description_1 = '{0}'".format(id))
    conn.commit()

    # Удаление колонки
    data_cursor.execute(
        '''
        ALTER TABLE {0} DROP COLUMN {1};
        '''.format(
            data_area[0][0],
            the_measure[0][0]
        )
    )
    data_conn.commit()

    flash('Предметная область удалена', 'success')

    return redirect(url_for('data_areas.data_area', id=data_area_id))

# Пары
@mod.route("/pair_models")
def pair_models():
    # Список пар
    cursor.execute(
        '''select 
            h.name, 
            m1.r_value, 
            a1.description, 
            a2.description, 
            m1.area_description_1, 
            m1.area_description_2, 
            m1.id 
            from math_models m1
            inner join hypotheses h on m1.hypothesis = h.id
            inner join area_description a1 on m1.area_description_1 = a1.id
            inner join area_description a2 on m1.area_description_2 = a2.id
            order by m1.r_value DESC;''')
    list = cursor.fetchall()
    return render_template('pair_models.html', list=list)

# Пара
@mod.route("/pair/<string:id1>/<string:id2>/<string:model_id>")
def pair(id1, id2, model_id):
    list = [id1, id2]
    pop = [[id1, id2, 'Модель']]

    # Получение данных о модели
    cursor.execute('''SELECT * FROM math_models WHERE id=%s;''', [model_id])
    model = cursor.fetchall()

    slope = float(model[0][2])
    intercept = float(model[0][3])

    # Получение данных для графика
    len = 100
    x = np.array(foo.numline(id1, len=len))
    y = np.array(foo.numline(id2, len=len))

    # Получение экземпляра класса обработки данных
    model_data = sm.Pairs(x, y)

    # Справочник гипотез
    hypotheses = {
        1: model_data.linereg_line,
        2: model_data.powerreg_line,
        3: model_data.exponentialreg1_line,
        4: model_data.hyperbolicreg1_line,
        5: model_data.hyperbolicreg2_line,
        6: model_data.hyperbolicreg3_line,
        7: model_data.logarithmic_line,
        8: model_data.exponentialreg2_line
    }

    # Получение данных для графика по модели
    Y = hypotheses[model[0][1]](slope, intercept)

    # Данные собираются в список для отображения
    xy = np.vstack((x, y, Y))
    for_graf = xy.transpose()

    for i in for_graf:
        pop.append([i[0], i[1], i[2]])

    popa = json.dumps(pop, ensure_ascii=False)


    return render_template('pair.html', list=list, for_graf=popa, model=model)


# Многомерная модель
@mod.route("/multiple_models")
def multiple_models():
    return render_template('multiple_models.html')