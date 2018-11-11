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

    db_da.delate_data_area(id)


    flash('Предметная область удалена', 'success')

    return redirect(url_for('data_areas.data_areas'))

id_to_da = ''

@mod.errorhandler(413)
def errror_413(error):
    global id_to_da
    flash('Загруаемый файл был слишком большой', 'danger')
    return redirect(url_for('data_areas.upload_data_area_from_file', id = id_to_da))

# Загрузка данных из файла
@mod.route("/upload_data_area_from_file/<string:id>", methods =['GET', 'POST'] )
@is_logged_in
def upload_data_area_from_file(id):
    global id_to_da

    id_to_da = id
    # Достаётся предметная область из базы по идентификатору
    data_area = db_da.data_area(id)[0]

    form = DataFile(request.form)

    if request.method == 'POST' and form.validate():

        # Проверка наличия файла
        if 'file' not in request.files:
            flash('Вы не указали файл для загрузки', 'danger')
            return redirect(request.url)

        file = request.files['file']
        type_of = form.type_of.data

        if file and allowed_file(file.filename):
            # Генерируется имя из идентификатора пользователя и врамени загрузки файла
            # Текущее время в сточку только цифрами
            filename = str(session['user_id']) + '_' + id + '_' + file.filename + '.xls'

            # Загружается файл
            file.save(os.path.join(constants.UPLOAD_FOLDER, filename))

            # Создание задачи в очереди на обработку
            db_da.create_task(id, filename, type_of, session['user_id'])

            # Изменение статуса предметной области
            status = '2'
            cursor.execute(
                '''
                UPDATE data_area SET 
                    status=%s
                WHERE id=%s;
                ''',
                (
                    status,
                    id
                ))
            conn.commit()
            flash('Данные добавлены и ожидают обработки', 'success')
            return redirect(url_for('data_areas.data_area', id=id))


        else:
            flash('Неверный формат файла. Справочник должен быть в формате .xlsx', 'danger')

    return render_template('upload_data_area_from_file.html', form=form, data_area=data_area)

