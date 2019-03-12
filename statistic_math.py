import numpy as np, scipy.stats as sci
import scipy as sp
import json
import math

# Статистики ряда
class Series:

    def __init__(self, line):

        # Список значений
        self.line = 1.0*np.array(line)

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

    # Список статистик качественных данных
    def stats_qualitative_line(self):
        result = {
            # Размер выборки
            'Размер выборки': len(self.line),

            # Максимальная частота
            'Максимальная частота': np.max(self.freq),

            # Мода
            'Мода': sci.mode(self.line)[0][0]
        }
        return result


    # Распределение частот и вероятности для графика в интерфейсе
    def freq_line_view(self):
        pop = [[i[0], i[1], i[1]] for i in self.freq]
        return json.dumps(pop)

    # Математическое ожидание для среднего
    def mbayes(self, a):
        data = self.line
        n = len(self.line)

        m, se = np.mean(data), sci.sem(data)
        h = se * sp.stats.t._ppf((1 + a) / 2., n - 1)
        return m, m-h, m+h

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

    # Математическое ожидание: для дискредной величины, для неприрывной (СЛОЖНА!!)
    def MathExpect(self, Probability):
        xox = sorted([i[0] for i in self.line])
        c0 = 0
        bottom = self.probability(self.linea, True, xox[0], xox[c0])
        while bottom <= (1 - Probability) / 2:
            c0 += 1
            bottom = self.probability(self.line, True, xox[0], xox[c0])
        if bottom >= (1 - Probability) / 2:
            c0 -= 1
            bottom = self.probability(self.line, True, xox[0], xox[c0])

        c1 = len(xox) - 1
        top = self.probability(self.line, True, xox[c1], xox[len(xox) - 1])
        while top <= (1 - Probability) / 2:
            c1 -= 1
            top = self.probability(self.line, True, xox[c1], xox[len(xox) - 1])
        if top >= (1 - Probability) / 2:
            c1 += 1
            top = self.probability(self.line, True, xox[c1], xox[len(xox) - 1])

        # Нижний уровень доверительного интервала
        low = xox[c0]
        # Верхний уровень доверительного интервала
        up = xox[c1]
        return low, up


# Парные модели
class Pairs:

    def __init__(self, x, y):

        # Первый ряд
        self.x = np.array(x)

        # Второй ряд
        self.y = np.array(y)

        # Смещение распределения для исключения отрицательных и нулевых значений
        self.xstat_div = np.fabs(self.x.min()) + 1
        self.ystat_div = np.fabs(self.y.min()) + 1
        self.x_div = self.x + self.xstat_div
        self.y_div = self.y + self.ystat_div



    # Линейная модель
    def linereg(self):
        slope, intercept, r_value, p_value, std_err = sci.linregress(self.x, self.y)
        return slope, intercept, r_value, p_value, std_err

    # Данные линейной модели
    def linereg_line(self, slope, intercept):
        Y = slope * self.x + intercept
        return Y



    # Степенная модель
    def powerreg(self):

        # Замена переменных
        x1 = np.log10(self.x_div)
        y1 = np.log10(self.y_div)

        # Вычисление коэфициентов
        slope1, intercept, r_value, p_value, std_err = sci.linregress(x1, y1)

        # Замена коэфициентов
        slope = np.power(10, slope1)

        return slope, intercept, r_value, p_value, std_err

    # Данные степенной модели
    def powerreg_line(self, slope, intercept):
        Y = intercept * np.power(slope, self.x)
        return Y



    # Показательная модель 1
    def exponentialreg1(self):

        # Замена переменных
        x1 = self.x_div
        y1 = np.log10(self.y_div)

        # Вычисление коэфициентов
        slope1, intercept, r_value, p_value, std_err = sci.linregress(x1, y1)

        # Замена коэфициентов
        slope = np.power(10, slope1)

        return slope, intercept, r_value, p_value, std_err

    # Данные показательной модели 1
    def exponentialreg1_line(self, slope, intercept):
        Y = slope * np.power(self.x, intercept)
        return Y




    # Гиперболическая модель 1
    def hyperbolicreg1(self):

        # Замена переменных
        x1 = 1/self.x_div

        # Вычисление коэфициентов
        slope, intercept, r_value, p_value, std_err = sci.linregress(x1, self.y_div)

        return slope, intercept, r_value, p_value, std_err

    # Данные гиперболической модели 1
    def hyperbolicreg1_line(self, slope, intercept):
        Y = slope / self.x + intercept
        return Y




    # Гиперболическая модель 2
    def hyperbolicreg2(self):

        # Замена переменных
        y1 = 1/self.y_div

        # Вычисление коэфициентов
        slope, intercept, r_value, p_value, std_err = sci.linregress(self.x_div, y1)

        return slope, intercept, r_value, p_value, std_err

    # Данные гиперболической модели 2
    def hyperbolicreg2_line(self, slope, intercept):
        Y = 1 / (slope * self.x + intercept)
        return Y



    # Гиперболическая модель 3
    def hyperbolicreg3(self):
        # Замена переменных
        x1 = 1/self.x_div
        y1 = 1/self.y_div

        # Вычисление коэфициентов
        slope, intercept, r_value, p_value, std_err = sci.linregress(x1, y1)

        return slope, intercept, r_value, p_value, std_err

    # Данные гиперболической модели 3
    def hyperbolicreg3_line(self, slope, intercept):
        Y = 1 / (slope / self.x + intercept)
        return Y




    # Логарифмическая модель
    def logarithmic(self):
        # Замена переменных
        x1 = np.log10(self.x_div)

        # Вычисление коэфициентов
        slope, intercept, r_value, p_value, std_err = sci.linregress(x1, self.y_div)

        return slope, intercept, r_value, p_value, std_err

    # Данные логарифмической модели
    def logarithmic_line(self, slope, intercept):
        Y = slope * np.log10(self.x) + intercept
        return Y



    # Экспоненциальная модель
    def exponentialreg2(self):
        # Замена переменных
        try:
            y1 = np.exp(self.y_div)
            x1 = self.x_div
            for i in y1:
                if i == np.inf:
                    index, = np.where(y1 == np.inf)
                    y1 = np.delete(y1, [index[0]])
                    x1 = np.delete(x1, [index[0]])

            # Вычисление коэфициентов
            slope1, intercept, r_value, p_value, std_err = sci.linregress(x1, y1)

            # Замена коэфициентов
            slope = np.exp(slope1)
        except:
            slope = None
            intercept = None
            r_value = None
            p_value = None
            std_err = None
        return slope, intercept, r_value, p_value, std_err

    # Данные экспоненциальной модели 2
    def exponentialreg2_line(self, slope, intercept):
        try:
            Y = slope * np.power(self.x * intercept, 2.718)
        except Exception:
            Y = []
        return Y


# Определение множестенной связи
def multiple(models):
    hash = {}

    mms = {}

    model_list = {}
    for num, i in enumerate(models):
        if i[1] not in hash:
            hash.setdefault(i[1], num)
            mms.setdefault(num, [i[1], i[2]])
            model_list.setdefault(num, [i[0]])

        else:
            if i[2] not in mms[hash[i[1]]]:
                mms[hash[i[1]]].append(i[2])
                hash.setdefault(i[2], hash[i[1]])

            if i[0] not in model_list[hash[i[1]]]:
                model_list[hash[i[1]]].append(i[0])

        if i[2] not in hash:
            hash.setdefault(i[2], num)
            if num not in model_list:
                model_list.setdefault(num, [i[0]])
        else:
            if i[0] not in model_list[hash[i[1]]]:
                model_list[hash[i[1]]].append(i[0])

    result = [mms[i] for i in mms if len(mms[i]) > 2]
    models_id = [model_list[i] for i in model_list if len(model_list[i]) > 1]

    return result, models_id


# Поиск рядов ассоциированных измерений и подстановка их в список моделей
def group_associations(associats, mod):
    pair = [[i[1], i[2]] for i in associats]

    # Временнный словарь уникальных измерений
    hash = {}
    hash2 = {}

    # Временнный словарь ассоциированных измерений. Содержит списки без пар.
    result = {}
    for num, i in enumerate(pair):
        if i[0] not in hash:
            hash.setdefault(i[0], num)
            result.setdefault(num, [i[0], i[1]])
            hash2.setdefault(i[0], num)
            hash2.setdefault(i[1], num)
        else:
            result[hash[i[0]]].append(i[1])
            hash2.setdefault(i[1], hash[i[0]])

        if i[1] not in hash:
            hash.setdefault(i[1], num)
            hash2.setdefault(i[1], num)
        else:
            hash[i[0]] = hash[i[1]]
            result[hash[i[1]]].append(i[0])
            hash2.setdefault(i[0], hash[i[0]])

    # Подстановка ассоциаций вместо измерений. Теперь они станут ключём для сбора множественной модели
    # с учетом дополнительных связей
    for num, i in enumerate(mod):
        if i[1] in hash2:
            list1 = result[hash2[i[1]]]
            str1 = ','.join(str(e) for e in list1)
            mod[num][1] = str1

        if i[2] in hash2:
            list1 = result[hash2[i[2]]]
            str1 = ','.join(str(e) for e in list1)
            mod[num][2] = str1

    return mod


# Итоговое получение сложных моделей выраженых в измерениях и простых связях
def count_measures(associations, pairs):
    # Для отчищения от лишних ассоциаций делается плоский список id измерений в выбранных моделях
    pi = [[i[1], i[2]] for i in pairs]
    p_list = np.array(pi)
    flot = p_list.ravel()

    # Избавляемся от ассоциаций, которых нет в списке моделей
    good_ass = []
    for i in associations:
        if i[1] in flot and i[2] in flot:
            good_ass.append(i)

    complex_models, complex_models_id = multiple(group_associations(good_ass, pairs))

    result = []
    for model in complex_models:
        new_model = []
        for i in model:
            item = str(i)
            list = item.split(',')
            for measure in list:
                if int(measure) not in new_model:
                    new_model.append(int(measure))
        result.append(new_model)

    remod = []
    for num, i in enumerate(result):
        remod.append([i, complex_models_id[num]])

    return remod






