import threading
from database import queue_conn, queue_cursor
from model_calculation import primal_calc
from loading_from_file import start

# Переменная для потока
t = None

# Проверка наичия задачи в очереди
def check ():
    global t
    queue_cursor.execute('''SELECT * FROM data_queue WHERE status = '1' LIMIT 1;''')
    result = queue_cursor.fetchall()
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
    log_id = result[0][2]
    filename = result[0][3]
    type = result[0][4]

    # Обновление статуса задачи
    queue_cursor.execute(
        '''
        UPDATE data_queue 
        SET status='2'
        WHERE id='{0}';
        '''.format(id)
    )
    queue_conn.commit()

    # Проверка и загрузка данных
    loading = start(id, data_area_id, log_id, filename, type)

    # Проверка гипотиз
    # TODO запускать рассчет моделей, только если есть имерения соответсвующего типа
    if loading == '5':
        primal_calc(data_area_id, log_id)

        # Расчет многомерных моделей


    # Удаление отработаной задачи
    queue_cursor.execute(
        '''
        DELETE 
        FROM 
            data_queue 
        WHERE id=%s;
        '''.format(id)
    )
    queue_conn.commit()

    # Запуск проверки наличия новой задачи
    if t == None:
        check()
    else:
        t.cancel()
        check()

check()