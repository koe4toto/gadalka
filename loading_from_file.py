import constants
import xlrd
import database as db
import datetime
import xlwt
import os

cursor = db.cursor
conn = db.conn
data_cursor = db.data_cursor
data_conn = db.data_conn

# Проверка даты
def validate_date(date):
    try:
        datetime.datetime.strptime(date, '%Y-%m-%d')
        return True, date, 'Принято'
    except ValueError:
        return False, date, 'Не верный формат даты'

# Проверка времни
def validate_time(time):
    try:
        datetime.datetime.strptime(time, '%H:%M:%S')
        return True, time, 'Принято'
    except ValueError:
        return False, time, 'Не верный формат времени'

# Проверка даты и времени
def validate_datetime(datetime):
    try:
        datetime.datetime.strptime(datetime, '%Y-%m-%d %H:%M:%S')
        return True, datetime, 'Принято'
    except ValueError:
        return False, datetime, 'Не верный форма времени'

# Проверка числа
def is_number(number):
    try:
        float(number)
        return True, number, 'Принято'
    except ValueError:
        return False, number, 'Не верный формат данных'

# Проверка не пустое ли значение
def not_empty(text):
    if text == None and text == '':
        return False, text, 'Ошибка'
    else:
        return True, text, 'Пустое значение не принимается'

# Проверка соответствия значению справочника
def validate_ref(data):
    data_cursor.execute(
        '''SELECT * FROM {0} WHERE code = '{1}' LIMIT 1;'''.format(data[2], data[0]))
    ref_name = cursor.fetchall()
    if len(ref_name) == 1:
        return True, data[0], 'Принято'
    else:
        return False, data[0], 'Такого кода нет в справочнике'

# Проверка строки
def validate_line(data):
    tom = {
        1: is_number,
        2: not_empty,
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

# Редактирование предметной области
def update_data_area_status(status, log_id):
    cursor.execute(
        '''
        UPDATE data_log SET 
            status='{0}'
        WHERE id='{1}';
        '''.format(status, log_id)
        )
    conn.commit()


# Функция возвращает либо ошибку с неверным значением, либо набор значений, которые можно записать в базу
def head_check(in_base, in_file):

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
def start(id, data_area_id, log_id, filename, type):
    # Обновление статуса предметной области и измерений
    status = '3'
    update_data_area_status(status, log_id)

    # Открывается сохраненный файл
    rb = xlrd.open_workbook(constants.UPLOAD_FOLDER + filename)
    sheet = rb.sheet_by_index(0)

    # Содержание файла
    in_table = range(sheet.nrows)

    # Набор колонок из файла
    row = sheet.row_values(in_table[0])

    # Набор колонок из базы
    cursor.execute(
        "SELECT id, column_name, type, ref_id FROM measures WHERE data_area_id = '{0}'".format(data_area_id))
    measures = cursor.fetchall()

    # Проверка структуры в файле
    headcheck = head_check(measures, row)
    if headcheck[0] != True:
        status = '4'
        update_data_area_status(status, log_id)
        return status

    # Набор справочников требуемых для проверки
    ref_names = {}
    for i in measures:
        if i[3] != None:
            cursor.execute(
                "SELECT data FROM refs WHERE id = '{0}'".format(i[3]))
            ref_name = cursor.fetchall()[0][0]
            ref_names.update({i[0]: ref_name})

    # Создание файла для записи ошибок
    style0 = xlwt.easyxf('font: name Times New Roman, color-index red, bold on', num_format_str='#,##0.00')
    style1 = xlwt.easyxf()
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Main')

    # Название таблицы, в которую записывать данные
    db_da = db.data_area()
    table_name = db_da.data_area(data_area_id)[0][5]

    # Удаление данных из таблицы, если идет операция обновления данных
    if type == '1':
        data_cursor.execute(
            '''
            DELETE FROM {0};
            '''.format(table_name)
        )
        data_conn.commit()

    count = 1
    errrors = 0
    done = 0
    # Загрузка данных из файла
    for rownum in in_table:
        # Строка в файле
        row = sheet.row_values(rownum)

        # Получение нужного набора данных из строки
        bdline = []
        for i in headcheck[1]:
            item = []
            item.append(row[i])
            item.append(measures[headcheck[1].index(i)][2])
            ref_table = measures[headcheck[1].index(i)][3]
            if ref_table != None and ref_table != '':
                item.append(ref_names[measures[headcheck[1].index(i)][0]])
            else:
                item.append(None)
            bdline.append(item)

        # Перебор строк
        if rownum == 0:
            ws.write(rownum, 0, 'Номер строки', style0)
            ws.write(rownum, 1, 'Ошибка', style0)
            ws.write(rownum, 2, 'Знаечние', style0)
        elif rownum >= 1:
            # Проверка данных строки на соответсвие формату
            vlidate_status, result, description = validate_line(bdline)

            if vlidate_status:
                names_to_record = ', '.join(str(e[1]) for e in measures)
                data_to_record = ', '.join("'"+str(e)+"'" for e in result)
                data_cursor.execute(
                    '''
                    INSERT INTO {0} (
                        {1}
                    ) VALUES ({2});
                    '''.format(table_name, names_to_record, data_to_record)
                    )
                data_conn.commit()
                done += 1
            else:
                ws.write(count, 0, rownum + 1, style1)
                ws.write(count, 1, description, style1)
                ws.write(count, 2, result, style1)
                errrors += 1
                count += 1

    # Удаление загруженного файла
    os.remove(constants.UPLOAD_FOLDER + filename)

    # Сохранение и закрытие файла с ошибками
    path_adn_file = constants.ERROR_FOLDER + filename
    wb.save(path_adn_file)

    # Обновление статуса предметной области и измерений
    status = '5'
    update_data_area_status(status, log_id)

    # Сохранение статистики по результатам обработки данных
    cursor.execute(
        '''
        UPDATE data_log SET 
            errors='{0}',
            downloads='{1}'
        WHERE id='{2}';
        '''.format(errrors, done, log_id)
    )
    conn.commit()

    return status

