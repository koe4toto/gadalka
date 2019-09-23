from flask import Blueprint, render_template, flash, redirect, url_for, session, request
import os
from decorators import is_logged_in
from model_calculation import multiple_models_auto_calc
from forms import *
import databases.db_app as db_app
import databases.db_data as db_data
import databases.db_queue as db_queue
import constants
from tools import allowed_file, looking, sqllist, sqlvar


mod = Blueprint('data_areas', __name__)

# Предметные области
@mod.route("/data_areas")
@is_logged_in
def data_areas():
    user = str(session['user_id'])
    return render_template(
        'data_areas.html',
        list = db_app.select_da(user)
    )


# Предметная область
@mod.route("/data_area/<string:id>/")
@is_logged_in
def data_area(id):
    # Поолучение данных о предметной области
    data_area = db_app.data_area(id)

    # Путь к файлу
    filename = 'olap_' + id + '.xls'

    # Получение описания параметров
    measures = db_app.select_measures_of_the_data_area(id)

    # Получение последнй операции загрузки данных
    log = db_app.select_data_log(id)

    if len(log) == 0:
        log_status = '1'
        last_log = None
    else:
        log_status = log[0][5]
        last_log = log[0]

    return render_template(
        'data_area.html',
        data_area=data_area[0],
        measures=measures,
        last_log=last_log,
        log_status=log_status,
        filename=filename
    )

# Добавление предметной области
@mod.route("/add_data_area", methods =['GET', 'POST'] )
@is_logged_in
def add_data_area():
    form = DataAreaForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        description = form.description.data
        partition_limit = form.partition_limit.data

        # Запись в базу данных
        olap_name, data_base_id = db_app.create_data_area(title, description, session['user_id'], '1', partition_limit)

        # Создание таблицы с данными
        db_data.create_olap(olap_name)

        # Сохранение имени куба в для ПО
        db_app.update_data_area_olap_name(olap_name, data_base_id[0][0])

        flash('Предметная область добавлена', 'success')
        return redirect(url_for('data_areas.data_areas'))
    return render_template('add_data_area.html', form=form)

# Редактирование предметной области
@mod.route("/edit_data_area/<string:id>", methods =['GET', 'POST'] )
@is_logged_in
def edit_data_area(id):

    # Достаётся предметная область из базы по идентификатору
    data_area = db_app.data_area(id)[0]

    # Форма заполняется данными из базы
    form = DataAreaForm(request.form)
    form.title.data = data_area[1]
    form.description.data = data_area[2]
    form.partition_limit.data = data_area[7]

    if request.method == 'POST':
        # Получение данных из формы
        form.title.data = request.form['title']
        form.description.data = request.form['description']
        form.partition_limit.data = request.form['partition_limit']

        # Если данные из формы валидные
        if form.validate():

            # Обновление базе данных
            db_app.update_data_area(
                form.title.data,
                form.description.data,
                data_area[4],
                id,
                form.partition_limit.data
            )

            flash('Данные обновлены', 'success')
            return redirect(url_for('data_areas.data_area', id=id))
    return render_template('edit_data_area.html', form=form)

# Удаление предметной области
@mod.route('/delete_data_area', methods =['GET', 'POST'] )
@is_logged_in
def delete_data_area():
    # Идентификатор отчета
    id = request.args.get('id', type=str)

    filename = 'olap_'+ id + '.xls'
    database_table = db_app.delete_data_area(id)

    # Удаление таблицы с данными
    db_data.delete_olap(database_table)

    # Удаление загруженного файла
    try:
        os.remove(constants.ERROR_FOLDER + filename)
        os.remove(constants.UPLOAD_FOLDER + filename)
    except:
        pass

    # Перерасчет моделей
    multiple_models_auto_calc()

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
    data_area = db_app.data_area(id)[0]

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
            filename = 'olap_'+ id + '.xls'

            # Загружается файл
            file.save(os.path.join(constants.UPLOAD_FOLDER, filename))

            # Изменение статуса предметной области
            status = '2'
            log_id = db_app.insert_data_log(id, status)

            # Создание задачи в очереди на обработку
            db_queue.create_task(id, filename, type_of, session['user_id'], log_id[0][0])
            flash('Данные добавлены и ожидают обработки', 'success')
            return redirect(url_for('data_areas.data_area', id=id))

        else:
            flash('Неверный формат файла. Справочник должен быть в формате .xlsx', 'danger')

    return render_template('upload_data_area_from_file.html', form=form, data_area=data_area)



# Загрузки в предметную область
@mod.route("/data_area_log/<string:id>/")
@is_logged_in
def data_area_log(id):
    return render_template(
        'data_area_log.html',
        data_area=db_app.data_area(id)[0],
        log=db_app.select_data_area_log(id)
    )

# Загрузки
@mod.route("/data_log/")
@is_logged_in
def data_log():
    return render_template(
        'data_log.html',
        log=db_app.select_all_data_log()
    )

# Удаление задачи на загрузку данных
@mod.route('/delete_data_log/<string:id>/<string:data_area_id>/<string:context>', methods=['POST'])
@is_logged_in
def delete_data_log(id, data_area_id, context):
    filename = 'olap_' + id + '.xls'
    # Удаление данных из таблиц
    db_app.delete_data_log(id)
    db_queue.delete_task(id)

    # Удаление загруженного файла
    try:
        os.remove(constants.UPLOAD_FOLDER + filename)
    except:
        pass

    flash('Загрузка отменена', 'success')
    if context == 'data_area_log':
        return redirect(url_for('data_areas.data_area_log', id=data_area_id))
    elif context == 'data_log':
        return redirect(url_for('data_areas.data_log'))
    elif context == 'data_area':
        return redirect(url_for('data_areas.data_area', id=data_area_id))