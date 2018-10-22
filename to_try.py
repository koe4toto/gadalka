import constants
import statistic_math as sm
import foo
import numpy as np
import random
import xlrd
import json
import database as db
import datetime


# Рассчета свойств модели и запись результатов в базу данных
def search_model(hypothesis, adid1, adid2):
    print('Старт!')


    # Получение списков данных
    x = foo.numline(adid1, len=100)
    y = foo.numline(adid2, len=100)
    print(x)

    # Экземпляр класса обработки данных по парам
    pairs = sm.Pairs(x, y)

    # Справочник гипотез
    hypotheses = {
        1: pairs.linereg,
        2: pairs.powerreg,
        3: pairs.exponentialreg1,
        4: pairs.hyperbolicreg1,
        5: pairs.hyperbolicreg2,
        6: pairs.hyperbolicreg3,
        7: pairs.logarithmic,
        8: pairs.exponentialreg2
    }

    # Рассчета показателей по указанной в базе модели
    slope, intercept, r_value, p_value, std_err = hypotheses[hypothesis]()
    print(slope, intercept, r_value, p_value, std_err)

    # Сохранение результатов в базу данных
    cursor.execute('UPDATE math_models SET '
                   'slope=%s, '
                   'intercept=%s, '
                   'r_value=%s, '
                   'p_value=%s, '
                   'std_err=%s '
                   'WHERE '
                   'area_description_1 = %s '
                   'AND area_description_2 = %s '
                   'AND hypothesis = %s;',
                   (slope,
                    intercept,
                    r_value,
                    p_value,
                    std_err,
                    adid1,
                    adid2,
                    hypothesis
                    ))
    conn.commit()

    print('Готово!')


# Обработка моделей с пустыми значениями
def primal_calc():
    # Выбор модели для рассчета
    cursor.execute("SELECT * FROM math_models m1 WHERE NOT (m1.r_value IS NOT NULL) LIMIT 1;")
    model = cursor.fetchall()
    print(model)

    while model != '[]':
        search_model(model[0][1], model[0][7], model[0][8])

        # Выбор модели для рассчета
        cursor.execute("SELECT * FROM math_models m1 WHERE NOT (m1.r_value IS NOT NULL) LIMIT 1;")
        model = cursor.fetchall()
        print(model)


#primal_calc()


def gen_line(x, slope, imtersept):
    y = slope * x + imtersept
    Y = [i + random.randint(-10, 15) for i in y]
    return Y

# Данные степенной модели
def gen_powerrege(x, slope, intercept):
    y = intercept * np.power(slope, x)
    Y = [i + random.randint(-10, 15) for i in y]
    return Y

# Данные показательной модели 1
def gen_exponentialreg1(x, slope, intercept):
    y = slope * np.power(x, intercept)
    Y = [i + random.randint(-10, 15) for i in y]
    return Y

# Данные гиперболической модели 1
def gen_hyperbolicreg1(x, slope, intercept):
    y = slope / x + intercept
    Y = [i + random.randint(-10, 15) for i in y]
    return Y

# Данные гиперболической модели 2
def gen_hyperbolicreg2(x, slope, intercept):
    y = 1 / (slope * x + intercept)
    Y = [i + random.randint(-10, 15) for i in y]
    return Y

# Данные гиперболической модели 3
def gen_hyperbolicreg3(x, slope, intercept):
    y = 1 / (slope / x + intercept)
    Y = [i + random.randint(-10, 15) for i in y]
    return Y

# Данные логарифмической модели
def gen_logarithmic(x, slope, intercept):
    y = slope * np.log10(x) + intercept
    Y = [i + random.randint(-10, 15) for i in y]
    return Y

# Данные экспоненциальной модели 2
def gen_exponentialreg2(x, slope, intercept):
    y = slope * np.power(x * intercept, 2.718)
    Y = [i + random.randint(-10, 15) for i in y]
    return Y


def gen_data():
    x = np.array([random.random() * 100 for i in range(90)])
    line_1 = gen_hyperbolicreg1(x, 3, 2)
    line_2 = gen_hyperbolicreg1(x, 2, 3)

    X = np.vstack((x, line_1, line_2))
    end = X.transpose()

    for i in end:
        # Подключение к базе данных
        cursor.execute('INSERT INTO test_data (x, line_1, line_2) VALUES (%s, %s, %s);',
                       (i[0], i[1], i[2]))
        conn.commit()
    return end

#print(gen_data())
#primal_calc()


#print(foo.numline(70))


# Создание моделей для пар с другими параметрами
# meg_id - идентификатор новой меры
# Получить идентификаторы всех остальных измерений
'''
cursor.execute("SELECT id FROM measures WHERE type = %s AND id != %s AND data_area_id = %s;", ['1', meg_id, id])
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
                    cursor.execute('CREATE TABLE ' + table_name + ' (' + rows + ');')
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
                                'INSERT INTO ' + table_name + ' ('+
                                ta +') VALUES ('+
                                va+');')
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
'''


def validate_date(date_text):
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
        print('Всё хорошо')
        return True
    except ValueError:
        print('Формат нe подходит')
        return False

def validate_time(time_text):
    try:
        datetime.datetime.strptime(time_text, '%H:%M:%S')
        print('Всё хорошо')
        return True
    except ValueError:
        print('Формат нe подходит')
        return False

def validate_datetime(datetime_text):
    try:
        datetime.datetime.strptime(datetime_text, '%Y-%m-%d %H:%M:%S')
        print('Всё хорошо')
        return True
    except ValueError:
        print('Формат нe подходит')
        return False

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def not_empty(s):
    if s == None:
        return False
    elif s == '':
        return False
    else:
        return True





line = (15, 2, '1_2_test0.xlsx', 1, 1, '2018-10-18 16:29:44.278127')

def line_check(line):
    print('Данные на вход из очереди: ', line)
    data_area_id = line[0]
    filename = line[2]

    # Открывается сохраненный файл
    rb = xlrd.open_workbook(constants.UPLOAD_FOLDER + filename)
    sheet = rb.sheet_by_index(0)

    try:
        # Запсиь строчек справочника в базу данных
        in_table = range(sheet.nrows)
        row = sheet.row_values(in_table[0])
        print(row)

        # Формирование названия таблицы хранения данных
        table_name = 'data_' + '1_' + str(data_area_id)


        # Формирование списка колонок для создания новой таблицы
        rows = str('"' + str(row[0]) + '" ' + 'varchar')
        for i in row:
            if row.index(i) > 0:
                rows += ', "' + str(i) + '" ' + 'varchar'
        print(rows)


    except:
        print('Что-то пошло не так. 8(')

    # Загрузка данных из файла
    try:
        for rownum in in_table:
            if rownum == 0:
                ta = foo.sqllist(sheet.row_values(rownum))
            elif rownum >= 1:
                row = sheet.row_values(rownum)
                va = foo.sqlvar(row)

    except:
        print('Что-то пошло не так. 8(')


def head_search():
    # Опсиание ожидаемого набора данных из базы
    in_base = [(1, 'line2'), (2, 'ref1')]

    # Набор колонок из файла
    in_file = ['ref1', 'line1', 'line2', 'line3']

    # Строка с данными из файла
    in_file_line = [11, 22, 33, 44]

    # Порядковые номера столбцов в файле, которые ожидаются для обработки в базе
    in_file_indexes = []

    # Проверка полного набора колонок в файле
    for i in in_base:
        if i[1] in in_file:
            in_file_indexes.append(in_file.index(i[1]))
        else:
            return False, i[1]

    # Данные из строки, которые можно записать в базу данных
    result = [i for i in in_file_line if in_file_line.index(i) in in_file_indexes]

    return result

print(head_search())
