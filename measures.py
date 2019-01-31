from flask import Blueprint, render_template, flash, redirect, url_for, session, request
from decorators import is_logged_in
import constants
import tools
import json
import numpy as np
import statistic_math as sm
import database as db
import itertools
import datetime
from model_calculation import multiple_models_auto_calc

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


# Продготовка данных времени к отображению
def time_to_num(measure):
    # Формат предствления статистик
    format = {
        4: '%H:%M:%S',
        5: '%Y-%m-%d',
        6: '%Y-%m-%d %H:%M:%S'
    }

    # Тип измерения
    type = measure[4]

    # Типы времения
    time_types = [4, 5, 6]

    # Статистики измерения
    statistics = []

    if type in time_types:
        result = 'EXTRACT(EPOCH FROM {0} )'.format(measure[1])
        for p, i in enumerate(measure):
            if p >= 8:
                m = float(i)
                try:
                    statistics.append(datetime.datetime.utcfromtimestamp(m).strftime(format[type]))
                except:
                    statistics.append(m)
            else:
                statistics.append(i)
    else:
        result = measure[1]
        statistics = measure
    return result, statistics

# Карточка параметра количественных данных
@mod.route("/data_area/<string:data_asrea_id>/measure_quantitative/<string:id>/", methods =['GET', 'POST'])
@is_logged_in
def measure_quantitative(data_asrea_id, id):
    # Получение данных о мере
    cursor.execute('''SELECT * FROM measures WHERE id = '{0}';'''.format(id))
    measure = cursor.fetchall()

    # Получение данных о предметной области
    cursor.execute('''SELECT * FROM data_area WHERE id = '{0}';'''.format(data_asrea_id))
    data_area = cursor.fetchall()

    # Список пар
    cursor.execute(
        '''SELECT *
            FROM (
                SELECT
                    h.name, 
                    ml.r_value,
                    a1.description,
                    a2.description,
                    ml.area_description_1, 
                    ml.area_description_2,
                    ml.id, 
                    ml.hypothesis,
                    row_number() 
                    OVER (
                        PARTITION BY area_description_1::text || area_description_2::text 
                        ORDER BY abs(to_number(r_value, '9.999999999999')) DESC)  
                        AS rating_in_section
                FROM 
                    math_models ml
                INNER JOIN 
                    measures a1 on ml.area_description_1 = a1.id
                INNER JOIN 
                    measures a2 on ml.area_description_2 = a2.id
                INNER JOIN 
                    hypotheses h on ml.hypothesis = h.id
                WHERE 
                    r_value != 'None' AND (ml.area_description_1 = '{0}' or ml.area_description_2 = '{0}')
                ORDER BY 
                    rating_in_section
            ) counted_news
            WHERE rating_in_section <= 1
            ORDER BY abs(to_number(r_value, '9.999999999999')) DESC;
            
            '''.format(id))
    list = cursor.fetchall()

    # Получение данных о мере
    ui_limit = 500

    # Настройка для измерений времени
    data_column, measure2 = time_to_num(measure[0])

    data_cursor.execute(
        '''
        SELECT {0}
            FROM (
                SELECT 
                    row_number() over (order by {0}) as num,
                    count(*) over () as count,
                    {0}  
                FROM {1}
                WHERE {0} IS NOT NULL
                ) selected
        WHERE (case when count > {2} then num %(count/{2}) = 0 else 1 = 1 end);
        '''.format(data_column, data_area[0][5], ui_limit))
    d = data_cursor.fetchall()

    # Получение данных для графика распределения
    da = [i[0] for i in d]
    data = sm.Series(da).freq_line_view()
    return render_template(
        'measure_quantitative.html',
        data_asrea_id=data_asrea_id,
        id=id,
        the_measure=[measure2],
        data_area=data_area,
        data=data,
        pairs=list
    )

# Карточка параметра времени
@mod.route("/data_area/<string:data_asrea_id>/measure_time/<string:id>/", methods=['GET', 'POST'])
@is_logged_in
def measure_time(data_asrea_id, id):
    # Получение данных о мере
    cursor.execute('''SELECT * FROM measures WHERE id = '{0}';'''.format(id))
    measure = cursor.fetchall()

    # Получение данных о предметной области
    cursor.execute('''SELECT * FROM data_area WHERE id = '{0}';'''.format(data_asrea_id))
    data_area = cursor.fetchall()

    # Список пар
    cursor.execute(
        '''SELECT *
            FROM (
                SELECT
                    h.name, 
                    ml.r_value,
                    a1.description,
                    a2.description,
                    ml.area_description_1, 
                    ml.area_description_2,
                    ml.id, 
                    ml.hypothesis,
                    row_number() 
                    OVER (
                        PARTITION BY area_description_1::text || area_description_2::text 
                        ORDER BY abs(to_number(r_value, '9.999999999999')) DESC)  
                        AS rating_in_section
                FROM 
                    math_models ml
                INNER JOIN 
                    measures a1 on ml.area_description_1 = a1.id
                INNER JOIN 
                    measures a2 on ml.area_description_2 = a2.id
                INNER JOIN 
                    hypotheses h on ml.hypothesis = h.id
                WHERE 
                    r_value != 'None' AND (ml.area_description_1 = '{0}' or ml.area_description_2 = '{0}')
                ORDER BY 
                    rating_in_section
            ) counted_news
            WHERE rating_in_section <= 1
            ORDER BY abs(to_number(r_value, '9.999999999999')) DESC;

            '''.format(id))
    list = cursor.fetchall()

    # Получение данных о мере
    ui_limit = 500
    # Настройка для измерений времени
    data_column, measure2 = time_to_num(measure[0])

    data_cursor.execute(
        '''
        SELECT result
            FROM (
                SELECT 
                    row_number() over (order by {0}) as num,
                    count(*) over () as count,
                    {0} as result  
                FROM {1}
                WHERE {0} IS NOT NULL
                ) selected
        WHERE (case when count > {2} then num %(count/{2}) = 0 else 1 = 1 end);
        '''.format(data_column, data_area[0][5], ui_limit))
    d = data_cursor.fetchall()
    print('Пщщщщщщщщщщщщщ:', d)

    # Получение данных для графика распределения
    da = [i[0] for i in d]
    data = sm.Series(da).freq_line_view()
    return render_template(
        'measure_time.html',
        data_asrea_id=data_asrea_id,
        id=id,
        the_measure=[measure2],
        data_area=data_area,
        data=data,
        pairs=list
    )

# Карточка параметра качественных данных
@mod.route("/data_area/<string:data_asrea_id>/measure_qualitative/<string:id>/", methods=['GET', 'POST'])
@is_logged_in
def measure_qualitative(data_asrea_id, id):
    # Получение данных о мере
    cursor.execute('''SELECT * FROM measures WHERE id = '{0}';'''.format(id))
    measure = cursor.fetchall()

    # Получение данных о предметной области
    cursor.execute('''SELECT * FROM data_area WHERE id = '{0}';'''.format(data_asrea_id))
    data_area = cursor.fetchall()


    # Получение данных о мере
    # Настройка для измерений времени
    data_column, measure2 = time_to_num(measure[0])

    data_cursor.execute(
        '''
        SELECT {0} FROM {1} WHERE {0} IS NOT NULL;
        '''.format(data_column, data_area[0][5]))
    d = data_cursor.fetchall()

    # Получение данных для графика распределения
    da = [i[0] for i in d]
    data = [[int(i[0]), int(i[0]), 0] for i in da]
    json.dumps(data)
    return render_template(
        'measure_qualitative.html',
        data_asrea_id=data_asrea_id,
        id=id,
        the_measure=[measure2],
        data_area=data_area,
        data=data
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
                column_name = '{0}' AND data_area_id = '{1}';
            '''.format(
                column_name,
                data_area_id
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
                        VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}') RETURNING id;
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
                    meg_id = cursor.fetchall()

                except:
                    flash('Колонка с таким именем уже существует', 'success')
                    return redirect(url_for('data_areas.data_area', id=data_area_id))

                cursor.execute('''SELECT data FROM refs WHERE id = '{0}';'''.format(ref))
                ref_name = cursor.fetchall()[0][0]

                # Сооздание колонки
                data_cursor.execute(
                    '''
                    ALTER TABLE 
                    {0} 
                    ADD COLUMN 
                    {1} {2} {3}(code);
                    '''.format(
                        data_area[0][5],
                        column_name,
                        constants.TYPE_OF_MEASURE[int(type)],
                        ref_name
                    )
                )
                data_conn.commit()

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
                    VALUES ('{0}', '{1}', '{2}', '{3}', '{4}') RETURNING id;
                    '''.format(
                        column_name,
                        description,
                        data_area_id,
                        type,
                        status
                    )
                )
                conn.commit()
                meg_id = cursor.fetchall()

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

            cursor.execute(
                '''
                SELECT id 
                FROM measures 
                WHERE (type = '1' OR type = '4' OR type = '5' OR type = '6') 
                    AND id != '{0}' 
                    AND data_area_id = '{1}';
                '''.format(str(meg_id[0][0]), data_area_id)
            )
            megs_a = cursor.fetchall()
            megs = [i[0] for i in megs_a]

            types = ['1', '4', '5', '6']

            if type in types and len(megs) != 0:
                # Получить список идентификаторов гипотез
                cursor.execute("SELECT id FROM hypotheses;")
                hypotheses_id_a = cursor.fetchall()
                hypotheses_id = [i[0] for i in hypotheses_id_a]

                # Создать записи для каждой новой пары и каждой гипотезы)
                arrays = [hypotheses_id, megs, [meg_id[0][0]], [int(data_area_id)]]
                tup = list(itertools.product(*arrays))
                args_str = str(tup).strip('[]')

                # Записать данные
                cursor.execute("INSERT INTO math_models (hypothesis, area_description_1, area_description_2, data_area_id) VALUES " + args_str)
                conn.commit()

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

    # Тип измерения
    type = str(result[4])

    # Форма заполняется данными из базы
    if type == '3':
        # Список справочников пользователя
        cursor.execute("SELECT id, name FROM refs WHERE user_id = '{0}'".format(str(session['user_id'])))
        ref_list = cursor.fetchall()
        dif = [(str(i[0]), str(i[1])) for i in ref_list]
        form = RefMeasureForm(request.form)
        form.ref.choices = dif
        form.ref.default = result[6]
    else:
        form = MeasureForm(request.form)


    form.description.default = result[2]
    form.column_name.default = result[1]
    form.process()


    if request.method == 'POST':
        # Получение данных из формы
        description = request.form['description']
        column_name = request.form['column_name']

        # Проверка уникальности имени колонки
        cursor.execute(
            '''
            SELECT 
                * 
            FROM  
                measures
            WHERE
                column_name = '{0}' AND data_area_id = '{1}';
            '''.format(
                column_name,
                id
            )
        )
        check = cursor.fetchall()

        if column_name != result[1] and len(check) >= 1:
            flash('Колонка с таким именем уже существует. Придумайте, пожалуйста новое', 'danger')
            return redirect(request.url)
        else:
            if type == '3':
                refiii = str(request.form['ref'])
                # Обновление базе данных
                cursor.execute('UPDATE measures SET description=%s, column_name=%s, ref_id=%s WHERE id=%s;',
                               (description, column_name, refiii, measure_id))
                conn.commit()

                if column_name != result[1]:
                    # Переименование колонки
                    data_cursor.execute(
                        '''
                        ALTER TABLE {0} RENAME COLUMN {1} TO {2};
                        '''.format(
                            data_area[0][5],
                            result[1],
                            column_name
                        )
                    )
                    data_conn.commit()

                flash('Данные обновлены', 'success')
                return redirect(url_for('data_areas.data_area', id=id))
            else:
                # Обновление базе данных
                cursor.execute('UPDATE measures SET description=%s, column_name=%s WHERE id=%s;',
                               (description, column_name, measure_id))
                conn.commit()

                # Переименование колонки
                if column_name != result[1]:
                    data_cursor.execute(
                        '''
                        ALTER TABLE {0} RENAME COLUMN {1} TO {2};
                        '''.format(
                            data_area[0][5],
                            result[1],
                            column_name
                        )
                    )
                    data_conn.commit()

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

    # Удаление измерения и моделей
    cursor.execute(
        '''
        DELETE FROM measures WHERE id = '{0}';
        DELETE FROM math_models WHERE area_description_2 = '{0}' OR area_description_1 = '{0}'
        DELETE FROM complex_model_measures WHERE measure_id = '{0}'
        '''.format(id)
    )
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

    multiple_models_auto_calc()

    flash('Предметная область удалена', 'success')

    return redirect(url_for('data_areas.data_area', id=data_area_id))

