from flask import Blueprint, render_template, flash, redirect, url_for, session, request
import psycopg2
import xlrd
import os
from decorators import is_logged_in
from datetime import datetime
import constants

# Мои модули
from foo import allowed_file, looking, sqllist, sqlvar
from forms import *
from database import conn, cursor, data_cursor, data_conn

mod = Blueprint('refs', __name__)

# Справочники
@mod.route("/refs")
@is_logged_in
def refs():
    # Список справочников
    cursor.execute('''SELECT * FROM refs ORDER BY register_date DESC;''')
    ref_list = cursor.fetchall()
    return render_template('refs.html', list = ref_list)

# Справочник
@mod.route("/ref/<string:id>/")
def ref(id):
    # Подключение к базе данных
    try:
        cursor.execute("SELECT * FROM refs WHERE id = %s", [id])
        the_ref = cursor.fetchall()
    except:
        redirect(url_for('refs.refs'))

    ref_data = the_ref[0][4]

    data_cursor.execute('''SELECT * FROM {0} ;'''.format(str(ref_data)))
    columns = data_cursor.fetchall()

    return render_template('ref.html', id = id, ref = the_ref, columns=columns)

# Добавление справочника
# TODO Справоничк нужно сохранять в специальной базе
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
                cursor.execute(
                    '''
                    INSERT INTO refs (name, description, user_id, data) VALUES ('{0}', '{1}', '{2}', '{3}');
                    '''.format(name, description, user, table_name)
                )
                conn.commit()

                # Создаёется таблица для хранения данных
                data_cursor.execute('''CREATE TABLE {0} ("code" varchar primary key, "value" varchar, "parent_value" varchar);'''.format(table_name))
                data_conn.commit()
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
                        data_cursor.execute(
                            '''
                            INSERT INTO {0} (code, value, parent_value) VALUES ('{1}', '{2}', '{3}');
                            '''.format(table_name, row[0], row[1], row[2])
                        )
                        data_conn.commit()
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
    # Execute
    cursor.execute('''SELECT * FROM refs WHERE id = '{0}';'''.format(id))
    the_ref = cursor.fetchall()
    ref_data = the_ref[0][4]
    cursor.execute('''DELETE FROM refs WHERE id = '{0}';'''.format(id))
    conn.commit()
    data_cursor.execute('''DROP TABLE {0}'''.format(ref_data))
    data_conn.commit()

    flash('Справочник удалён', 'success')

    return redirect(url_for('refs.refs'))

# Редактироваение справочника
@mod.route("/edit_ref/<string:id>", methods =['GET', 'POST'] )
@is_logged_in
def edit_ref(id):
    # Достаётся предметная область из базы по идентификатору
    cursor.execute("SELECT * FROM refs WHERE id = %s", [id])
    result = cursor.fetchall()

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
            cursor.execute(
                '''
                UPDATE refs SET name='{0}', description='{1}' WHERE id='{2}';
                '''.format(form.name.data, form.description.data, id)
            )
            conn.commit()

            flash('Данные обновлены', 'success')
            return redirect(url_for('refs.ref', id=id))

    return render_template('edit_ref.html', form=form)

# Обновление данных справочника из файла
@mod.route("/update_ref/<string:id>", methods =['GET', 'POST'] )
@is_logged_in
def update_ref(id):
    # Достаётся предметная область из базы по идентификатору
    cursor.execute('''SELECT * FROM refs WHERE id = '{0}';'''.format(id))
    result = cursor.fetchall()

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
            data_cursor.execute(
                '''DELETE FROM '{0}';'''.format(table_name))
            data_conn.commit()

            # Открывается сохраненный файл
            rb = xlrd.open_workbook(constants.UPLOAD_FOLDER + filename)
            sheet = rb.sheet_by_index(0)

            # Запсиь строчек справочника в базу данных
            in_table = range(sheet.nrows)
            try:
                for rownum in in_table:
                    if rownum >= 1:
                        row = sheet.row_values(rownum)
                        data_cursor.execute(
                            '''
                            INSERT INTO {0} (code, value, parent_value) VALUES ('{1}', '{2}', '{3}');
                            '''.format(table_name, row[0], row[1], row[2])
                            )
                        data_conn.commit()
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