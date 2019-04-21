from flask import Blueprint, render_template, flash, redirect, url_for, session, request
from forms import *
from decorators import is_logged_in
import databases.db_app as db_app
import constants

mod = Blueprint('reports', __name__)

# Отчеты
@mod.route("/reports")
@is_logged_in
def reports():
    # Список единиц измерений
    reports_list = db_app.reports_list(session['user_id'])
    return render_template('reports.html', list=reports_list)

# Добавление простого отчёта
@mod.route("/add_simple_report", methods =['GET', 'POST'] )
@is_logged_in
def add_simple_report():

    user = str(session['user_id'])

    result = db_app.select_da(user)
    dif = [(str(i[0]), str(i[1])) for i in result]
    form = SimpleReport(request.form)
    form.data_area.choices = dif


    if request.method == 'POST' and form.validate():
        name = form.name.data
        description = form.description.data
        data_area = form.data_area.data
        type_of = '1'

        # Запись в базу данных
        report_id = db_app.create_simple_report(name, description, type_of, session['user_id'], data_area)

        flash('Новый отчет добавлен', 'success')
        return redirect(url_for('reports.report', id=report_id[0][0]))
    return render_template('add_report.html', form=form)

# Добавление отчёта из агрегатов
@mod.route("/add_aggregation_report", methods =['GET', 'POST'] )
@is_logged_in
def add_aggregation_report():
    form = АggregationReport(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        description = form.description.data
        type_of = '2'

        # Запись в базу данных
        report_id = db_app.create_aggregation_report(name, description, type_of, session['user_id'])

        flash('Новый отчет добавлен', 'success')
        return redirect(url_for('reports.report', id=report_id[0][0]))
    return render_template('add_report.html', form=form)

# Отчёт
@mod.route("/report/<string:id>", methods =['GET', 'POST'] )
@is_logged_in
def report(id):
    report = db_app.report(id)
    data_area_id = report[0][6]

    # Получение списка измерений предметной области
    measurement_report_list = db_app.select_measures_to_data_area(data_area_id)
    unit = [(str(i[0]), str(i[2])) for i in measurement_report_list]

    # Полуение списка солонок
    columns = db_app.select_measurement_report_list(id)
    if len(columns) == len(measurement_report_list):
        no_more_measures = True
    else:
        no_more_measures = False

    if report[0][3] == 1:
        return render_template(
            'simple_report.html',
            report=report,
            measurement_report_list= measurement_report_list,
            columns=columns,
            no_more_measures=no_more_measures
        )
    elif report[0][3] == 2:
        return render_template('aggregation_report.html', report=report)

# Редактирование отчета
@mod.route("/edit_report/<string:id>", methods =['GET', 'POST'] )
@is_logged_in
def edit_report(id):

    # Достаётся предметная область из базы по идентификатору
    report = db_app.report(id)[0]

    # Форма заполняется данными из базы
    form = EditReport(request.form)
    form.name.data = report[1]
    form.description.data = report[2]

    if request.method == 'POST':
        # Получение данных из формы
        form.name.data = request.form['name']
        form.description.data = request.form['description']

        # Если данные из формы валидные
        if form.validate():

            # Обновление базе данных
            db_app.update_report(id, form.name.data, form.description.data)

            flash('Данные обновлены', 'success')
            return redirect(url_for('reports.report', id=id))
    return render_template('edit_report.html', form=form, report_id=id, report_name=report[1])

# Удаление отчёта
@mod.route('/delete_report/<string:id>', methods=['POST'])
@is_logged_in
def delete_report(id):
    # TODO реализовать каскадное удаление колонок
    db_app.delete_report(id)
    flash('Отчёт удалён', 'success')
    return redirect(url_for('reports.reports'))

# Добавление колонки в отчет
@mod.route("/add_measurement_report/<string:report_id>/<string:measurement_report_id>", methods =['GET', 'POST'] )
@is_logged_in
def add_measurement_report(report_id, measurement_report_id):
    form = MeasurementReport(request.form)

    # Получение имени отчета
    report = db_app.report(report_id)[0]
    report_name = report[1]

    # Формирование списка измерений в отчете на данный момент
    n_me = [('1', 'Разместить в начале')]
    colors = [(i[0], i[1]) for i in constants.COLORS_IN_OREDERS]
    form.next_measure.choices = n_me
    form.style.choices = colors

    # Получение списка стилей

    if request.method == 'POST' and form.validate():
        measure_id = measurement_report_id
        next_measure = form.next_measure.data
        style = form.style.data

        # Запись в базу данных
        db_app.create_measurement_report(report_id, measure_id, next_measure, style)

        flash('Параметр добавлен', 'success')
        return redirect(url_for('reports.report', id=report[0]))
    return render_template('add_measurement_report.html', form=form, report_id=report_id, report_name=report_name)

# Редактирвание колонки в отчете
@mod.route("/edit_measurement_report/<string:measurement_report_id>", methods =['GET', 'POST'] )
@is_logged_in
def edit_measurement_report(measurement_report_id):

    # TODO реализовать
    report_id = None
    report_name = None
    return render_template('edit_measurement_report.html', form=form, report_id=report_id, report_name=report_name)

# Удаление колонки в отчете
@mod.route("/delete_measurement_report/<string:measurement_report_id>", methods =['GET', 'POST'] )
@is_logged_in
def delete_measurement_report(measurement_report_id):
    # TODO реализовать
    flash('Колонка удалена', 'success')
    return redirect(url_for('reports.report', id=measurement_report_id))


