import constants
import xlrd
import datetime
import xlwt
import os
import psycopg2
import databases.db_app as db_app
import databases.db_data as db_data


# Првоерка наличия ожидаемых колонок
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
    db_app.update_data_area_status(status, log_id)

    # Открывается сохраненный файл
    rb = xlrd.open_workbook(constants.UPLOAD_FOLDER + filename)
    sheet = rb.sheet_by_index(0)

    # Содержание файла
    in_table = range(sheet.nrows)

    # Набор колонок из файла
    row = sheet.row_values(in_table[0])

    # Набор колонок из базы
    measures = db_app.select_columns_from_measures(data_area_id)

    # Проверка структуры в файле
    headcheck = head_check(measures, row)
    if headcheck[0] != True:
        status = '4'
        db_app.update_data_area_status(status, log_id)
        return status

    # Набор справочников требуемых для проверки
    ref_names = {}
    for i in measures:
        if i[3] != None:
            ref_name = db_app.select_ref_name(i[3])
            ref_names.update({i[0]: ref_name})

    # Создание файла для записи ошибок
    style0 = xlwt.easyxf('font: name Times New Roman, color-index red, bold on', num_format_str='#,##0.00')
    style1 = xlwt.easyxf()
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Main')

    # Название таблицы, в которую записывать данные
    db_da = db_app.data_area(data_area_id)
    table_name = db_da[0][5]
    # Максимальное количество хранимых загрузок
    limit = db_da[0][7]

    # Удаление данных из таблицы, если идет операция обновления данных
    if type == '1':
        db_data.delete_data_from_olap(table_name)
    else:
        # Удление лишних данных в оперативном хранилище
        db_data.delete_oldest_partitions(table_name, limit)
        pass

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
            # Выбирается значение нужной колонки в исходных данных
            item.append(row[i])
            # Выбирается тип данных
            item.append(measures[headcheck[1].index(i)][2])
            # Первод даты в формат для записи в базу
            if item[1] == 5 and rownum >= 1:
                try:
                    mi = datetime.datetime(*xlrd.xldate_as_tuple(item[0], rb.datemode))
                    bdline.append([mi, '5'])
                except:
                    bdline.append([None, '5'])
            else:
                bdline.append(item)

        # TODO Реализовать проверку наличия свободного места в общем наборе данных

        # Запись данных
        if rownum == 0:
            ws.write(rownum, 0, 'Номер строки', style0)
            ws.write(rownum, 1, 'Ошибка', style0)
        elif rownum >= 1:
            result = []
            for t in bdline:
                result.append(t[0])
            names_to_record = ', '.join(str(e[1]) for e in measures)
            data_to_record = ', '.join("'" + str(e) + "'" for e in result)
            try:
                db_data.insret_data_to_olap(table_name, names_to_record, data_to_record, log_id)
                done += 1
            except psycopg2.Error as er:
                db_data.conn.rollback()
                ws.write(count, 0, rownum + 1, style1)
                ws.write(count, 1, str(er.diag.message_primary), style1)
                errrors += 1
                count += 1

    # Удаление загруженного файла
    os.remove(constants.UPLOAD_FOLDER + filename)

    # Сохранение и закрытие файла с ошибками
    path_adn_file = constants.ERROR_FOLDER + filename
    wb.save(path_adn_file)

    # TODO нужно записать (обновить) статистические таблицы для измерений

    # Обновление статуса предметной области и измерений
    status = '5'
    db_app.update_data_area_status(status, log_id)

    # Сохранение статистики по результатам обработки данных
    db_app.update_data_log_stats(errrors, done, log_id)

    return status

