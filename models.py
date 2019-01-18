from flask import Blueprint, render_template, flash, redirect, url_for, session, request
from decorators import is_logged_in
import constants
import foo
import json
import numpy as np
import statistic_math as sm
import database as db
import itertools
import datetime
from model_calculation import take_lines

# Мои модули
from forms import *
from statistic_math import Series

mod = Blueprint('models', __name__)

# работа с базой данных
db_measures = db.measures()
db_data_area = db.data_area()

conn = db.conn
cursor = db.cursor

data_conn = db.data_conn
data_cursor = db.data_cursor


# Пары
@mod.route("/pair_models")
def pair_models():
    # Список пар
    cursor.execute(
        '''SELECT *
            FROM (
                SELECT
                    h.name, 
                    ml.r_value,
                    a1.description,
                    a2.description,
                    ml.area_description_1, 
                    ml.area_description_2,
                    ml.id, 
                    ml.hypothesis,
                    row_number() OVER (PARTITION BY area_description_1::text || area_description_2::text ORDER BY abs(to_number(r_value, '9.999999999999')) DESC)  AS rating_in_section
                FROM 
                    math_models ml
                INNER JOIN 
                    measures a1 on ml.area_description_1 = a1.id
                INNER JOIN 
                    measures a2 on ml.area_description_2 = a2.id
                INNER JOIN 
                    hypotheses h on ml.hypothesis = h.id
                WHERE 
                    r_value != 'None'
                ORDER BY 
                    rating_in_section
            ) counted_news
            WHERE rating_in_section <= 1
            ORDER BY abs(to_number(r_value, '9.999999999999')) DESC;
            ''')
    list = cursor.fetchall()
    return render_template('pair_models.html', list=list)

# Пара
@mod.route("/pair/<string:id1>/<string:id2>/<string:model_id>")
def pair(id1, id2, model_id):
    list = [id1, id2]
    pop = [[id1, id2, 'Модель']]

    # Получение данных о модели
    xy, database_table, database_id = take_lines(id1, id2, limit=500)
    XY = np.array(xy)
    x = [float(i[0]) for i in XY]
    y = [float(i[1]) for i in XY]
    cursor.execute('''SELECT * FROM math_models WHERE id='{0}';'''.format(model_id))
    model = cursor.fetchall()

    # Список моделей пары
    alt_models = db.measures()
    list_models = alt_models.model(id1, id2)

    # Параметры пары
    cursor.execute('''SELECT * FROM measures WHERE id='{0}' OR id='{1}';'''.format(id1, id2))
    maesures = cursor.fetchall()

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

# Многомерные модели
@mod.route("/complex_models")
def multiple_models():
    cursor.execute(
        '''
        SELECT * FROM complex_models WHERE type = 1 LIMIT 5;
        '''
    )
    auto_models = cursor.fetchall()

    cursor.execute(
        '''
        SELECT * FROM complex_models WHERE type = 2 LIMIT 5;
        '''
    )
    user_models = cursor.fetchall()
    return render_template('complex_models.html', auto_models=auto_models, user_models=user_models)