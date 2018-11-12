import threading
from database import data_conn, data_cursor
import loading_from_file

# Переменная для потока
t = None

# Проверка наичия задачи в очереди
def check ():
    global t
    data_cursor.execute('''SELECT * FROM data_queue LIMIT 1;''')
    result = data_cursor.fetchall()
    if len(result) < 1:
        # Если задач нет, то запускается поток по таймеру
        t = threading.Timer(2.0, check)
        t.start()
    else:
        # Если задача есть, то идентификатор задачи отправляется в обработчик
        id = str(result[0][0])
        task(result)

# Отработка задачи
def task(result):
    global t

    id = str(result[0][0])
    # Исполнение задачи
    case = loading_from_file.data_loading()
    case.id = result[0][0]
    case.data_area_id = result[0][1]
    case.filename = result[0][2]
    case.type = result[0][3]
    case.user = result[0][4]
    case.start()

    # Запуск проверки наличия новой задачи
    if t == None:
        check()
    else:
        t.cancel()
        check()


check()