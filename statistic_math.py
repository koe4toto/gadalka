import psycopg2, numpy as np


# Указываем название файла базы данных
conn = psycopg2.connect(database="test111", user="postgres", password="gbcmrf", host="localhost", port="5432")
cursor = conn.cursor()

# Сумма
cursor.execute('SELECT SUM(statisticdata) FROM statdata')
Summa = cursor.fetchall() [0][0]
print('Сума:', Summa)

# Объём выборки
cursor.execute('SELECT COUNT(statisticdata) FROM statdata')
SampleSize = cursor.fetchall() [0][0]
print('Объём выборки:', SampleSize)

# Минимум
cursor.execute('SELECT MIN(statisticdata) FROM statdata')
Minimum = cursor.fetchall() [0][0]
print('Минимум:', Minimum)

# Максимум
cursor.execute('SELECT MAX(statisticdata) FROM statdata')
Maximum = cursor.fetchall() [0][0]
print('Максимум:', Maximum)


# Добавление выборки в список
cursor.execute('SELECT * FROM statdata ORDER BY statisticdata')
mi = cursor.fetchall()


# Выборка уникальных значений
cursor.execute('SELECT DISTINCT statisticdata FROM statdata ORDER BY statisticdata')
di = cursor.fetchall()


cursor.close()
conn.close()

# Ряд агрегатов
OneList =[i[1] for i in mi]
#print('Ряд агрегатов:', OneList)


# Ряд уникальных агрегатов
UniqueList = [i[0] for i in di]
#print('Ряд уникальных агрегатов:', UniqueList)


# Частотное распределение
FashionTrand = []
for i in di:
    FashionTrand.append((i[0], OneList.count(i[0]), OneList.count(i[0]) / SampleSize))
print('Частотное рапределение: ', FashionTrand)
# Создается матрицу для рассчета коэффициентов моделей
Xaxis = []
Yaxis = []
for i in FashionTrand:
    Xaxis.append(float(i[0]))
    Yaxis.append(float(i[1]))



# Максимальная частота
MaxFrequency = max([i[1] for i in FashionTrand])
Fashion = FashionTrand[[i[1] for i in FashionTrand].index(MaxFrequency)][0]
print('Мода: ', Fashion)
print('Максимальная частота: ', MaxFrequency)


# Размах
swipe = Maximum - Minimum
print('Размах:', swipe)


# Среднее
Secondary = np.mean(OneList)
print('Среднее:', Secondary)


# Медиана
Median = np.median(UniqueList)
print('Медиана:', Median)


# Квартильный размах
def MathQuartile (x):
    if x % 4 >= 2:
        return x // 4 + 1
    else:
        return x // 4

Quartile = MathQuartile(SampleSize)
IQR = OneList [Quartile*3] - OneList [Quartile*2]
print('Квартильный размах:', IQR)

# Выбросы
MinDischarge = (OneList [Quartile*2] - IQR*1.5, OneList [Quartile*3] + IQR*1.5)
MaxDischarge = (OneList [Quartile*2] - IQR*3, OneList [Quartile*3] + IQR*3)

MinDischargeCount = 0
for i in OneList:
    if i < OneList [Quartile*2] - IQR*1.5 or i > OneList [Quartile*3] + IQR*1.5:
        MinDischargeCount += 1

MaxDischargeCount = 0
for i in OneList:
    if i < OneList [Quartile*2] - IQR*3 or i > OneList [Quartile*3] + IQR*3:
        MaxDischargeCount += 1

print('Минимальные границы выбросов: ', MinDischarge[0], '...', MinDischarge[1])
print('Максимальные границы выбросов: ', MaxDischarge[0], '...', MaxDischarge[1])

print('Количество умеренных выбросов: ', MinDischargeCount - MaxDischargeCount)
print('Количество выбросов: ', MaxDischargeCount)


# Дисперсия
Dispersion = np.var(OneList)
print('Дисперсия: ', Dispersion)


# Стандартное отклонение
StandardDeviation = np.std(OneList)

print('Стандартное отклонение: ', StandardDeviation)


# Коэффициент вариаци
try:
    СoefficientOfVariation = StandardDeviation/Secondary
except ZeroDivisionError:
    СoefficientOfVariation = None
    print('Ошибка. Нет данных для обработки.')
print('Коэффициент вариации: ', СoefficientOfVariation)


# Асимметрия
try:
    Asymmetry = (Secondary - Median)/StandardDeviation
except ZeroDivisionError:
    Asymmetry = None
    print('Ошибка. Нет данных для обработки.')
print('Асимметрия: ', Asymmetry)


# Вероятность событий: для дискредной величины, для неприрывной
def probability(data, DataQualitative = True, x1=None, x2=None):
    if DataQualitative == None:
        DataQualitative = True
    if x1 == None:
        x1 = min([i[0] for i in data])
    if x2 == None:
        x2 = max([i[0] for i in data])
    if DataQualitative == True:
        Qualitative = np.sum([i[2] for i in data if i[0]>=x1 and i[0]<=x2])
    else:
        QuaAll = np.trapz([i[2] for i in data], [i[0] for i in data])
        QuaLim = np.trapz([i[2] for i in data if i[0]>=x1 and i[0]<=x2], [i[0] for i in data if i[0]>=x1 and i[0]<=x2])
        Qualitative = QuaLim/QuaAll
    return Qualitative

print('Вероятность в заданном промежутке: ', probability(FashionTrand, True, -3, 54))

# Математическое ожидание: для дискредной величины, для неприрывной (СЛОЖНА!!)
def MathExpect(data, Probability):
    xox = sorted([i[0] for i in data])
    c0 = 0
    bottom = probability(data, True, xox[0], xox[c0])
    while bottom <= (1 - Probability) / 2:
        c0 += 1
        bottom = probability(data, True, xox[0], xox[c0])
    if bottom >= (1 - Probability) / 2:
        c0 -= 1
        bottom = probability(data, True, xox[0], xox[c0])

    c1 = len(xox)-1
    top = probability(data, True, xox[c1], xox[len(xox)-1])
    while top <= (1 - Probability) / 2:
        c1 -= 1
        top = probability(data, True, xox[c1], xox[len(xox)-1])
    if top >= (1 - Probability) / 2:
        c1 += 1
        top = probability(data, True, xox[c1], xox[len(xox)-1])

    # Нижний уровень доверительного интервала
    low = xox[c0]
    # Верхний уровень доверительного интервала
    up  = xox[c1]
    return low, up


print('Математическое ожидание (пока не в точности соответствует вероятности в заданном проемежутке): ', MathExpect(FashionTrand, 0.90))
# Выбор модели


# Проверка линейной модели y = b1*x + b0
def LineModel(x, y):
    # Это рабочая схема
    # Перобразовывает ряд в матрицу для поиска коэффициентов
    A = np.vstack([x, np.ones(len(x))]).T

    # При вызове метода лучше придерживаться этого синтаксиса: linalg.lstsq(x, y, rcond=-1)
    b1, b0 = np.linalg.lstsq(A, np.array(y), rcond=-1)[0]
    # Показания по модели
    y1 = np.array([b1 * i + b0 for i in x])
    x1 = np.array([(i - b0)/b1 for i in y])

    # Коэффициент корреляции Пирсона
    kp = np.corrcoef(y,y1) [0,1]

    # Оценка статистической значимости
    si = kp * np.sqrt(SampleSize-2)/np.sqrt(1-kp**2)

    return b1, b0, 'Линейниая зависимость', kp, si, x1, y1


B1 = [LineModel(Xaxis, Yaxis)[0], LineModel(Xaxis, Yaxis)[1], LineModel(Xaxis, Yaxis)[2], LineModel(Xaxis, Yaxis)[3], LineModel(Xaxis, Yaxis)[4]]

print('Коэффициенты линейной модели:', '{:f}'.format(B1[0]), '{:f}'.format(B1[1]), B1[2], '{:f}'.format(B1[3]), '{:f}'.format(B1[4]))










