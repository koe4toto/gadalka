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