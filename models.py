from flask import Blueprint, render_template, flash, redirect, url_for, session, request
from decorators import is_logged_in
import constants
import json
import numpy as np
import statistic_math as sm
import database as db
from model_calculation import take_lines

# Мои модули
import databases.db_app as db_app

mod = Blueprint('models', __name__)

# работа с базой данных
db_measures = db.measures()
db_data_area = db.data_area()

conn = db.conn
cursor = db.cursor

data_conn = db.data_conn
data_cursor = db.data_cursor


# Простые связи
@mod.route("/pair_models")
@is_logged_in
def pair_models():
    return render_template(
        'pair_models.html',
        list=db_app.select_pairs()
    )

# Карточка простой связи
@mod.route("/pair/<string:id1>/<string:id2>/<string:model_id>")
@is_logged_in
def pair(id1, id2, model_id):
    list = [id1, id2]
    pop = [[id1, id2, 'Модель']]

    # Получение данных о модели
    xy, database_table, database_id = take_lines(id1, id2, limit=500)
    XY = np.array(xy)
    x = [float(i[0]) for i in XY]
    y = [float(i[1]) for i in XY]

    # Модель
    model = db_app.select_model(model_id)

    # Список моделей пары
    list_models = db_app.select_pair_models(id1, id2)

    # Параметры пары
    maesures = db_app.select_pairs_measures(id1, id2)

    slope = float(model[0][2])
    intercept = float(model[0][3])

    # Получение данных для графика
    len = 100

    # Получение экземпляра класса обработки данных
    model_data = sm.Pairs(x, y)

    # Справочник гипотез
    hypotheses = {
        1: model_data.linereg_line,
        2: model_data.powerreg_line,
        3: model_data.exponentialreg1_line,
        4: model_data.hyperbolicreg1_line,
        5: model_data.hyperbolicreg2_line,
        6: model_data.hyperbolicreg3_line,
        7: model_data.logarithmic_line,
        8: model_data.exponentialreg2_line
    }

    # Получение данных для графика по модели
    Y = hypotheses[model[0][1]](slope, intercept)

    # Данные собираются в список для отображения
    xy = np.vstack((x, y, Y))
    for_graf = xy.transpose()

    for i in for_graf:
        pop.append([i[0], i[1], i[2]])

    popa = json.dumps(pop, ensure_ascii=False)

    return render_template('pair.html', list=list, for_graf=popa, model=model, list_models=list_models, maesures=maesures)

# Сложные связи
@mod.route("/complex_models")
@is_logged_in
def complex_models():
    return render_template(
        'complex_models.html',
        auto_models=db_app.select_complex_models(1),
        user_models=db_app.select_complex_models(2)
    )

# Карточка сложной связи
@mod.route("/complex_model/<string:model_id>")
@is_logged_in
def complex_model(model_id):
    return render_template(
        'complex_model.html',
        model=db_app.select_complex_model(model_id),
        complex_model_measures=db_app.select_complex_model_measures(model_id),
        pair_models=db_app.select_complex_model_pairs(model_id)
    )