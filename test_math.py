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