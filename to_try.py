import constants
import statistic_math as sm
import foo
import numpy as np
import random
import xlrd
import json
import database as db
import datetime
import xlwt
import os

cursor = db.cursor
conn = db.conn
data_cursor = db.data_cursor
data_conn = db.data_conn


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


def validate_date(date):
    try:
        datetime.datetime.strptime(date, '%Y-%m-%d')
        return True, date, 'Принято'
    except ValueError:
        return False, date, 'Не верный формат даты'

def validate_time(time):
    try:
        datetime.datetime.strptime(time, '%H:%M:%S')
        return True, time, 'Принято'
    except ValueError:
        return False, time, 'Не верный формат времени'

def validate_datetime(datetime):
    try:
        datetime.datetime.strptime(datetime, '%Y-%m-%d %H:%M:%S')
        return True, datetime, 'Принято'
    except ValueError:
        return False, datetime, 'Не верный форма времени'

def is_number(number):
    try:
        float(number)
        return True, number, 'Принято'
    except ValueError:
        return False, number, 'Не верный формат данных'

def not_empty(text):
    if text == None and text == '':
        return False, text, 'Ошибка'
    else:
        return True, text, 'Пустое значение не принимается'

def validate_ref(data):
    cursor.execute(
        "SELECT * FROM {0} WHERE code = '{1}' LIMIT 1".format(data[2], data[0]))
    ref_name = cursor.fetchall()
    if len(ref_name) == 1:
        return True, data[0], 'Принято'
    else:
        return False, data[0], 'Такого кода нет в справочнике'

def validate_line(data):
    tom = {
        1: not_empty,
        2: is_number,
        3: validate_ref,
        4: validate_time,
        5: validate_date,
        6: validate_datetime
    }
    for i in data:
        if not_empty(i[0]):
            if i[1] == 3:
                status, check_result, description = validate_ref(i)
                if status != True:
                    return False, check_result, description
            else:
                status, check_result, description = tom[i[1]](i[0])
                if status != True:
                    return False, check_result, description
        else:
            continue

    result = [i[0] for i in data]
    return True, result, 'Принято'

def xlfile(m):
    style0 = xlwt.easyxf('font: name Times New Roman, color-index red, bold on', num_format_str='#,##0.00')
    style1 = xlwt.easyxf(num_format_str='D-MMM-YY')

    wb = xlwt.Workbook()
    ws = wb.add_sheet('A Test Sheet')

    ws.write(0, 0, 1234.56, style0)
    ws.write(1, 0, m, style1)
    ws.write(2, 0, 1)
    ws.write(2, 1, 1)
    ws.write(2, 2, 123424)

    path_adn_file = constants.ERROR_FOLDER + 'example.xls'

    wb.save(path_adn_file)

class data_loading():

    def __init__(self):
        self.line = None
        self.id = line[0]
        self.data_area_id = line[1]
        self.filename = line[2]
        self.type = line[3]
        self.user = line[4]

    # Функция возвращает либо ошибку с неверным значением, либо набор значений, которые можно записать в базу
    def head_check(self,  in_base, in_file):

        # Порядковые номера столбцов в файле, которые ожидаются для обработки в базе
        in_file_indexes = []

        # Проверка полного набора колонок в файле
        for i in in_base:
            if i[1] in in_file:
                in_file_indexes.append(in_file.index(i[1]))
            else:
                return False, i[1], 'Этой колонки не хвататет в загружаемых данных'

        return True, in_file_indexes


    # Запуск обработки
    def start(self):
        # Открывается сохраненный файл
        rb = xlrd.open_workbook(constants.UPLOAD_FOLDER + self.filename)
        sheet = rb.sheet_by_index(0)

        # Содержание файла
        in_table = range(sheet.nrows)

        # Набор колонок из файла
        row = sheet.row_values(in_table[0])

        # Набор колонок из базы
        cursor.execute("SELECT id, column_name, type, ref_id FROM measures WHERE data_area_id = '{0}'".format(self.data_area_id))
        measures = cursor.fetchall()

        # Проверка структуры в файле
        head_check = self.head_check(measures, row)
        if head_check[0] != True:
            return head_check

        # Набор справочников требуемых для проверки
        ref_names = {}
        for i in measures:
            if i[3] != None:
                cursor.execute(
                    "SELECT data FROM refs WHERE id = '{0}'".format(i[3]))
                ref_name = cursor.fetchall()[0][0]
                ref_names.update({i[0]: ref_name})

        # Создать файл для записи ошибок

        # Загрузка данных из файла
        for rownum in in_table:
            # Перебор строк
            if rownum >= 1:
                # Строка в файле
                row = sheet.row_values(rownum)

                # Получение нужного набора данных из строки
                bdline = []
                for i in head_check[1]:
                    item = []
                    item.append(row[i])
                    item.append(measures[head_check[1].index(i)][2])
                    ref_table = measures[head_check[1].index(i)][3]
                    if ref_table != None and ref_table != '':
                        item.append(ref_names[measures[head_check[1].index(i)][0]])
                    else:
                        item.append(None)
                    bdline.append(item)

                # Проверка данных строки на соответсвие формату
                status, result, description = validate_line(bdline)
                if status:
                    print(result)
                else:
                    print('Ошибка в строке номер: ', rownum + 1, description, result)

        # Удаление загруженного файла
        #os.remove(constants.UPLOAD_FOLDER + self.filename)

        # Обновление статуса предметной области и измерений, сохранение и закрытие файла с ошибками



# Позиция в очереди
line = (17, 24, '1_23_test0.xlsx', 1, 1, '2018-10-18 16:29:44.278127')




kaa = data_loading()
kaa.line = line
kaa.start()
