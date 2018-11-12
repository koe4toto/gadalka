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
        task(result)

# Отработка задачи
def task(result):
    global t

    id = result[0][0]
    data_area_id = result[0][1]
    filename = result[0][2]
    type = result[0][3]

    fin = loading_from_file.start(id, data_area_id, filename, type)

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
    print(fin)
    
    # Запуск проверки наличия новой задачи
    if t == None:
        check()
    else:
        t.cancel()
        check()


check()