from flask import Blueprint, render_template, flash, redirect, url_for, session, request
from decorators import is_logged_in
import json
import statistic_math as sm
import database as db
import itertools
import datetime
from model_calculation import multiple_models_auto_calc
import constants
from forms import *
import databases.db_app as db_app
import databases.db_data as db_data

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
    user = str(session['user_id'])
    return render_template(
        'measures.html',
        list = db_app.select_measures(user)
    )

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
            if p >= 8 and p <= 21:
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
    measure = db_app.select_measure(id)

    # Список пар
    pairs = db_app.get_measure_models(id)

    # График распределеления
    # Объем выброки
    ui_limit = 500

    # Название таблицы с данными
    olap_name = measure[0][26]

    # Название колонки с данными
    column_name = measure[0][1]

    # Данные для графика распределения
    d = db_data.distribution(column_name, olap_name, ui_limit)

    # Формирование графика распределения
    da = [i[0] for i in d]
    data = sm.Series(da).freq_line_view()
    return render_template(
        'measure_quantitative.html',
        data_asrea_id=data_asrea_id,
        id=id,
        measure=measure,
        data=data,
        pairs=pairs
    )

# Карточка параметра времени
@mod.route("/data_area/<string:data_asrea_id>/measure_time/<string:id>/", methods=['GET', 'POST'])
@is_logged_in
def measure_time(data_asrea_id, id):
    # Получение данных о мере
    measure = db_app.select_measure(id)

    # Список пар
    pairs = db_app.get_measure_models(id)

    # Получение данных о мере
    ui_limit = 500

    # Название таблицы с данными
    olap_name = measure[0][26]

    # Настройка для измерений времени
    data_column, measure2 = time_to_num(measure[0])

    # Данные для графика распределения
    d = db_data.time_distribution(data_column, olap_name, ui_limit)

    # Получение данных для графика распределения
    da = [i[0] for i in d]
    data = sm.Series(da).freq_line_view()
    return render_template(
        'measure_time.html',
        data_asrea_id=data_asrea_id,
        id=id,
        measure=measure2,
        data=data,
        pairs=pairs
    )

# Карточка параметра качественных данных
@mod.route("/data_area/<string:data_asrea_id>/measure_qualitative/<string:id>/", methods=['GET', 'POST'])
@is_logged_in
def measure_qualitative(data_asrea_id, id):
    # Получение данных о мере
    measure = db_app.select_measure(id)
    return render_template(
        'measure_qualitative.html',
        data_asrea_id=data_asrea_id,
        id=id,
        the_measure=measure
    )

# Добавление параметра
@mod.route("/data_area/<string:data_area_id>/add_measure_type_<string:type>", methods =['GET', 'POST'] )
@is_logged_in
def add_measure(data_area_id, type):

    data_area = db_data_area.data_area(data_area_id)

    if type == '3':
        # Список справочников пользователя
        user_id = str(session['user_id'])
        result = db_app.user_ref_list(user_id)
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
        check = db_app.measures_for_check(column_name, data_area_id)

        if len(check) >= 1:
            flash('Колонка с таким именем уже существует. Придумайте, пожалуйста новое', 'danger')
            return redirect(request.url)
        else:

            if type == '3':
                ref = form.ref.data

                # Сохранение данных
                try:
                    meg_id = db_app.insetr_measure(column_name, description, data_area_id, type, status, ref)

                except:
                    flash('Колонка с таким именем уже существует', 'success')
                    return redirect(url_for('data_areas.data_area', id=data_area_id))

                ref_name = db_app.ref_name(ref)

                # Сооздание колонки
                db_data.add_ref_column(data_area[0][5], column_name, constants.TYPE_OF_MEASURE[int(type)], ref_name)

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

# Удаление параметра
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
        DELETE FROM math_models WHERE area_description_2 = '{0}' OR area_description_1 = '{0}';
        DELETE FROM complex_model_measures WHERE measure_id = '{0}';
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

    # Запуск расчета сложных связей
    multiple_models_auto_calc()

    flash('Предметная область удалена', 'success')

    return redirect(url_for('data_areas.data_area', id=data_area_id))

