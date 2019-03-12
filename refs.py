from flask import Blueprint, render_template, flash, redirect, url_for, session, request
import psycopg2
import xlrd
import os
from decorators import is_logged_in
from datetime import datetime
from tools import allowed_file, looking, sqllist, sqlvar
from forms import *
import constants
import databases.db_app as db_app
import databases.db_data as db_data

mod = Blueprint('refs', __name__)

# Справочники
@mod.route("/refs")
@is_logged_in
def refs():
    # Список справочников
    ref_list = db_app.ref_list()
    return render_template('refs.html', list = ref_list)

# Справочник
@mod.route("/ref/<string:id>/")
@is_logged_in
def ref(id):
    # Подключение к базе данных
    the_ref = db_app.ref_data(id)

    # Имя справочника
    ref_name = the_ref[0][4]

    # Содержание справочника
    columns = db_data.ref_data(ref_name)

    return render_template('ref.html', id = id, ref = the_ref, columns=columns)

# Добавление справочника
@mod.route("/add_ref", methods =['GET', 'POST'] )
@is_logged_in
def add_ref():
    form = RefForm(request.form)

    if request.method == 'POST' and form.validate():
        user = str(session['user_id'])
        name = form.name.data
        description = form.description.data

        # Проверка наличия файла
        if 'file' not in request.files:
            flash('Вы не указали файл для загрузки', 'danger')
            return redirect(request.url)

        file = request.files['file']


        if file and allowed_file(file.filename):
            # Генерируется имя из идентификатора пользователя и врамени загрузки файла
            # Текущее время в сточку только цифрами
            now = ''.join(c for c in str(datetime.now()) if c not in '- :.')
            filename = 'ref_' + str(session['user_id']) + '_' + now + '.xlsx'
            # Загружается файл
            file.save(os.path.join(constants.UPLOAD_FOLDER, filename))

            # Создаётся запись в базе данных
            # Генерируется имя для таблицы с данными
            table_name = str('ref' + str(session['user_id']) + now)

            try:
                # Создаётся запись в таблице с базой данных
                db_app.insert_ref(name, description, user, table_name)

                # Создаёется таблица для хранения данных
                db_data.create_ref_table(table_name)
            except psycopg2.Error as e:
                flash(e.diag.message_primary, 'danger')
                return redirect(request.url)

            # Открывается сохраненный файл
            rb = xlrd.open_workbook(os.path.abspath('.') + '/uploaded_files/' + filename)
            sheet = rb.sheet_by_index(0)

            # Запсиь строчек справочника в базу данных
            in_table = range(sheet.nrows)
            try:
                for rownum in in_table:
                    if rownum >= 1:
                        row = sheet.row_values(rownum)

                        # Запсиь строчек справочника в базу данных
                        db_data.insert_data_in_ref(table_name, row[0], row[1], row[2])
            except:
                flash('Неверный формат данных в файле', 'danger')
                return redirect(url_for('add_ref'))

            # Удаление загруженного файла
            os.remove(os.path.join(constants.UPLOAD_FOLDER, filename))

            flash('Справочник добавлен', 'success')
            return redirect(url_for('refs.refs'))
        else:
            flash('Неверный формат файла. Справочник должен быть в формате .xlsx', 'danger')

    return render_template('add_ref.html', form=form)

# Удаление справочника
@mod.route('/delete_ref/<string:id>', methods=['POST'])
@is_logged_in
def delete_ref(id):

    # Удаление записи о справочнике
    ref_name = db_app.delete_ref(id)

    # Удаление таблицы с данными
    db_data.delete_table(ref_name)

    flash('Справочник удалён', 'success')

    return redirect(url_for('refs.refs'))

# Редактироваение справочника
@mod.route("/edit_ref/<string:id>", methods =['GET', 'POST'] )
@is_logged_in
def edit_ref(id):
    # Данные о справочнике
    result = db_app.ref_data(id)

    # Форма заполняется данными из базы
    form = RefForm(request.form)
    form.name.data = result[0][1]
    form.description.data = result[0][2]

    if request.method == 'POST':
        # Получение данных из формы
        form.name.data = request.form['name']
        form.description.data = request.form['description']

        # Если данные из формы валидные
        if form.validate():

            # Обновление базе данных
            db_app.update_ref(form.name.data, form.description.data, id)

            flash('Данные обновлены', 'success')
            return redirect(url_for('refs.ref', id=id))

    return render_template('edit_ref.html', form=form)

# Обновление данных справочника из файла
@mod.route("/update_ref/<string:id>", methods =['GET', 'POST'] )
@is_logged_in
def update_ref(id):
    # Данные о справочнике
    result = db_app.ref_data(id)

    if request.method == 'POST':

        # Проверка наличия файла
        if 'file' not in request.files:
            flash('Вы не указали файл для загрузки', 'danger')
            return redirect(request.url)

        file = request.files['file']

        if file and allowed_file(file.filename):
            # Генерируется имя из идентификатора пользователя и врамени загрузки файла
            # Текущее время в сточку только цифрами
            filename = result[0][4] + '.xlsx'
            # Загружается файл
            file.save(os.path.join(constants.UPLOAD_FOLDER, filename))

            # Имя обновляемой таблицы
            table_name = result[0][4]

            # Отчистка таблицы
            db_data.delete_from_table(table_name)

            # Открывается сохраненный файл
            rb = xlrd.open_workbook(constants.UPLOAD_FOLDER + filename)
            sheet = rb.sheet_by_index(0)

            # Запсиь строчек справочника в базу данных
            in_table = range(sheet.nrows)
            try:
                for rownum in in_table:
                    if rownum >= 1:
                        row = sheet.row_values(rownum)
                        # Запсиь строчек справочника в базу данных
                        db_data.insert_data_in_ref(table_name, row[0], row[1], row[2])
            except:
                flash('Неверный формат данных в файле', 'danger')
                return redirect(url_for('update_ref'))

            # Удаление загруженного файла
            os.remove(constants.UPLOAD_FOLDER + filename)

            flash('Данные обновлены', 'success')
            return redirect(url_for('refs.ref', id=id))
        else:
            flash('Неверный формат файла. Справочник должен быть в формате .xlsx', 'danger')


    return render_template('update_ref.html', form=form)


# Справочник единиц измерений
@mod.route("/units_of_measurement/")
@is_logged_in
def units_of_measurement():
    # Список единиц измерений
    ref_list = db_app.unit_of_measurement_list()
    return render_template('units_of_measurement.html', list = ref_list)

# Справочник единиц измерений
@mod.route("/unit_of_measurement/<string:id>")
@is_logged_in
def unit_of_measurement(id):
    # Единица измерения
    unit_of_measurement_item = db_app.unit_of_measurement_item(id)
    user = str(session['user_id'])

    measures = db_app.select_measures_by_unit(unit_of_measurement_item[0][0], user)

    # Список параметров с таким единицами измерения
    columns = []

    # ПРоверка на возможность удалять единицу
    if len(columns) > 0 or len(measures) > 0:
        is_delete = False
    else:
        is_delete = True
    return render_template(
        'unit_of_measurement.html',
        list = unit_of_measurement_item,
        columns=columns,
        is_delete=is_delete,
        measures=measures
    )


@mod.route("/add_unit_of_measurement", methods =['GET', 'POST'] )
@is_logged_in
def add_unit_of_measurement():
    form = UnitOfMeasurement(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        short_name = form.short_name.data

        # Запись в базу данных
        id = db_app.create_unit_of_measurement(name, short_name, 1)[0][0]

        flash('Единица измерения добавлена ', 'success')
        return redirect(url_for('refs.unit_of_measurement', id=id))
    return render_template('add_unit_of_measurement.html', form=form)

# Редактироваение справочника
@mod.route("/edit_unit_of_measurement/<string:id>", methods =['GET', 'POST'] )
@is_logged_in
def edit_unit_of_measurement(id):
    # Данные об измерении
    result = db_app.unit_of_measurement_item(id)

    # Форма заполняется данными из базы
    form = UnitOfMeasurement(request.form)
    form.name.data = result[0][1]
    form.short_name.data = result[0][2]

    if request.method == 'POST':
        # Получение данных из формы
        form.name.data = request.form['name']
        form.short_name.data = request.form['short_name']

        # Если данные из формы валидные
        if form.validate():

            # Обновление базе данных
            db_app.update_unit_of_measurement(form.name.data, form.short_name.data, id)

            flash('Данные обновлены', 'success')
            return redirect(url_for('refs.unit_of_measurement', id=id))

    return render_template('edit_unit_of_measurement.html', form=form, unit=result[0])

# Удаление измерения
@mod.route('/delete_unit_of_measurement/<string:id>', methods=['POST'])
@is_logged_in
def delete_unit_of_measurement(id):

    # Удаление записи о справочнике
    db_app.delete_unit_of_measurement(id)

    flash('Единица измерения удалена', 'success')

    return redirect(url_for('refs.units_of_measurement'))