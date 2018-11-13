import constants
from database import data_conn, data_cursor, cursor, conn

# Проверка формата загружаемого файлв
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in constants.ALLOWED_EXTENSIONS

# Поиск совпадений в списке
def looking(item, list):
    for i in list:
        if i[1] == item:
            return i

def sqllist(row):
    rows = str(row[0])
    for i in row:
        if row.index(i) > 0:
            if i != '':
                rows += ', ' + str(i)
            else:
                rows += ', None'
    return rows

def sqlvar(row):
    rows = "'" +str(row[0]) + "'"
    for i in row:
        if row.index(i) > 0:
            if i != '':
                rows += ", '" + str(i) + "'"
            else:
                rows += ", 'None'"
    return rows

# Получение данных по идентификатору меры
def numline(id, len = None):

    # Получение данных о мере
    cursor.execute("SELECT * FROM measures WHERE id = '{0}'".format(id))
    the_measure = cursor.fetchall()
    print('Измерения: ', the_measure)

    cursor.execute("SELECT * FROM data_area WHERE id = '{0}'".format(the_measure[0][3]))
    data_a = cursor.fetchall()[0]
    print('Данные: ', data_a)

    database_table = data_a[5]
    print('Название таблицы: ', database_table)

    # Данные
    try:
        data_cursor.execute('SELECT column_name FROM information_schema.columns WHERE table_name=%s;', [database_table])
        tc = data_cursor.fetchall()

        if str(tc) == '[]':
            return 'Указаной таблицы нет в базе данных'
        else:
            # Получение данных
            try:
                if len != None:
                    data_cursor.execute('''select ''' + the_measure[0][1] +
                                ''' from (select row_number() over (order by ''' + the_measure[0][1] +
                                ''') num, count(*) over () as count, ''' + the_measure[0][1] +
                                ''' from ''' + database_table + ''' p)A 
                                where case when count > ''' + str(len) + ''' then num %(count/''' + str(len) +
                                ''') = 0 else 1 = 1 end;''')
                    measure_data = data_cursor.fetchall()
                else:
                    cursor.execute('select ' + the_measure[0][1] +' from '+ database_table+ ' order by ' + the_measure[0][1] +' DESC;' )
                    measure_data = cursor.fetchall()

                # Данные в список
                mline = [float(i[0]) for i in measure_data]
                return mline

            except:
                pre = []
                stats = []
                return 'Нет данных'
    except:
        the_measure = None
        return 'Нет подключения'


