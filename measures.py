from flask import Blueprint, render_template, flash, redirect, url_for, session, request
import psycopg2
from decorators import is_logged_in
import constants
import itertools
import foo
import json
import numpy as np
import statistic_math as sm

# Мои модули
from forms import *
from statistic_math import Series

mod = Blueprint('measures', __name__)

# Подключение к базе данных
conn = psycopg2.connect(
    database=constants.DATABASE_NAME,
    user=constants.DATABASE_USER,
    password=constants.DATABASE_PASSWORD,
    host=constants.DATABASE_HOST,
    port=constants.DATABASE_PORT)
cursor = conn.cursor()

# Меры
@mod.route("/measures")
@is_logged_in
def measures():
    # Список справочников
    cursor.execute(
        '''SELECT * FROM area_description WHERE user_id=%s AND type=%s ORDER BY id DESC''',
        [str(session['user_id']), constants.AREA_DESCRIPTION_TYPE['Мера']])
    measures_list = cursor.fetchall()
    return render_template('measures.html', list = measures_list)

# Мера
@mod.route("/measure/<string:id>/<string:probal>/", methods =['GET', 'POST'])
@is_logged_in
def measure(id, probal):
    # Получение данных о мере
    cursor.execute("SELECT * FROM area_description WHERE id = %s", [id])
    the_measure = cursor.fetchall()

    cursor.execute("SELECT * FROM data_area WHERE id = %s", [the_measure[0][4]])
    data_a = cursor.fetchall()
    conn.commit()
    prob1 = '20&60&22&23'

    # Строка из URL разбивается на список
    probability = prob1.split('&')

    # Передача данных на страницу
    # Форма расчета фероятностив интервале
    form1 = IntervalForm(request.form)
    form1.di_from.data = probability[0]
    form1.di_to.data = probability[1]

    # Форма расчета доверительного интервала по значению вероятности
    form2 = ProbabilityForm(request.form)
    form2.probability.data = probability[2]

    # Форма фильтра
    form3 = MeFilterForm(request.form)
    form3.test1.data = probability[0]
    form3.test2.data = probability[1]

    # Данные
    try:
        conn2 = psycopg2.connect(
            database=data_a[0][4],
            user=data_a[0][5],
            password=data_a[0][6],
            host=data_a[0][7],
            port=data_a[0][8])
        cur = conn2.cursor()
        cur.execute('SELECT column_name FROM information_schema.columns WHERE table_name=%s;', [data_a[0][9]])
        tc = cur.fetchall()

        if str(tc) == '[]':
            flash('Указаной таблицы нет в базе данных', 'danger')
        else:
            # Получение данных
            try:
                cur.execute('''SELECT ''' + the_measure[0][1] + ''' FROM ''' + data_a[0][9])
                measure_data = cur.fetchall()

                # Данные в список
                mline = [float(i[0]) for i in measure_data]

                # Получение экземпляра класса обработки данных
                to_print = Series(mline)

                # Рассчет математического ожидания
                m, down, up = to_print.mbayes(float(probal))

                # Получение частотного распределения для отображения в графике
                pre = to_print.freq_line_view(1000, down, up)
                stats = to_print.stats_line()

            except:
                pre = []
                stats = []
                flash(mline, 'danger')
    except:
        the_measure = None
        flash('Нет подключения', 'danger')


    return render_template('measure.html',
                           id = id,
                           the_measure = the_measure,
                           sdata = pre,
                           sd = stats,
                           form1=form1,
                           form2=form2,
                           form3=form3,
                           probability = probal,
                           test = [m, down, up]
                           )

# Добавление измерения
@mod.route("/data_area/<string:id>/add_measure_to_<string:item>", methods =['GET', 'POST'] )
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
                       'VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;',
                       (item,
                        description,
                        session['user_id'],
                        id,
                        constants.AREA_DESCRIPTION_TYPE['Мера'],
                        kind_of_metering
                        ))
        meg_id = cursor.fetchone()
        conn.commit()

        # Создание моделей для пар с другими параметрами
        # meg_id - идентификатор новой меры
        # Получить идентификаторы всех остальных измерений
        cursor.execute("SELECT id FROM area_description WHERE type = %s AND id != %s AND data_area_id = %s;", ['1', meg_id, id])
        megs_a = cursor.fetchall()
        megs = [i[0] for i in megs_a]

        if len(megs) >= 1:
            # Получить список идентификаторов гипотез
            cursor.execute("SELECT id FROM hypotheses;")
            hypotheses_id_a = cursor.fetchall()
            hypotheses_id = [i[0] for i in hypotheses_id_a]

            # Создать записи для каждой новой пары и каждой гипотезы)
            arrays = [hypotheses_id, megs, [meg_id[0]]]
            tup = list(itertools.product(*arrays))
            args_str = str(tup).strip('[]')

            # Записать данные
            cursor.execute("INSERT INTO math_models (hypothesis, area_description_1, area_description_2) VALUES " + args_str)

        flash('Параметр добавлен', 'success')
        return redirect(url_for('data_areas.data_area', id=id))
    return render_template('add_measure.html', form=form)

# Редактирование измерения
@mod.route("/data_area/<string:id>/edit_measure_<string:measure_id>", methods =['GET', 'POST'] )
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
            return redirect(url_for('data_areas.data_area', id=id))
    return render_template('edit_measure.html', form=form)

# Добавление измерения времени
@mod.route("/data_area/<string:id>/add_time_to_<string:item>", methods =['GET', 'POST'] )
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
        return redirect(url_for('data_areas.data_area', id=id))
    return render_template('add_time.html', form=form)

# Редактирование измерения времени
@mod.route("/data_area/<string:id>/edit_time_<string:measure_id>", methods =['GET', 'POST'] )
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
            return redirect(url_for('data_areas.data_area', id=id))
    return render_template('edit_time.html', form=form)

# Добавление измерения по справочнику
@mod.route("/data_area/<string:id>/add_mref_to_<string:item>", methods =['GET', 'POST'] )
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
        return redirect(url_for('data_areas.data_area', id=id))
    return render_template('add_mref.html', form=form)

# Редактирование измерения по справочнику
@mod.route("/data_area/<string:id>/edit_mref_<string:measure_id>", methods =['GET', 'POST'] )
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
            return redirect(url_for('data_areas.data_area', id=id))
    return render_template('edit_mref.html', form=form)

# Удаление измерения
@mod.route('/delete_data_measure/<string:id>?data_area_id=<string:data_area_id>', methods=['POST'])
@is_logged_in
def delete_data_measure(id, data_area_id):

    # Execute
    cursor.execute("DELETE FROM area_description WHERE id = %s", [id])
    cursor.execute("DELETE FROM math_models WHERE area_description_2 = %s OR area_description_1 = %s", [id, id])
    conn.commit()

    flash('Предметная область удалена', 'success')

    return redirect(url_for('data_areas.data_area', id=data_area_id))

# Пары
@mod.route("/pair_models")
def pair_models():
    # Список пар
    cursor.execute(
        '''select 
            h.name, 
            m1.r_value, 
            a1.description, 
            a2.description, 
            m1.area_description_1, 
            m1.area_description_2, 
            m1.id 
            from math_models m1
            inner join hypotheses h on m1.hypothesis = h.id
            inner join area_description a1 on m1.area_description_1 = a1.id
            inner join area_description a2 on m1.area_description_2 = a2.id
            order by m1.r_value DESC;''')
    list = cursor.fetchall()
    return render_template('pair_models.html', list=list)

# Пара
@mod.route("/pair/<string:id1>/<string:id2>/<string:model_id>")
def pair(id1, id2, model_id):
    list = [id1, id2]
    pop = [[id1, id2, 'Модель']]

    # Получение данных о модели
    cursor.execute('''SELECT * FROM math_models WHERE id=%s;''', [model_id])
    model = cursor.fetchall()

    slope = float(model[0][2])
    intercept = float(model[0][3])

    # Получение данных для графика
    len = 100
    x = np.array(foo.numline(id1, len=len))
    y = np.array(foo.numline(id2, len=len))

    # Получение экземпляра класса обработки данных
    model_data = sm.Pairs(x, y)

    # Справочник гипотез
    hypotheses = {
        1: model_data.linereg_line,
        2: model_data.powerreg_line,
        3: model_data.exponentialreg1_line,
        4: model_data.hyperbolicreg1_line,
        5: model_data.hyperbolicreg2_line,
        6: model_data.hyperbolicreg3_line,
        7: model_data.logarithmic_line,
        8: model_data.exponentialreg2_line
    }

    # Получение данных для графика по модели
    Y = hypotheses[model[0][1]](slope, intercept)

    # Данные собираются в список для отображения
    xy = np.vstack((x, y, Y))
    for_graf = xy.transpose()

    for i in for_graf:
        pop.append([i[0], i[1], i[2]])

    popa = json.dumps(pop, ensure_ascii=False)


    return render_template('pair.html', list=list, for_graf=popa, model=model)


# Многомерная модель
@mod.route("/multiple_models")
def multiple_models():
    return render_template('multiple_models.html')