from flask import Blueprint, render_template, flash, redirect, url_for, session, request
import psycopg2
import xlrd
import os
from decorators import is_logged_in
import constants
import database as db

# Мои модули
from foo import *
from forms import *

mod = Blueprint('data_areas', __name__)

# Работа с базами данных
conn = db.conn
cursor = db.cursor

db_da = db.data_area()
db_measure = db.measures()


# Предметные области
@mod.route("/data_areas")
@is_logged_in
def data_areas():
    user = str(session['user_id'])
    list = db_da.select_da(user)
    return render_template('data_areas.html', list = list)


# Предметная область
@mod.route("/data_area/<string:id>/")
def data_area(id):
    # Поолучение данных о предметной области
    data_area = db_da.data_area(id)

    # Получение описания параметров
    measures = db_measure.select_measures_to_data_area(id)

    return render_template('data_area.html', data_area=data_area[0], measures=measures)

# Добавление предметной области
@mod.route("/add_data_area", methods =['GET', 'POST'] )
@is_logged_in
def add_data_area():
    form = DataAreaForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        description = form.description.data

        # Запись в базу данных
        db_da.create_data_area(title, description, session['user_id'], '1')

        flash('Предметная область добавлена', 'success')
        return redirect(url_for('data_areas.data_areas'))
    return render_template('add_data_area.html', form=form)

# Редактирование предметной области
@mod.route("/edit_data_area/<string:id>", methods =['GET', 'POST'] )
@is_logged_in
def edit_data_area(id):

    # Достаётся предметная область из базы по идентификатору
    data_area = db_da.data_area(id)[0]

    # Форма заполняется данными из базы
    form = DataAreaForm(request.form)
    form.title.data = data_area[1]
    form.description.data = data_area[2]

    if request.method == 'POST':
        # Получение данных из формы
        form.title.data = request.form['title']
        form.description.data = request.form['description']

        # Если данные из формы валидные
        if form.validate():

            # Обновление базе данных
            db_da.update_data_area(form.title.data, form.description.data, data_area[4], id)

            flash('Данные обновлены', 'success')
            return redirect(url_for('data_areas.data_area', id=id))
    return render_template('edit_data_area.html', form=form)

# Удаление предметной области
@mod.route('/delete_data_area/<string:id>', methods=['POST'])
@is_logged_in
def delete_data_area(id):

    # Получение свдений о предметной области
    cursor.execute("SELECT database_table FROM data_area WHERE id = %s", [id])
    data_a = cursor.fetchall()

    # Удаление данных из таблиц
    cursor.execute("DELETE FROM measures WHERE data_area_id = %s", [id])
    cursor.execute("DELETE FROM data_area WHERE id = %s", [id])
    conn.commit()

    if data_a[0][0] is not None:
        cursor.execute("DROP TABLE " + data_a[0][0])
        conn.commit()

    flash('Предметная область удалена', 'success')

    return redirect(url_for('data_areas.data_areas'))

# Загрузка данных из файла
@mod.route("/upload_data_area_from_file/<string:id>", methods =['GET', 'POST'] )
@is_logged_in
def upload_data_area_from_file(id):

    # Подключение к базе данных
    cursor.execute("SELECT name, database_table FROM data_area WHERE id = %s", [id])
    data_a = cursor.fetchall()

    if request.method == 'POST':

        # Проверка наличия файла
        if 'file' not in request.files:
            flash('Вы не указали файл для загрузки', 'danger')
            return redirect(request.url)

        file = request.files['file']

        if file and allowed_file(file.filename):
            # Генерируется имя из идентификатора пользователя и врамени загрузки файла
            # Текущее время в сточку только цифрами
            filename = str(session['user_id']) + file.filename + '.xlsx'

            # Загружается файл
            file.save(os.path.join(constants.UPLOAD_FOLDER, filename))

            # Открывается сохраненный файл
            rb = xlrd.open_workbook(constants.UPLOAD_FOLDER + filename)
            sheet = rb.sheet_by_index(0)

            # Запсиь строчек справочника в базу данных
            in_table = range(sheet.nrows)

            try:
                row = sheet.row_values(in_table[0])

                if data_a[0][1] != None:
                    # Удаление предыдущих данных
                    cursor.execute("DROP TABLE " + data_a[0][1])
                    conn.commit()

                # Формирование списка колонок для создания новой таблицы
                rows = str('"' + str(row[0]) + '" ' + 'varchar')
                for i in row:
                    if row.index(i) > 0:
                        rows += ', "' + str(i) + '" ' + 'varchar'

                # Формирование названия таблицы хранения данных
                table_name = 'data_' + str(session['user_id']) + str(id)

                # Добавление данных в таблицу
                cursor.execute('UPDATE data_area SET '
                               'database=%s, '
                               'database_user=%s, '
                               'database_password=%s, '
                               'database_host=%s, '
                               'database_port=%s, '
                               'database_table=%s '
                               'WHERE id=%s;',
                               (constants.DATABASE_NAME,
                                constants.DATABASE_USER,
                                constants.DATABASE_PASSWORD,
                                constants.DATABASE_HOST,
                                constants.DATABASE_PORT,
                                table_name,
                                id))
                conn.commit()


                try:
                    # Создание новой таблицы
                    cursor.execute('''CREATE TABLE ''' + table_name + ''' (''' + rows + ''');''')
                    conn.commit()

                    # Удаление загруженного файла
                    os.remove(constants.UPLOAD_FOLDER + filename)
                except:
                    flash('Таблица не добавилась 8(', 'danger')
                    return redirect(request.url)


                # Загрузка данных из файла
                try:
                    for rownum in in_table:
                        if rownum == 0:
                            ta = sqllist(sheet.row_values(rownum))
                        elif rownum >= 1:
                            row = sheet.row_values(rownum)
                            va = sqlvar(row)

                            cursor.execute(
                                '''INSERT INTO ''' + table_name + ''' ('''+
                                ta +''') VALUES ('''+
                                va+''');''')
                            conn.commit()

                except:
                    flash('Не удалось загрузить данные', 'danger')
                    return redirect(url_for('data_areas.data_area', id=id))

                flash('Даные успешно обновлены', 'success')
                return redirect(url_for('data_areas.data_area', id=id))

            except:
                flash('Неверный формат данных в файле', 'danger')
                return redirect(request.url)

        else:
            flash('Неверный формат файла. Справочник должен быть в формате .xlsx', 'danger')

    return render_template('upload_data_area_from_file.html', form=form)

