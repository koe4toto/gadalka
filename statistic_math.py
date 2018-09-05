import numpy as np, scipy.stats as sci
import json

# Статистики ряда
class Series:

    def __init__(self, line):

        # Список значений
        self.line = np.array(line)

        # Частотное распределение
        self.freq = sci.itemfreq(self.line)

        # Список значений игнорируя 0
        self.nonzero = self.line.ravel()[np.flatnonzero(self.line)]


    # Список статистик
    def stats_line(self):

        sline = {
            # Размер выборки
            'Размер выборки': len(self.line),

            # Сумма
            'Сумма': np.sum(self.line),

            # Минимум
            'Минимум': np.min(self.line),

            # Максимум
            'Максимум': np.max(self.line),

            # Максимальная частота
            'Максимальная частота': np.max(self.freq),

            # Размах
            'Размах': np.ptp(self.line),

            # Среднее
            'Среднее': np.mean(self.line),

            # Медиана
            'Медиана': np.median(self.line),

            # Мода
            'Мода': sci.mode(self.line)[0][0],

            # Средневзвешенное
            'Средневзвешенное': np.average(self.line),

            # Стандартное отклонение
            'Стандартное отклонение': np.std(self.line),

            # Дисперсия
            'Дисперсия': np.var(self.line),

            # Стандартная ошибка средней
            'Стандартная ошибка средней': sci.sem(self.line),

            # Межквартильный размах
            'Межквартильный размах': sci.iqr(self.line)

        }
        return sline


    # Распределение частот и вероятности для графика в интерфейсе
    def freq_line_view(self, limit):
        lenfreq = len(self.freq)
        pop = []
        if lenfreq >= limit:
            i = 0
            step = int(lenfreq / limit)
            while i < lenfreq:
                if self.freq[i][0]<10:
                    pop.append([self.freq[i][0], self.freq[i][1], 0])
                elif self.freq[i][0]>=10:
                    pop.append([self.freq[i][0], self.freq[i][1], self.freq[i][1]])
                elif self.freq[i][0] > 80:
                    pop.append([self.freq[i][0], self.freq[i][1], 0])
                i += step
            return pop
        else:
            for i in self.freq:
                if i[0]<10 or i[0] > 80:
                    pop.append([i[0], i[1], None])
                elif i[0]>10:
                    pop.append([i[0], i[1], i[1]])
            return json.dumps(pop)

    # Математическое ожидание для среднего
    def mbayes(self, a):
        mean, var, std = sci.bayes_mvs(self.line, alpha=a)
        return mean

    # Вероятность событий: для дискредной величины, для неприрывной
    def probability(self, DataQualitative=True, x1=None, x2=None):
        qlen = len(self.freq)
        if DataQualitative == None:
            DataQualitative = True
        if x1 == None:
            x1 = self.freq.min(axis=0)[0]
        if x2 == None:
            x2 = self.freq.max(axis=0)[0]
        if DataQualitative == True:
            Qualitative = np.sum([i[1]/qlen for i in self.freq if i[0] >= x1 and i[0] <= x2])
        else:
            QuaAll = np.trapz([i[1]/qlen for i in self.freq], [i[0] for i in self.freq])
            QuaLim = np.trapz([i[1]/qlen for i in self.freq if i[0] >= x1 and i[0] <= x2],
                              [i[1]/qlen for i in self.freq if i[0] >= x1 and i[0] <= x2])
            Qualitative = QuaLim / QuaAll
        return Qualitative


# Парные модели
class Pairs:

    def __init__(self, x, y):

        # Первый ряд
        self.x = np.array(x)

        # Второй ряд
        self.y = np.array(y)


    # Линейная модель
    def linereg(self):
        slope, intercept, r_value, p_value, std_err = sci.linregress(self.x, self.y)
        return slope, intercept, r_value, p_value, std_err

    # Степенная модель
    def powerreg(self):

        # Замена переменных
        x1 = np.log10(self.x)
        y1 = np.log10(self.y)

        # Вычисление коэфициентов
        slope1, intercept, r_value, p_value, std_err = sci.linregress(x1, y1)

        # Замена коэфициентов
        slope = np.power(10, slope1)

        return slope, intercept, r_value, p_value, std_err

    # Гиперболическая модель 1
    def hyperbolicreg1(self):
        # Замена переменных
        x1 = 1/self.x

        # Вычисление коэфициентов
        slope, intercept, r_value, p_value, std_err = sci.linregress(x1, self.y)

        return slope, intercept, r_value, p_value, std_err

    # Гиперболическая модель 2
    def hyperbolicreg2(self):
        # Замена переменных
        y1 = 1/self.y

        # Вычисление коэфициентов
        slope, intercept, r_value, p_value, std_err = sci.linregress(self.x, y1)

        return slope, intercept, r_value, p_value, std_err

    # Гиперболическая модель 3
    def hyperbolicreg3(self):
        # Замена переменных
        x1 = 1 / self.x
        y1 = 1/self.y

        # Вычисление коэфициентов
        slope, intercept, r_value, p_value, std_err = sci.linregress(x1, y1)

        return slope, intercept, r_value, p_value, std_err

    # Логарифмическая модель
    def logarithmic(self):
        # Замена переменных
        x1 = np.log10(self.x)

        # Вычисление коэфициентов
        slope, intercept, r_value, p_value, std_err = sci.linregress(x1, self.y)

        return slope, intercept, r_value, p_value, std_err

    # Экспоненциальная модель
    def exponential(self):
        # Замена переменных
        y1 = np.exp(self.y)

        # Вычисление коэфициентов
        slope1, intercept, r_value, p_value, std_err = sci.linregress(self.x, y1)

        # Замена коэфициентов
        slope = np.exp(slope1)

        return slope, intercept, r_value, p_value, std_err



    # Поток рассчета парных моделей
    def pair_regressions(self):
        # Получить данные о пользователе, в данных которого надо искать связи
        # Проверить есть ли чего анализировать
            # Если нет, то закрыть поток или процесс
            # Если да, то проверить есть ли пары без результатов анализа
                # Если нет, то начать анализировать заново пару с самой ранней датой обновления
                # Если да, то начать анализировать первую в списке
                    # Получить выборку из базы
                    # Найти коэф моделей коэф корреляции проверку достоверности
                    # Записать результаты анализа
                    # Запустить данную процедуру заново
        print('Вот')


















'''
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


'''






