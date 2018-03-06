import xlrd
import os
import psycopg2
from datetime import datetime

# Подключение к базе данных
conn = psycopg2.connect(database="test111", user="postgres", password="gbcmrf", host="localhost", port="5432")
cursor = conn.cursor()

cursor.execute('''SELECT * FROM area_description WHERE data_area_id = '25';''')
descriptions = cursor.fetchall()

desc = tuple([i[6] for i in descriptions if i[6] != None])

prim = [[2,2],[2,28],[2,25],[2,2]]
ref_id = tuple(['25', '28'])
cursor.execute('''SELECT * FROM refs WHERE id in ''' + str(ref_id))
refs_name = cursor.fetchall()

for i in prim:
    if i[1] in [k[0] for k in refs_name]:
        m = [k[1] for k in refs_name if k[0] == i[1]]
        i[1] = m[0]

print(str(ref_id))

if len(desc) >= 1:
    print('Попа')
else:
    print(len(desc))