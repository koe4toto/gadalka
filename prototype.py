import constants
import statistic_math as sm
import tools
import numpy as np
import random
import xlrd
import json
import datetime
import xlwt
import os
import psycopg2
import databases.db_app as db_app
import databases.db_data as db_data
import databases.db_queue as db_queue
from itertools import groupby

'''
Колонки для выгрузки из таблицы tmp_itmc_odli_diagnosis_mart
Только одна колонка соержит количественные данные

SELECT
  order_patient_age
FROM tmp_itmc_odli_diagnosis_mart
LIMIT 10;
'''

'''
Колонки для выгрузки из таблицы tmp_itmc_odli_observation_mart
Только одна колонка соержит количественные данные

SELECT
  diagnosticreport_patient_age
FROM tmp_itmc_odli_observation_mart
LIMIT 50;

'''

'''
Колонки для выгрузки из таблицы tmp_itmc_iemk_diagnosis_mart_short
Только одна колонка соержит количественные данные

Это похоже качественные данные: 
case_doctor_spec_code,
case_doctor_spec_high,
case_doctor_spec_okso

SELECT
  case_patient_age,
  case_doctor_spec_code,
  case_doctor_spec_high,
  case_doctor_spec_okso
FROM tmp_itmc_iemk_diagnosis_mart_short
LIMIT 50;
'''

'''
1. Преобразовывать качественные данные в количественные. 
Каким-то образом. Мало получится агрегатов. За три месяца около 100 штук на каждую колонку. 
Не очень эффектно может получиться.

2. Реализовать статистику качественных рядов. 
Это в принципе полезно. 

'''

