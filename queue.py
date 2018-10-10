import threading
import multiprocessing
from database import data_conn, data_cursor

t = None

def check ():
    global t
    data_cursor.execute('''SELECT * FROM data_queue LIMIT 1;''')
    result = data_cursor.fetchall()
    if len(result) < 1:
        print(result)
        t = threading.Timer(2.0, check)
        t.start()
    else:
        id = str(result[0][0])
        task(id)


def task(result):
    global t
    print('Вот оно: ', result)
    data_cursor.execute(
        '''
        DELETE 
        FROM 
            data_queue 
        WHERE id=%s;
        ''', [result]
    )
    data_conn.commit()

    if t == None:
        check()
    else:
        t.cancel()
        check()


check()