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
from itertools import groupby


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
            if p >= 8 and p <= 20:
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
def measure_quantitative(measure):

    # Идентификатор предметной области
    data_asrea_id = measure[0][22]

    # Идентификатор измерения
    id = measure[0][0]

    # Список пар
    pairs = db_app.get_measure_models(id)

    # График распределеления
    # Объем выброки
    ui_limit = 500

    # Название таблицы с данными
    olap_name = measure[0][27]

    # Название колонки с данными
    column_name = measure[0][1]

    # Данные для графика распределения
    d = db_data.default_measure_freqs(id, olap_name)

    # Данные для графика комуляивного распределения
    k = db_data.default_measure_cumulative_freqs(id, olap_name)

    # Список ассоциированных параметров
    now_associations = db_app.select_associations(id)

    # Формирование графика распределения
    da = [[i[0], float(i[1]), "silver"] for i in d]
    ka = [[i[0], float(i[1]), "silver"] for i in k]
    data = json.dumps(da)
    data_ka = json.dumps(ka)

    return data_asrea_id, id, measure, data, pairs, now_associations, data_ka


# Карточка параметра времени
def measure_time(measure):

    # Идентификатор предметной области
    data_asrea_id = measure[0][22]

    # Идентификатор измерения
    id = measure[0][0]

    # Список пар
    pairs = db_app.get_measure_models(id)

    # Получение данных о мере
    # Объем выброки
    ui_limit = 500

    # Название таблицы с данными
    olap_name = measure[0][27]

    # Настройка для измерений времени
    data_column, measure2 = time_to_num(measure[0])

    # Данные для графика распределения
    d = db_data.time_distribution(data_column, olap_name, ui_limit)

    # Получение данных для графика распределения
    da = [i[0] for i in d]
    data = sm.Series(da).freq_line_view()
    return data_asrea_id, id, measure2, data, pairs


# Карточка параметра качественных данных
def measure_qualitative(measure):

    # Идентификатор предметной области
    data_asrea_id = measure[0][22]

    # Идентификатор измерения
    id = measure[0][0]

    return data_asrea_id, id


# Карточка измерения
@mod.route("/measure/<string:measure_id>/")
@is_logged_in
def measure(measure_id):
    # Получение данных о мере
    measure = db_app.select_measure(measure_id)
    statistics = db_app.default_measure_stats(measure_id, 2)

    if measure[0][4] == 1:
        data_asrea_id, id, measure, data, pairs, now_associations, data_ka = measure_quantitative(measure)
        return render_template(
            'measure_quantitative.html',
            data_asrea_id=data_asrea_id,
            id=id,
            measure=measure,
            data=data,
            pairs=pairs,
            now_associations=now_associations,
            statistics=statistics,
            data_ka=data_ka
        )
    elif measure[0][4] == 2 or measure[0][4] == 3:
        data_asrea_id, id = measure_qualitative(measure)
        return render_template(
            'measure_qualitative.html',
            data_asrea_id=data_asrea_id,
            id=id,
            measure=measure
        )
    elif measure[0][4] == 4 or measure[0][4] == 5 or measure[0][4] == 6:
        data_asrea_id, id, measure2, data, pairs = measure_time(measure)
        return render_template(
            'measure_time.html',
            data_asrea_id=data_asrea_id,
            id=id,
            measure=measure2,
            data=data,
            pairs=pairs
        )


# Добавление параметра
@mod.route("/data_area/<string:data_area_id>/add_measure_type_<string:type>", methods =['GET', 'POST'] )
@is_logged_in
def add_measure(data_area_id, type):

    data_area = db_app.data_area(data_area_id)

    # Список единиц измерений
    unit_list = db_app.unit_of_measurement_list()

    if type == '3':
        # Список справочников пользователя
        user_id = str(session['user_id'])
        result = db_app.user_ref_list(user_id)
        dif = [(str(i[0]), str(i[1])) for i in result]
        form = RefMeasureForm(request.form)
        form.ref.choices = dif
    elif type == '1':
        form = QualMeasureForm(request.form)
        unit = [(str(i[0]), str(i[1])) for i in unit_list]
        form.unit_of_measurement.choices = unit
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
                meg_id = db_app.insetr_measure_ref(column_name, description, data_area_id, type, status, ref)

                ref_name = db_app.ref_name(ref)

                # Сооздание колонки
                db_data.add_ref_column(data_area[0][5], column_name, constants.TYPE_OF_MEASURE[int(type)], ref_name)

            elif type == '1':
                uom = form.unit_of_measurement.data

                # Сохранение данных
                meg_id = db_app.insetr_measure_qualitative(column_name, description, data_area_id, type, status, uom)

                # Сооздание колонки
                db_data.add_column(data_area[0][5], column_name, constants.TYPE_OF_MEASURE[int(type)])
            else:
                # Сохранение данных
                meg_id = db_app.insetr_measure(column_name, description, data_area_id, type, status)

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
    data_area_name = result[23]

    # Имя таблицы хранения данных предметной области
    olap_name = result[27]

    # Тип измерения
    type = str(result[4])

    # Список единиц измерений
    unit_list = db_app.unit_of_measurement_list()

    # Форма заполняется данными из базы
    if type == '3':
        # Список справочников пользователя
        user_id = str(session['user_id'])
        ref_list = db_app.user_ref_list(user_id)
        dif = [(str(i[0]), str(i[1])) for i in ref_list]
        form = RefMeasureForm(request.form)
        form.ref.choices = dif
        form.ref.default = result[6]
    elif type == '1':
        form = QualMeasureForm(request.form)
        unit = [(str(i[0]), str(i[1])) for i in unit_list]
        form.unit_of_measurement.choices = unit
        form.unit_of_measurement.default = result[21]
    else:
        form = MeasureForm(request.form)


    form.description.default = result[2]
    form.column_name.default = result[1]
    form.process()


    if request.method == 'POST':
        form.process(request.form)
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

            elif type == '1':
                uom = str(request.form['unit_of_measurement'])

                # Обновление базе данных
                db_app.update_measure_quantitative(description, column_name, uom, measure_id)

            else:
                # Обновление базе данных
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


def dassosiations_group(measures):
    sorted_vehicles = sorted(measures, key=lambda x: x[2])
    fin = []

    # Получение списка поле
    for key, group in groupby(sorted_vehicles, lambda x: x[2]):
        choices = []
        for thing in group:
            choices.append((thing[0], thing[1]))
        item = [key, 'SelectMultipleField', thing[3], choices]
        fin.append(item)

    return fin


# Ассоциации параметра
@mod.route("/associations/<string:measure_id>", methods =['GET', 'POST'] )
@is_logged_in
def assosiations(measure_id):
    # Получение данных о мере
    measure = db_app.select_measure(measure_id)

    # Список измерений пользователя
    measures = db_app.select_measures_to_associations(measure_id, measure[0][21])

    fin = dassosiations_group(measures)

    # Форма отчищается от лишних полей
    atrr = AssosiationsForm.__dict__.keys()
    mix = [i for i in atrr]
    for i in mix:
        if mix.index(i) > 3:
            delattr(AssosiationsForm, i)

    # Добавление полей в форму
    for i in fin:
        atrname = str(i[0])
        setattr(AssosiationsForm, atrname, forrms[i[1]](i[2], choices=i[3]))

    # Форма
    form = AssosiationsForm(request.form)

    # Текущий набор ассоциаций
    now_associations = db_app.select_associations(measure_id)
    checked = dassosiations_group(now_associations)

    # Заполнение формы текущими значениями
    for i in checked:
        n = [m[0] for m in i[3]]
        getattr(form, i[0]).default = n
    form.process()

    # Обработка данных из формы
    if request.method == 'POST':
        # Получение данных из формы
        form.process(request.form)

        # Перечень идентификаторов ассоциированных параметров
        result = []
        for i in fin:
            me_ids = getattr(form, i[0]).data
            if len(me_ids) > 0:
                for ids in me_ids:
                    result.append(ids)



        # Сохранние данных об ассоциациях
        db_app.insert_associations(measure_id, result)

        # Запуск расчета сложных связей
        multiple_models_auto_calc()

        return redirect(url_for('measures.measure', measure_id=measure[0][0]))

    return render_template('associations.html', form=form, measure=measure)


# Параметры
@mod.route("/associations")
@is_logged_in
def associations_list():
    user = str(session['user_id'])
    return render_template(
        'associations_list.html',
        list = db_app.assosiations_list(user)
    )


