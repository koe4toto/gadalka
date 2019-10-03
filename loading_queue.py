import threading
import model_calculation as mc
from loading_from_file import start
import databases.db_queue as db_queue

# Переменная для потока
t = None

# Проверка наичия задачи в очереди
def check ():
    global t
    # Выбирается задача
    result = db_queue.task()
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
    status = 2

    # Обновление статуса задачи
    db_queue.update_task_status(id, status)

    # Проверка и загрузка данных из файла
    loading = start(id, data_area_id, log_id, filename, type)

    # Проверка гипотиз и расчет статистик
    if loading == '5':

        # Расчет статистик измерений для новой выборки
        mc.measure_stats(data_area_id, log_id, 1)

        # Расчет статистик измерений для всей выборки
        mc.measure_stats(data_area_id, log_id, 2)

        # TODO реализовать расчет и сохранение частотныого распределения
        # Расчет и сохранение частотных характеристик параметров
        mc.measure_freqs(data_area_id, log_id)

        # TODO нужно обработать ошибку расчета моделей и поставить конечный статус
        mc.primal_calc(data_area_id, log_id)

        # Расчет многомерных моделей
        mc.multiple_models_auto_calc()

    # Удаление отработаной задачи
    db_queue.delete_task_by_id(id)

    # Запуск проверки наличия новой задачи
    if t == None:
        check()
    else:
        t.cancel()
        check()

check()