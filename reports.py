from flask import Blueprint, render_template, flash, redirect, url_for, session, request
from forms import *
from decorators import is_logged_in
import databases.db_app as db_app
import databases.db_data as db_data
import constants
import re

mod = Blueprint('reports', __name__)


# Отчеты
@mod.route("/reports")
@is_logged_in
def reports():
    # Список единиц измерений
    reports_list = db_app.reports_list(session['user_id'])
    return render_template('reports.html', list=reports_list)


# Добавление простого отчёта
@mod.route("/add_simple_report", methods=['GET', 'POST'])
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
@mod.route("/add_aggregation_report", methods=['GET', 'POST'])
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


# Расстановка колнок отчета по очереди
class order(object):
    def __init__(self, columns):
        self.columns = columns
        self.result_columns = []
        self.start()

    # Запуск поиск первого
    def search_first(self):
        for i in self.columns:
            if i[3] == 0:
                return i

    # Поиск следующего
    def search_next(self, prev):
        for i in self.columns:
            if i[3] == prev[0]:
                self.result_columns.append(i)
                self.start_next(i)

    # Запуск поиска следующего в очереди
    def start_next(self, last):
        if last != None:
            self.search_next(last)

    # Запуск выстраивния очереди
    def start(self):
        first = self.search_first()
        if first != None:
            self.result_columns.append(first)
            self.search_next(first)


# Функция распределитель
@mod.route("/aggregation_report")
@is_logged_in
def aggregation_report():
    id = request.args.get('id', default=1, type=int)
    report = db_app.report(id)
    return render_template('aggregation_report.html', report=report)



# Простой отчёт
@mod.route("/simple_report", methods=['GET', 'POST'])
@is_logged_in
def simple_report():
    # Идентификатор отчета
    id = request.args.get('id', default=1, type=int)

    # Текущая страница
    page = request.args.get('page', default=1, type=int)

    # Номер колонки по которой нужно сортировать
    order_by_column = request.args.get('order_by_column', default=0, type=int)

    # Направление сортировки
    desc = request.args.get('desc', default='True', type=str)

    # Количество элеменов списка на странице
    filter = request.args.get('filter', default=20, type=int)

    # Список доступных параметров для добавления в отчете
    choises = []

    # URL для фильтра
    preseto = ''

    # SQL для фильтра
    where = ''

    # Данные об отчете
    report = db_app.report(id)
    data_area_id = report[0][6]

    # Получение списка измерений предметной области
    measures_of_the_data_area = db_app.select_measures_of_the_data_area(data_area_id)

    # Полуение списка солонок
    columns = db_app.select_measurement_report_list(id)

    # Колонки выстраиваются по порядку
    if len(columns) > 0:
        columns_orders = order(columns).result_columns

        # Название таблицы, в которой хранятся данные
        data_area = db_app.data_area(data_area_id)
        database_table = data_area[0][5]

        # Колонки, из которых нужно данные забирать
        columns_string = ''
        left_join = ''
        columns_names = []
        for num, i in enumerate(columns_orders):
            sep = ''
            if num != 0:
                sep = ', '

            if i[6] == 3:
                left_join += ('LEFT JOIN ' + i[7] + ' ON ' + database_table + '.' + i[2] + ' = ' + i[7] + '.code ')
                columns_string += (sep + i[7] + '.value')
                columns_names.append((i[7] + '.value'))
            else:
                columns_string += (sep + database_table + '.' + i[2])
                columns_names.append((database_table + '.' + i[2]))

        styles = []
        for num, i in enumerate(columns_orders):
            n = i[5]
            styles.append(
                [num, 'right, {0}, {1}'.format(constants.COLORS_IN_OREDERS[n][2], constants.COLORS_IN_OREDERS[n][3])]
            )

        # Фильтр
        pres = [i for num, i in enumerate(request.args.items()) if num > 3]

        if len(pres) > 0:
            for i in pres:
                preseto += ('&' + str(i[0]) + '=' + str(i[1]))

            for num, i in enumerate(pres):
                if num == 0:
                    operator = 'WHERE '
                else:
                    operator = ' AND '

                # Определение мультиселекта
                if '[' in i[1]:
                    array = 'ANY(ARRAY'
                    skob = ')'
                else:
                    array = ''
                    skob = ''

                # Определение знака
                if re.match(r'from_value_', str(i[0])) != None:
                    symbol = '>'
                    column = re.sub(r'from_value_', '', str(i[0]))
                elif re.match(r'to_value_', str(i[0])) != None:
                    symbol = '<'
                    column = re.sub(r'to_value_', '', str(i[0]))
                else:
                    symbol = '='
                    column = str(i[0])

                # Строка
                where += operator + column + symbol + array + str(i[1]) + skob

        # Подучение данных
        if desc == 'True':
            order_by = columns_names[order_by_column] + ' DESC'
        else:
            order_by = columns_names[order_by_column]

        limit = filter
        if int(page) == 1:
            offset = 0
        else:
            offset = (int(page) - 1) * limit
        # Подучение данных из базы
        data_to_simple_report = db_data.select_columns_to_simple_report(columns_string, database_table, limit, offset,
                                                                        order_by, left_join, where)

        # Подучение общего количества записей
        count_data = db_data.select_data_count(columns_string, database_table, left_join, where)[0][0]

        # Формирование переключателя
        pages = (count_data // limit)
        if count_data % limit > 0:
            pages += 1
    else:
        columns_orders = []
        data_to_simple_report = []
        pages = 0
        count_data = 0
        styles = ''

    # Формирование списка доступных измерений
    names_in_columns = [i[2] for i in columns_orders]
    for i in measures_of_the_data_area:
        if i[1] not in names_in_columns:
            choises.append(i)



    return render_template(
        'simple_report.html',
        report=report,
        choises=choises,
        columns=columns_orders,
        data_to_simple_report=data_to_simple_report,
        pages=pages,
        current_page=page,
        count_data=count_data,
        styles=styles,
        order_by_column=order_by_column,
        desc=desc,
        filter=filter,
        preset=preseto,
        where=where
    )


# Редактирование отчета
@mod.route("/edit_report/<string:id>", methods=['GET', 'POST'])
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
@mod.route('/delete_report/<string:id>', methods=['GET'])
@is_logged_in
def delete_report(id):
    db_app.delete_report(id)
    flash('Отчёт удалён', 'success')
    return redirect(url_for('reports.reports'))


# Добавление колонки в отчет
@mod.route("/add_measurement_report/<string:report_id>/<string:measurement_report_id>", methods=['GET', 'POST'])
@is_logged_in
def add_measurement_report(report_id, measurement_report_id):
    # Получение имени отчета
    report = db_app.report(report_id)[0]
    report_name = report[1]

    # Получение сведений о параметре
    measure_of_data_area = db_app.select_measure(measurement_report_id)
    type_of_measure = measure_of_data_area[0][4]
    name_of_measure = measure_of_data_area[0][2]

    # Стили колонок
    colors = [(i[0], i[1]) for i in constants.COLORS_IN_OREDERS]

    # Если поле стиля есть в форме, то оно удаляется
    if hasattr(MeasurementReport, 'style') == True:
        # Форма отчищается от лишних полей
        delattr(MeasurementReport, 'style')

    # Если параметр количественный, то добавляется селект для выбора стилей
    if type_of_measure == 1:
        # Добавление полей в форму
        setattr(MeasurementReport, 'style', forrms['SelectField']('Стиль', choices=colors))

    # Форма
    form = MeasurementReport(request.form)

    # Если параметр количественный, то полю стилей присваиваются варианты
    if type_of_measure == 1:
        form.style.choices = colors

    # Полуение списка солонок
    columns = db_app.select_measurement_report_list(report_id)
    # Колонки выстраиваются по порядку
    if len(columns) > 1:
        orders = order(columns)
        columns_orders = orders.result_columns
    else:
        columns_orders = columns
    cols = [[str(i[0]), i[1]] for i in columns_orders]

    # Формирование списка измерений в отчете на данный момент
    n_me = [('0', 'Разместить в начале')]
    for i in cols:
        n_me.append(i)
    form.next_measure.choices = n_me

    # Обработка полученных данных формы
    if request.method == 'POST' and form.validate():
        measure_id = measurement_report_id
        next_measure = form.next_measure.data

        # Если параметр количественный, то полью стиля присваиваются значения
        if type_of_measure == 1:
            style = form.style.data
        else:
            style = 0

        # Запись в базу данных
        db_app.create_measurement_report(report_id, measure_id, next_measure, style)

        flash('Параметр добавлен', 'success')
        return redirect(url_for('reports.report', id=report[0], page=1))

    return render_template(
        'add_measurement_report.html',
        form=form, report_id=report_id,
        report_name=report_name,
        name_of_measure=name_of_measure
    )


# Редактирвание колонки в отчете
@mod.route("/edit_measurement_report/<string:measurement_report_id>", methods=['GET', 'POST'])
@is_logged_in
def edit_measurement_report(measurement_report_id):
    # TODO реализовать
    report_id = None
    report_name = None
    return render_template('edit_measurement_report.html', form=form, report_id=report_id, report_name=report_name)


# Удаление колонки в отчете
@mod.route("/delete_measurement_report/<string:measurement_report_id>/<string:report_id>", methods=['GET', 'POST'])
@is_logged_in
def delete_measurement_report(measurement_report_id, report_id):

    db_app.delete_report_column(measurement_report_id)
    flash('Колонка удалена', 'success')
    return redirect(url_for('reports.report', id=report_id, page=1))


# Перенаправление на отображение отчета
@mod.route("/report")
@is_logged_in
def report():
    id = request.args.get('id', type=int)

    # Текущая страница
    page = request.args.get('page', default=1, type=int)

    # Номер колонки по которой нужно сортировать
    order_by_column = request.args.get('order_by_column', default=0, type=int)

    # Направление сортировки
    desc = request.args.get('desc', default='True', type=str)

    report = db_app.report(id)
    if report[0][3] == 1:
        return redirect(url_for('reports.simple_report', id=id, page=page, order_by_column=order_by_column, desc=desc))
    if report[0][3] == 2:
        return redirect(url_for('reports.aggregation_report', id=id, page=page, order_by_column=order_by_column, desc=desc))

# Форма фильтра
@mod.route("/simple_report_filter", methods=['GET', 'POST'])
@is_logged_in
def simple_form_filter():
    # Идентификатор отчета
    id = request.args.get('id', type=int)

    # Описание отчета
    report = db_app.report(id)
    data_area_id = report[0][6]

    # Получение списка параметров предметной области
    measure = db_app.select_measures_of_the_data_area(data_area_id)

    # Форма отчищается от лишних полей
    atrr = FilterReportForm.__dict__.keys()
    mix = [i for i in atrr]
    for i in mix:
        if mix.index(i) > 3:
            delattr(FilterReportForm, i)

    # Добавление полей в форму
    for i in measure:
        atrname = str(i[1])
        if i[5] in [1, 4, 5, 6]:
            setattr(FilterReportForm, ('from_value_' + atrname), forrms['IntegerField']((i[2] + " от:")))
            setattr(FilterReportForm, ('to_value_' + atrname), forrms['IntegerField']((i[2] + " до:")))
        elif i[5] == 2:
            setattr(FilterReportForm, atrname, forrms['StringField'](i[2]))
        elif i[5] == 3:
            ref_data = db_data.ref_data(i[6])
            choices = [(i[0], i[1]) for i in ref_data]
            setattr(FilterReportForm, atrname, forrms['SelectMultipleField'](i[2], choices=choices))

    # Форма
    form = FilterReportForm(request.form)


    # Заполнение формы текущими значениями
    '''
    for i in checked:
        n = [m[0] for m in i[3]]
        getattr(form, i[0]).default = n 
    '''
    form.process()

    # Обработка данных из формы
    if request.method == 'POST' and form.validate():
        # Получение данных из формы
        form.process(request.form)
        params = form.data

        part_of_url = ''
        for i in params:
            if params[i] not in [None, []]:
                part_of_url += ('&' + str(i)+ '=' + str(params[i]))

        return redirect(url_for('reports.simple_report', id=id, page=1, order_by_column=0, desc='False') + part_of_url)

    return render_template('simple_report_filter.html', form=form, report=report, measure=measure)