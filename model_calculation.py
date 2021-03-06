from flask import session
import statistic_math as sm
import numpy as np
import constants
import databases.db_app as db_app
import databases.db_data as db_data

# Определение типа измерения и вывод строчки для соответствуующего запроса
def time_to_num(measure):
    if measure[3] == 4 or measure[3] == 5 or measure[3] == 6:
        result = 'EXTRACT(EPOCH FROM {0} )'.format(measure[0])
    else:
        result = measure[0]
    return result

# Данные для анализа
def take_lines (line1, line2, limit=None):

    # Измерения
    try:
        measures = db_app.select_measures_to_lines(line1, line2)
    except:
        return None, False, None

    # Название таблицы, в котрой хранятся данные
    database_table = measures[0][1]
    database_id = measures[0][2]

    x = None
    y = None

    # Расстановка измерений в правильном порядке
    for i in measures:
        if int(i[4]) == int(line1):
            x = i
        if int(i[4]) == int(line2):
            y = i

    me1_alt = time_to_num(x)
    me2_alt = time_to_num(y)

    # Данные
    # Выборка всех данных
    measure_data = db_data.select_data_from_olap(me1_alt, me2_alt, database_table, limit)
    return measure_data, database_table, database_id

def measure_stats(data_area_id, log_id, kind):

    # Измерения
    measures = db_app.select_measures_to_stats(data_area_id)

    # Обработка и сохранение статистик
    for i in measures:

        # TODO сделать проверку про время: time_to_num
        # Статистики средствами БД
        stats = db_data.select_stats_general_line(i[1], i[2], log_id)
        for num, k in enumerate(stats):
            db_app.insert_stats(i[0], log_id, num + 1, kind, k)

# Расчет и сохранение частотных характеристик параметров
def measure_freqs(data_area_id, log_id):
    # Измерения
    measures = db_app.select_measures_to_simple_stats(data_area_id)
    data_area = db_app.data_area(data_area_id)

    olap = data_area[0][5]

    # Вычисление и запись данных о частотах и "вариантах"
    for i in measures:
        if  i[3] == 1:
            db_data.agr_freq_table_for_numeric_measure(olap, i[0], log_id, i[2])
        elif i[3] == 2:
            db_data.agr_freq_table_for_quantitative_measure(olap, i[0], log_id, i[2])
        elif i[3] == 3:
            db_data.agr_freq_table_for_ref_quantitative_measure(olap, i[0], log_id, i[2])
        # TODO сделать расчеты для времени

    # Расчет накопленных частот
    '''
    Select sum(p.val) as sm
    from test p, test v
    where p.id<=v.id
    GROUP BY v.id;
    '''
    pass

# Рассчета свойств модели и запись результатов в базу данных
def search_model(hypothesis, x, y, adid1, adid2):

    # Экземпляр класса обработки данных по парам
    pairs = sm.Pairs(x, y)

    # Справочник гипотез
    hypotheses = {
        1: pairs.linereg,
        2: pairs.powerreg,
        3: pairs.exponentialreg1,
        4: pairs.hyperbolicreg1,
        5: pairs.hyperbolicreg2,
        6: pairs.hyperbolicreg3,
        7: pairs.logarithmic,
        8: pairs.exponentialreg2
    }

    # Рассчета показателей по указанной в базе модели
    slope, intercept, r_value, p_value, std_err = hypotheses[hypothesis]()
    print('Расчеты: ', slope, intercept, r_value, p_value, std_err, pairs.xstat_div, pairs.ystat_div)

    # Сохранение результатов в базу данных. Записываются данные по модели.
    db_app.upgate_math_models(
        slope,
        intercept,
        r_value,
        p_value,
        std_err,
        pairs.xstat_div,
        pairs.ystat_div,
        adid1,
        adid2,
        hypothesis
    )

# Расчте моделей моделей предметной области
def primal_calc(data_area_id, log_id):

    # Список моделей
    model = db_app.select_math_models_by_data_area(data_area_id)

    if len(model) <= 1:
        # Изменить статус предметной области, измерений
        db_app.update_data_area_status('6', log_id)
        return True

    for i in model:

        hypothesis = i[1]
        line_id_1 = i[10]
        line_id_2 = i[11]


        # Получение данных
        try:
            xy, database_table, database_id = take_lines(line_id_1, line_id_2)

            if xy == None:
                status = '4'
            else:
                XY = np.array(xy)
                x = [float(i[0]) for i in XY]
                y = [float(i[1]) for i in XY]


                # Рассчет параметров модели и запись их в базу
                search_model(hypothesis, x, y, line_id_1, line_id_2)
                status = '6'

                # Изменить статус предметной области, измерений
                db_app.update_measures_status(database_id, line_id_1, line_id_2, status)

        except:
            status = '6'
            pass

        # Изменить статус предметной области, измерений
        db_app.update_data_area_status(status, log_id)

# Запись сложной модели в базу
def multiple_models_safe(koef):

    # Выбираются модели по силе связи
    # TODO чтобы не производить этих вычислений лучше сразу делать правильную выборку в базе
    mods = db_app.get_models(koef)
    mods_ids = [[i[6], i[4], i[5]] for i in mods]

    asss = db_app.select_all_associations()

    # Поиск сложных связей
    models = sm.count_measures(asss, mods_ids)

    # Имя модели
    if len(models) > 0:
        for mod in models:
            model_name = 'Модель для {0} измерений: {1}'.format(len(mod[0]), ', '.join([str(i) for i in mod[0]]) )
            model_kind = constants.KIND_OF_MODEL['Сильная связь']
            model_type = constants.TYPE_OF_MODEL['Автоматически расчитанный']

            # Список идентификаторов простых моделей в строку
            ti = ','.join(str(e) for e in mod[1])

            # Сохранение модели
            model_id = db_app.insert_complex_models(model_name, model_type, model_kind, ti)

            for measure in mod[0]:
                # Характеристики измерений модели
                measure_id = measure

                # Сохранение измерений модели
                db_app.insert_complex_model_measures(model_id[0][0], measure_id, model_type)

            for pair in mod[1]:
                # Сохранение измерений модели
                db_app.insert_complex_model_pairs(model_id[0][0], int(pair), model_type)

        return True
    else:
        return False

# Определение сложных связей
def multiple_models_auto_calc():

    # Удаление старых связей
    try:
        db_app.delete_complex_model(constants.TYPE_OF_MODEL['Автоматически расчитанный'])
    except:
        pass

    # Поиск и запись моделей опираясь на текущие данные
    multiple_models_safe(constants.COMPLEX_MODEL_KOEF)

    return True
