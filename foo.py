import psycopg2
import constants

def tryit(user):
    conn = psycopg2.connect(database="test111", user="postgres", password="gbcmrf", host="localhost", port="5432")
    cursor = conn.cursor()
    # Сумма
    cursor.execute('SELECT id, name, register_date, description FROM data_area WHERE user_id=%s ORDER BY register_date DESC', [str(user)])
    a = cursor.fetchall()
    return a

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
def numline(id):

    # Подключение к базе данных
    conn = psycopg2.connect(
        database=constants.DATABASE_NAME,
        user=constants.DATABASE_USER,
        password=constants.DATABASE_PASSWORD,
        host=constants.DATABASE_HOST,
        port=constants.DATABASE_PORT)
    cursor = conn.cursor()

    # Получение данных о мере
    cursor.execute("SELECT * FROM area_description WHERE id = %s", [id])
    the_measure = cursor.fetchall()

    cursor.execute("SELECT * FROM data_area WHERE id = %s", [the_measure[0][4]])
    data_a = cursor.fetchall()
    conn.commit()

    database = data_a[0][4]
    database_user = data_a[0][5]
    database_password = data_a[0][6]
    database_host = data_a[0][7]
    database_port = data_a[0][8]
    database_table = data_a[0][9]

    # Данные
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
            return 'Указаной таблицы нет в базе данных'
        else:
            # Получение данных
            try:
                '''
                cur.execute('select ' + the_measure[0][1] + '
                from (select row_number() over (order by pupil) num, count(*) over () as count, '
                            + the_measure[0][1] + '
                            from ' + database_table + ' p)A
                            where case 
                            when count > 100 then num %(count/100) = 0 
                            else 1 = 1 end;')
                measure_data = cur.fetchall()
                '''
                cursor.execute('select ' + the_measure[0][1] +' from '+ database_table+ ' ;' )
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


