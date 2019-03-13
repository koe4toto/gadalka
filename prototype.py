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
from clickhouse-client-master.client import ClickHouseClient
from errors import Error as ClickHouseError

def on_progress(total, read, progress):
    print(total,read,progress)

try:
    client = ClickHouseClient('http://ch00.fin.adfox.ru:8123/', on_progress=on_progress, user='api', password='apipass')
    query = 'SELECT date FROM adfox.dist_elog WHERE date > toDate(0)'
    result = client.select(query, send_progress_in_http_headers=1)
    print(result.data)
except ClickHouseError as e:
    print(e)
except Exception as e:
    print(e)