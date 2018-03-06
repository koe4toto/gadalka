# Библиотеки
from datetime import datetime
from flask import Flask, render_template, flash, redirect, url_for, session, request
from passlib.hash import sha256_crypt
from functools import wraps
import psycopg2
import xlrd
import os
import constants

# Мои модули
from test_math import tryit, allowed_file, looking
from forms import *

# Настройки
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = constants.UPLOAD_FOLDER

# Подключение к базе данных
conn = psycopg2.connect(
    database=constants.DATABASE_NAME,
    user=constants.DATABASE_USER,
    password=constants.DATABASE_PASSWORD,
    host=constants.DATABASE_HOST,
    port=constants.DATABASE_PORT)
cursor = conn.cursor()







# Регистрация
@app.route("/register", methods =['GET', 'POST'] )
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Подключение к базе данных
        cursor.execute('INSERT INTO users (name, username, email, password) VALUES (%s, %s, %s, %s);', (name, username, email, password))
        conn.commit()

        flash('Вы зарегистрированны и можете войти', 'success')

        return redirect(url_for('index'))
    return render_template('register.html', form=form)

# Форма входа
@app.route("/login", methods =['GET', 'POST'] )
def login():
    if request.method == 'POST':
        # Даные полей формы авторизации
        username = request.form['username']
        password_candidate = request.form['password']


        # Поиск пользователя в базе по значению username
        cursor.execute("SELECT * FROM users WHERE username = %s", [username])
        result = cursor.fetchall()
        if str(result) == '[]':
            error = 'Пользователь не найден'
            return render_template('login.html', error=error)
        else:
            password = result[0][4]
            if sha256_crypt.verify(password_candidate, password):
                app.logger.info('PASSWORD MATCHED')
                # Открывается сессия
                session['logged_in'] = True
                session['username'] = username
                session['user_id'] = result[0][0]

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Не верный пароль'
                return render_template('login.html', error=error)

    return render_template('login.html')

# Проверка авторизации
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Вы не авторизованы', 'danger')
            return redirect(url_for('login'))
    return wrap

# Выход
@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли', 'success')
    return redirect(url_for('login'))

# Главная
@app.route("/")
def index():
    return render_template('home.html')

# Сводка
@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')

# О проекте
@app.route("/about")
def about():
    return render_template('about.html')







# Предметные области
@app.route("/data_areas")
@is_logged_in
def data_areas():
    return render_template('data_areas.html', list = tryit(session['user_id']))

# Предметная область
@app.route("/data_area/<string:id>/")
def data_area(id):
    # Подключение к базе данных
    cursor.execute("SELECT * FROM data_area WHERE id = %s", [id])
    data_a = cursor.fetchall()
    conn.commit()

    database = data_a[0][4]
    database_user = data_a[0][5]
    database_password = data_a[0][6]
    database_host = data_a[0][7]
    database_port = data_a[0][8]
    database_table = data_a[0][9]

    try:
        conn2 = psycopg2.connect(
            database=database,
            user=database_user,
            password=database_password,
            host=database_host,
            port=database_port)
        cur = conn2.cursor()
        cur.execute('SELECT column_name FROM information_schema.columns WHERE table_name=%s;', [database_table])
        tc = cur.fetchall()
        if str(tc) == '[]':
            flash('Указаной таблицы нет в базе данных', 'danger')
            columns = None
        else:
            columns = [i[0] for i in tc]
    except:
        columns = None
        flash('Нет подключения', 'danger')

    # Получение описания предметной области (меры и измерения)
    cursor.execute('''
    SELECT
        area_description.id,
        area_description.column_name,
        area_description.description,
        area_description.user_id,
        area_description.data_area_id,
        area_description.type,
        refs.name,
        area_description.kind_of_metering
    FROM
        area_description
    LEFT JOIN refs ON area_description.ref_id = refs.id
    WHERE
        area_description.data_area_id = %s;''', [id])
    descriptions = cursor.fetchall()


    # TODO нужно вынести в базу данных справочники видов и типов измерений и избавиться от тупого кода до return
    # Замена идентификаторов значениями справочника
    # Перевод кортэжа в список. Приведение к редактируемому формату списка
    desc = []
    for i in descriptions:
        desc.append(list(i))


    # Переворачиваются словарь, для поиска ключенй по значению
    adt = {value: key for key, value in constants.AREA_DESCRIPTION_TYPE.items()}

    # Замена идентификаторов значениями справочника типов описания
    for n, i in enumerate(desc):
        if i[5] == 1:
            desc[n][5] = adt.get('1')
        elif i[5] == 2:
            desc[n][5] = adt.get('2')
        elif i[5] == 3:
            desc[n][5] = adt.get('3')

    # Замена идентификаторов значениями справочника видов распределений
    for n, i in enumerate(desc):
        if i[7] == 1:
            desc[n][7] = constants.KIND_OF_METERING[0][1]
        elif i[7] == 2:
            desc[n][7] = constants.KIND_OF_METERING[1][1]

    # Данные для представления
    view_table = []

    for i in columns:
        # Проверка наличия описания для данной колонки
        look2 = looking(i, desc)
        if look2 == None:
            view_table.append((i, None, None, None, None, None, None, None, None))
        else:
            view_table.append(look2)

    return render_template('data_area.html', id = id, data_area = data_a, columns=view_table)

# Добавление предметной области
@app.route("/add_data_area", methods =['GET', 'POST'] )
@is_logged_in
def add_data_area():
    form = DataAreaForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        description = form.description.data

        # Подключение к базе данных
        cursor.execute('INSERT INTO data_area (name, description, user_id) VALUES (%s, %s, %s);',
                       (title, description, session['user_id']))
        conn.commit()

        flash('Предметная область добавлена', 'success')
        return redirect(url_for('data_areas'))
    return render_template('add_data_area.html', form=form)

# Редактирование предметной области
@app.route("/edit_data_area/<string:id>", methods =['GET', 'POST'] )
@is_logged_in
def edit_data_area(id):

    # Достаётся предметная область из базы по идентификатору
    cursor.execute("SELECT * FROM data_area WHERE id = %s", [id])
    result = cursor.fetchone()

    # Форма заполняется данными из базы
    form = DataAreaForm(request.form)
    form.title.data = result[1]
    form.description.data = result[2]

    if request.method == 'POST':
        # Получение данных из формы
        form.title.data = request.form['title']
        form.description.data = request.form['description']

        # Если данные из формы валидные
        if form.validate():

            # Обновление базе данных
            cursor.execute('UPDATE data_area SET name=%s, description=%s WHERE id=%s;',
                           (form.title.data, form.description.data, id))
            conn.commit()

            flash('Данные обновлены', 'success')
            return redirect(url_for('data_area', id=id))
    return render_template('edit_data_area.html', form=form)

# Удаление предметной области
@app.route('/delete_data_area/<string:id>', methods=['POST'])
@is_logged_in
def delete_data_area(id):

    # Execute
    cursor.execute("DELETE FROM data_area WHERE id = %s", [id])
    cursor.execute("DELETE FROM area_description WHERE data_area_id = %s", [id])
    conn.commit()

    flash('Предметная область удалена', 'success')

    return redirect(url_for('data_areas'))

# Удаление описания колонки
@app.route('/delete_data_measure/<string:id>?data_area_id=<string:data_area_id>', methods=['POST'])
@is_logged_in
def delete_data_measure(id, data_area_id):

    # Execute
    cursor.execute("DELETE FROM area_description WHERE id = %s", [id])
    conn.commit()

    flash('Предметная область удалена', 'success')

    return redirect(url_for('data_area', id=data_area_id))

# Подключение к базе данных по предметной области
@app.route("/edit_connection/<string:id>", methods =['GET', 'POST'] )
@is_logged_in
def edit_data_connection(id):

    # Достаётся предметная область из базы по идентификатору
    cursor.execute("SELECT * FROM data_area WHERE id = %s", [id])
    result = cursor.fetchall()

    # Форма заполняется данными из базы
    form = DataConForm(request.form)
    form.database.data = result[0][4]
    form.database_user.data = result[0][5]
    form.database_password.data = result[0][6]
    form.database_host.data = result[0][7]
    form.database_port.data = result[0][8]
    form.database_table.data = result[0][9]

    if request.method == 'POST':

        # Получение данных из формы
        form.database.data = request.form['database']
        form.database_user.data = request.form['database_user']
        form.database_password.data = request.form['database_password']
        form.database_host.data = request.form['database_host']
        form.database_port.data = request.form['database_port']
        form.database_table.data = request.form['database_table']

        # Если данные из формы валидные
        if form.validate():
            # Обновление в базе данных
            cursor.execute('UPDATE data_area SET '
                           'database=%s, '
                           'database_user=%s, '
                           'database_password=%s, '
                           'database_host=%s, '
                           'database_port=%s, '
                           'database_table=%s '
                           'WHERE id=%s;',
                           (form.database.data,
                            form.database_user.data,
                            form.database_password.data,
                            form.database_host.data,
                            form.database_port.data,
                            form.database_table.data,
                            id))
            conn.commit()
            flash('Данные обновлены', 'success')
            return redirect(url_for('data_area', id=id))

    return render_template('edit_connection.html', form=form)

# Добавление измерения
@app.route("/data_area/<string:id>/add_measure_to_<string:item>", methods =['GET', 'POST'] )
@is_logged_in
def add_measure(id, item):
    form = MeasureForm(request.form)
    if request.method == 'POST' and form.validate():
        description = form.description.data
        kind_of_metering = form.kind_of_metering.data

        # Подключение к базе данных
        cursor.execute('INSERT INTO area_description '
                       '(column_name, '
                       'description, '
                       'user_id, '
                       'data_area_id, '
                       'type, '
                       'kind_of_metering) '
                       'VALUES (%s, %s, %s, %s, %s, %s);',
                       (item,
                        description,
                        session['user_id'],
                        id,
                        constants.AREA_DESCRIPTION_TYPE['Мера'],
                        kind_of_metering
                        ))
        conn.commit()

        flash('Мера добавлена', 'success')
        return redirect(url_for('data_area', id=id))
    return render_template('add_measure.html', form=form)

# Редактирование измерения
@app.route("/data_area/<string:id>/edit_measure_<string:measure_id>", methods =['GET', 'POST'] )
@is_logged_in
def edit_measure(id, measure_id):

    # Достаётся предметная область из базы по идентификатору
    cursor.execute("SELECT * FROM area_description WHERE id = %s", [measure_id])
    result = cursor.fetchone()

    # Форма заполняется данными из базы
    form = MeasureForm(request.form)
    form.description.default = result[2]
    form.kind_of_metering.default = result[7]
    form.process()


    if request.method == 'POST':
        # Получение данных из формы
        form.description.data = request.form['description']
        form.kind_of_metering.data = request.form['kind_of_metering']

        # Если данные из формы валидные
        if form.validate():

            # Обновление базе данных
            cursor.execute('UPDATE area_description SET description=%s, kind_of_metering=%s WHERE id=%s;',
                           (form.description.data, form.kind_of_metering.data, measure_id))
            conn.commit()

            flash('Данные обновлены', 'success')
            return redirect(url_for('data_area', id=id))
    return render_template('edit_measure.html', form=form)

# Добавление измерения времени
@app.route("/data_area/<string:id>/add_time_to_<string:item>", methods =['GET', 'POST'] )
@is_logged_in
def add_time(id, item):
    form = MeasureForm(request.form)
    if request.method == 'POST' and form.validate():
        description = form.description.data
        kind_of_metering = form.kind_of_metering.data

        # Подключение к базе данных
        cursor.execute('INSERT INTO area_description '
                       '(column_name, '
                       'description, '
                       'user_id, '
                       'data_area_id, '
                       'type, '
                       'kind_of_metering) '
                       'VALUES (%s, %s, %s, %s, %s, %s);',
                       (item,
                        description,
                        session['user_id'],
                        id,
                        constants.AREA_DESCRIPTION_TYPE['Время'],
                        kind_of_metering
                        ))
        conn.commit()

        flash('Измерение времени добавлено', 'success')
        return redirect(url_for('data_area', id=id))
    return render_template('add_time.html', form=form)

# Редактирование измерения времени
@app.route("/data_area/<string:id>/edit_time_<string:measure_id>", methods =['GET', 'POST'] )
@is_logged_in
def edit_time(id, measure_id):

    # Достаётся предметная область из базы по идентификатору
    cursor.execute("SELECT * FROM area_description WHERE id = %s", [measure_id])
    result = cursor.fetchone()

    # Форма заполняется данными из базы
    form = MeasureForm(request.form)
    form.description.default = result[2]
    form.kind_of_metering.default = result[7]
    form.process()


    if request.method == 'POST':
        # Получение данных из формы
        form.description.data = request.form['description']
        form.kind_of_metering.data = request.form['kind_of_metering']

        # Если данные из формы валидные
        if form.validate():

            # Обновление базе данных
            cursor.execute('UPDATE area_description SET description=%s, kind_of_metering=%s WHERE id=%s;',
                           (form.description.data, form.kind_of_metering.data, measure_id))
            conn.commit()

            flash('Данные обновлены', 'success')
            return redirect(url_for('data_area', id=id))
    return render_template('edit_time.html', form=form)

# Добавление измерения по справочнику
@app.route("/data_area/<string:id>/add_mref_to_<string:item>", methods =['GET', 'POST'] )
@is_logged_in
def add_mref(id, item):

    # Список справочников пользователя
    cursor.execute("SELECT id, name FROM refs WHERE user_id = %s", [str(session['user_id'])])
    result = cursor.fetchall()
    dif = [(str(i[0]), str(i[1])) for i in result]

    form = RefMeasureForm(request.form)
    form.ref.choices = dif

    if request.method == 'POST' and form.validate():
        description = form.description.data
        ref = form.ref.data

        # Подключение к базе данных
        cursor.execute('INSERT INTO area_description '
                       '(column_name, '
                       'description, '
                       'user_id, '
                       'data_area_id, '
                       'type, '
                       'ref_id) '
                       'VALUES (%s, %s, %s, %s, %s, %s);',
                       (item,
                        description,
                        session['user_id'],
                        id,
                        constants.AREA_DESCRIPTION_TYPE['Справочник'],
                        ref
                        ))
        conn.commit()

        flash('Измерение по справочнику добавлено', 'success')
        return redirect(url_for('data_area', id=id))
    return render_template('add_mref.html', form=form)

# Редактирование измерения по справочнику
@app.route("/data_area/<string:id>/edit_mref_<string:measure_id>", methods =['GET', 'POST'] )
@is_logged_in
def edit_mref(id, measure_id):

    # Достаётся предметная область из базы по идентификатору
    cursor.execute("SELECT * FROM area_description WHERE id = %s", [measure_id])
    result = cursor.fetchone()

    # Список справочников пользователя
    cursor.execute("SELECT id, name FROM refs WHERE user_id = %s", [str(session['user_id'])])
    result2 = cursor.fetchall()
    dif = [(str(i[0]), str(i[1])) for i in result2]

    # Форма заполняется данными из базы
    form = RefMeasureForm(request.form)
    form.description.default = result[2]
    form.ref.choices = dif
    form.ref.default = result[6]
    form.process()


    if request.method == 'POST':
        # Получение данных из формы
        form.description.data = request.form['description']
        form.ref.data = request.form['ref']

        # Если данные из формы валидные
        if form.validate():

            # Обновление базе данных
            cursor.execute('UPDATE area_description SET description=%s, ref_id=%s WHERE id=%s;',
                           (form.description.data, form.ref.data, measure_id))
            conn.commit()

            flash('Данные обновлены', 'success')
            return redirect(url_for('data_area', id=id))
    return render_template('edit_mref.html', form=form)





# Справочники
@app.route("/refs")
@is_logged_in
def refs():
    # Список справочников
    cursor.execute(
        'SELECT * FROM refs WHERE user_id=%s ORDER BY register_date DESC',
        [str(session['user_id'])])
    ref_list = cursor.fetchall()
    return render_template('refs.html', list = ref_list)

# Справочник
@app.route("/ref/<string:id>/")
def ref(id):
    # Подключение к базе данных
    cursor.execute("SELECT * FROM refs WHERE id = %s", [id])
    the_ref = cursor.fetchall()

    ref_data = the_ref[0][4]

    cursor.execute("SELECT * FROM " + str(ref_data) + " ;")
    columns = cursor.fetchall()
    print(columns)

    return render_template('ref.html', id = id, ref = the_ref, columns=columns)

# Добавление справочника
@app.route("/add_ref", methods =['GET', 'POST'] )
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
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Создаётся запись в базе данных
            # Генерируется имя для таблицы с данными
            table_name = str('ref' + str(session['user_id']) + now)

            # Создаётся запись в таблице с базой данных
            cursor.execute('INSERT INTO refs (name, description, user_id, data) VALUES (%s, %s, %s, %s);',
                           (name, description, session['user_id'], table_name))
            # Создаёется таблица для хранения данных
            cursor.execute('''CREATE TABLE '''+ table_name +''' ("code" varchar, "value" varchar, "parent_value" varchar);''')
            conn.commit()

            # Открывается сохраненный файл
            rb = xlrd.open_workbook(os.path.abspath('.') + '/uploaded_files/' + filename)
            sheet = rb.sheet_by_index(0)

            # Запсиь строчек справочника в базу данных
            in_table = range(sheet.nrows)
            try:
                for rownum in in_table:
                    if rownum >= 1:
                        row = sheet.row_values(rownum)
                        cursor.execute('''INSERT INTO ''' + table_name + ''' (code, value, parent_value) VALUES (%s, %s, %s);''',
                                       (row[0], row[1], row[2]))
                        conn.commit()
            except:
                flash('Неверный формат данных в файле', 'danger')
                return redirect(url_for('add_ref'))

            # Удаление загруженного файла
            os.remove(constants.UPLOAD_FOLDER + filename)

            flash('Справочник добавлен', 'success')
            return redirect(url_for('refs'))
        else:
            flash('Неверный формат файла. Справочник должен быть в формате .xlsx', 'danger')

    return render_template('add_ref.html', form=form)

# Удаление справочника
@app.route('/delete_ref/<string:id>', methods=['POST'])
@is_logged_in
def delete_ref(id):
    # Execute
    cursor.execute("SELECT * FROM refs WHERE id = %s", [id])
    the_ref = cursor.fetchall()
    ref_data = the_ref[0][4]
    cursor.execute("DELETE FROM refs WHERE id = %s", [id])
    cursor.execute("DROP TABLE " + ref_data)
    conn.commit()

    flash('Справочник удалён', 'success')

    return redirect(url_for('refs'))

# Редактироваение справочника
@app.route("/edit_ref/<string:id>", methods =['GET', 'POST'] )
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
            cursor.execute('UPDATE refs SET name=%s, description=%s WHERE id=%s;',
                           (form.name.data, form.description.data, id))
            conn.commit()

            flash('Данные обновлены', 'success')
            return redirect(url_for('ref', id=id))

    return render_template('edit_ref.html', form=form)

# Обновление данных справочника из файла
@app.route("/update_ref/<string:id>", methods =['GET', 'POST'] )
@is_logged_in
def update_ref(id):
    # Достаётся предметная область из базы по идентификатору
    cursor.execute("SELECT * FROM refs WHERE id = %s", [id])
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
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Имя обновляемой таблицы
            table_name = result[0][4]

            # Отчистка таблицы
            cursor.execute(
                '''DELETE FROM ''' + table_name)
            conn.commit()

            # Открывается сохраненный файл
            rb = xlrd.open_workbook(constants.UPLOAD_FOLDER + filename)
            sheet = rb.sheet_by_index(0)

            # Запсиь строчек справочника в базу данных
            in_table = range(sheet.nrows)
            try:
                for rownum in in_table:
                    if rownum >= 1:
                        row = sheet.row_values(rownum)
                        cursor.execute(
                            '''INSERT INTO ''' + table_name + ''' (code, value, parent_value) VALUES (%s, %s, %s);''',
                            (row[0], row[1], row[2]))
                        conn.commit()
            except:
                flash('Неверный формат данных в файле', 'danger')
                return redirect(url_for('update_ref'))

            # Удаление загруженного файла
            os.remove(constants.UPLOAD_FOLDER + filename)

            flash('Данные обновлены', 'success')
            return redirect(url_for('ref', id=id))
        else:
            flash('Неверный формат файла. Справочник должен быть в формате .xlsx', 'danger')


    return render_template('update_ref.html', form=form)



# Меры
@app.route("/measures")
@is_logged_in
def measures():
    # Список справочников
    cursor.execute(
        '''SELECT * FROM area_description WHERE user_id=%s AND type=%s ORDER BY id DESC''',
        [str(session['user_id']), constants.AREA_DESCRIPTION_TYPE['Мера']])
    measures_list = cursor.fetchall()
    return render_template('measures.html', list = measures_list)

# Мера
@app.route("/measure/<string:id>/")
def measure(id):
    # Подключение к базе данных
    cursor.execute("SELECT * FROM area_description WHERE id = %s", [id])
    the_measure = cursor.fetchall()

    return render_template('measure.html', id = id, the_measure = the_measure)


# Запуск сервера
if __name__ == "__main__":
    app.secret_key = 'secret123'
    app.run(debug=True)