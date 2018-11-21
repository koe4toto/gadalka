import threading
from database import data_conn, data_cursor
from model_calculation import primal_calc
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
        task(result)

# Отработка задачи
def task(result):
    global t

    id = result[0][0]
    data_area_id = result[0][1]
    filename = result[0][2]
    type = result[0][3]

    loading = loading_from_file.start(id, data_area_id, filename, type)

    if loading == '5':
        primal_calc(data_area_id)

    # Удаление отработаной задачи
    data_cursor.execute(
        '''
        DELETE 
        FROM 
            data_queue 
        WHERE id=%s;
        ''', [result[0][0]]
    )
    data_conn.commit()

    # Запуск проверки наличия новой задачи
    if t == None:
        check()
    else:
        t.cancel()
        check()

check()