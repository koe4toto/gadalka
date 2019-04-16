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

# Добавление простого отчёта
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
    if report[0][3] == 1:
        return render_template('simple_report.html', report=report)
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
    db_app.delete_report(id)
    flash('Отчёт удалён', 'success')
    return redirect(url_for('reports.reports'))