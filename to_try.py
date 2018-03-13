import xlrd
import os
import psycopg2
from datetime import datetime
from statistic_math import Series
import numpy as np, scipy.stats as sci


# Подключение к базе данных
conn = psycopg2.connect(database="test111", user="postgres", password="gbcmrf", host="localhost", port="5432")
cursor = conn.cursor()


cursor.execute('''
    SELECT
        area_description.id,
        area_description.column_name,
        area_description.description,
        area_description.type,
        refs.name,
        area_description.kind_of_metering
    FROM
        area_description
    LEFT JOIN
        refs
    ON
        area_description.ref_id = refs.id
    WHERE
        area_description.data_area_id = '28';''')
pik = cursor.fetchall()

cursor.execute("SELECT * FROM area_description WHERE id = %s", [19])
the_measure = cursor.fetchall()



# Добавление выборки в список
cursor.execute('SELECT job FROM edu_test ORDER BY job')
OneList = [i[0] for i in cursor.fetchall()]

x = [1,2,2,2,3,4,5,6,0]
z = np.array(OneList)

y = z.ravel()[np.flatnonzero(z)]

mi = np.amin(z)
r = np.array([i-mi+1 for i in OneList])
k = sci.hmean(r) + mi - 1
print(sci.mode(OneList))
print(z)
print(k)


