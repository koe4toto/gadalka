import xlrd
import os
import psycopg2
from datetime import datetime

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



line = [i+1 for i in range(200)]
pre = 10

print(len(line))
if len(line) >= pre:
    i = 0
    pop = []
    while i < len(line):
        pop.append(line[i])
        i += int(len(line) / pre)
    print(pop)
else:
    print('Не получилось')
