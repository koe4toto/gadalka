from flask import Blueprint, render_template, flash, redirect, url_for, session, request
from decorators import is_logged_in
import json
import statistic_math as sm
import itertools
import datetime
from model_calculation import multiple_models_auto_calc
import constants
from forms import *
import databases.db_app as db_app
import databases.db_data as db_data

mod = Blueprint('measures', __name__)


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

    data_area = db_app.data_area(data_area_id)

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
                meg_id = db_app.insetr_measure_ref(column_name, description, data_area_id, type, status)

                # Сооздание колонки
                db_data.add_column(data_area[0][5], column_name, constants.TYPE_OF_MEASURE[int(type)])

            # Измерения для форимрования пар с новым параметром
            megs_a = db_app.select_measures_for_models(str(meg_id[0][0]), data_area_id)
            megs = [i[0] for i in megs_a]

            types = ['1', '4', '5', '6']

            if type in types and len(megs) != 0:
                # Получить список идентификаторов гипотез
                hypotheses_id_a = db_app.select_id_from_hypotheses()
                hypotheses_id = [i[0] for i in hypotheses_id_a]

                # Создать записи для каждой новой пары и каждой гипотезы)
                arrays = [hypotheses_id, megs, [meg_id[0][0]], [int(data_area_id)]]
                tup = list(itertools.product(*arrays))
                args_str = str(tup).strip('[]')

                # Записать данные
                db_app.insert_math_models(args_str)

            flash('Параметр добавлен', 'success')
            return redirect(url_for('data_areas.data_area', id=data_area_id))
    return render_template('add_measure.html', form=form, data_area=data_area[0], title = db_app.types[int(type)])

# Редактирование параметра
@mod.route("/data_area/<string:data_area_id>/edit_measure_<string:measure_id>", methods =['GET', 'POST'] )
@is_logged_in
def edit_measure(data_area_id, measure_id):

    # Достаётся предметная область из базы по идентификатору
    result = db_app.select_measure(measure_id)[0]

    # Имя предметной области для хлебной крошки
    data_area_name = result[22]

    # Имя таблицы хранения данных предметной области
    olap_name = result[26]

    # Тип измерения
    type = str(result[4])

    # Форма заполняется данными из базы
    if type == '3':
        # Список справочников пользователя
        user_id = str(session['user_id'])
        ref_list = db_app.user_ref_list(user_id)
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
        check = db_app.measures_for_check(column_name, data_area_id)

        if column_name != result[1] and len(check) >= 1:
            flash('Колонка с таким именем уже существует. Придумайте, пожалуйста новое', 'danger')
            return redirect(request.url)
        else:
            if type == '3':
                refiii = str(request.form['ref'])
                # Обновление базе данных
                db_app.update_measure_with_ref(description, column_name, refiii, measure_id)

                if column_name != result[1]:
                    # Переименование колонки
                    db_data.update_column(olap_name, result[1], column_name)

                flash('Данные обновлены', 'success')
                return redirect(url_for('data_areas.data_area', id=data_area_id))
            else:
                # Обновление базе данных
                print(description, column_name, measure_id)
                db_app.update_measure(description, column_name, measure_id)

                # Переименование колонки
                if column_name != result[1]:
                    db_data.update_column(olap_name, result[1], column_name)

                flash('Данные обновлены', 'success')
                return redirect(url_for('data_areas.data_area', id=data_area_id))

    return render_template('edit_measure.html', form=form, data_area_id=data_area_id, data_area_name=data_area_name)

# Удаление параметра
@mod.route('/delete_data_measure/<string:measure_id>?data_area_id=<string:data_area_id>?olap_name=<string:olap_name>?column_name=<string:column_name>', methods=['POST'])
@is_logged_in
def delete_data_measure(measure_id, data_area_id, olap_name, column_name):

    # Удаление измерения и моделей
    db_app.delete_measure(measure_id)

    # Удаление колонки
    db_data.delete_column(olap_name, column_name)

    # Запуск расчета сложных связей
    multiple_models_auto_calc()

    flash('Предметная область удалена', 'success')

    return redirect(url_for('data_areas.data_area', id=data_area_id))

