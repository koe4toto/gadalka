import threading

count = 0
t = None

def check (i):
    global t, count
    if i < 5:
        t = threading.Timer(2.0, task)
        t.start()
    else:
        count = 0
        print('Заново!')
        check(count)


def task():
    global t, count
    count += 1
    text = 'Привет, букет!!!'
    print(text)
    t.cancel()
    check(count)

check(count)