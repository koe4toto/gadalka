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
import math
import matplotlib.pyplot as plt


'''
1. Преобразовывать качественные данные в количественные. 
Каким-то образом. Мало получится агрегатов. За три месяца около 100 штук на каждую колонку. 
Не очень эффектно может получиться.

2. Реализовать статистику качественных рядов. 
Это в принципе полезно. 

'''

'''
Количествно значений в выборке
N = int 

Максимальное значение выборки
x_max = float

Минимальное значение выборки
x_min = float

Количествно интервалов на которые можно (нужно) разбить выборку. C округлением до целого.
k = math.ceil(1 + math.log(N, [2]))

Шаг разбиения выборки
h = (x_max - x_min)/ k

Первый и последний интервалы должны быть открытыми. То есть первы начинаться со значения менее x_min
Последние должен заканчиваться значением больше x_max. Каждый следующий интервал имеет длинну h
В итоге посчитав количество попаданий в интервалы можно построить частотную гистограмму

Варианта - серезина интервала. Можно вычислить как сумму значения начала интервала и половины шага

Среднее значение выборки или математическое ожидание
mean = float

Среднее геометрическое. Корень по ооснованию N из произведения всех значения ряда.
Прикладной смысл: среднее приращение величины
geo_mean = float

Среднее квадратичесоке. Квадратный корень из суммы квадратов значений.
Прикладной смысл: среднее квадратическое отклонение от среднего. Сигма.
std_mean = float

График накопленной частоты. Комулята. Отображает сколько уникальных значений выборки имеет частоту ниже указанной.
К прмиеру, показывает сколько людей моложе 18, далее сколько людей моложе 20
и так далее согласно гистограмме распределения
Прикладной смысл: помогает оценить равномерность распределения.
Используя значения этого графика можено расчитать коффициент Джинни.
Вычсляется как разница (половины квадрата максимальной накопленной частоты) и
интеграла (площади) под графиокм накопленных частот
Джинни показывает насколько неравномерно рапределение. К примеру как неравномерно распределены доходы.

Моменты (центральные) распределения показывают силу отклоненияот нормального
Первый центральный момент равен нулю
Второй центральный момент равен дисперсии
Третий центральный момент показывает насколько вершина распределения отклоняется от нормального по горизонтали.
Положительное - смещение влево. Отрицательное - смещение вправо.
Четверты центральный момент показывает насколько вершина распределения отклоняется от нормального по вертикали
Моменты помогают оценить насколько распределение далеко от нормального.


Вариация. Отношение Сигмы (среднеквадратичного отклодения или корня из дисперыии) к средней.
Измеряется в процентах. Чем она меньше, тем меньше изменчивость, тем параметр стабильнее.
Прикладной смысл: помогает оценить силу изменчивости наблюдаемого явления.


Дисперсионная характеристика. Эмпирическое корреляционное соотношение.
Показатель равен корню квадратному из отношения межгрупповой дисперсии к общей.
Изменяется от 0 до 1. Чем больше, тем сильнее связь между количественным и качественным показателем.
К примеру зависит ли средняя зарплата от района проживания.

Общая дисперсия - это разброс всех значений количественного показателя.

Межгрупповая дисперсия равна отношению (суммы произведений количества в каждой группе
на (квадрат разницы среднего группы и общего среднего)) к (сумме всех значений выборки)
Общая дисперсия складывается из суммы межгрупповой и внутрегрупповой дисперсий

Следует расчитать дисперцию для наборов количественных данных каждого качественного значения,
чтобы отыскать среднюю внутригрупповую дисперсию. В этом примере дисперсию в каждом районе.
Средняя внутригрупповая дисперсия равна сумме произведений количества элементов в каждой группе (районе)
поделенной на общее количество событий во всех группах


Децильный коэффициент. Отношение начала последнего децияля к концу первого.
В Дециль попадают десятая часть всех элементов выборки

Фондовый коэффициент. Отношение суммы значений последнего децияля к сумме первого.
В Дециль попадают десятая часть всех элементов выборки

Анализ распределения. Посчитать матожидание и отклонение. Расчитать значение параметров для нормальной
функции распределения. https://www.youtube.com/watch?v=9HaCmjx-RnM&list=PLDrmKwRSNx7K3oySk9znyI4kolE8wQElL&index=10
Позволяет оценить вероятность распределения как нормального. 

Чтобы выбирать для анализа меньше данных, чем есть в генеральной выборке, можено провести анализ выборочной
погрещности и найти такой объем меньшей выборки, для которой отклокнение от средней будет не значительным.
Пересмотреть, чтобы узнать как: https://www.youtube.com/watch?v=e7JYKLovX_4&list=PLDrmKwRSNx7K3oySk9znyI4kolE8wQElL&index=11

Расчет доверительного интервала и оценка выборки. Доверительный интервал подбирается количеством
сигм: одна две три, четыре. Можно посчитать для одной, двух, трёх сигм и сохранить данный результат анализа.
https://www.youtube.com/watch?v=2IdDeATTVbM&list=PLDrmKwRSNx7K3oySk9znyI4kolE8wQElL&index=12

В результате процесс анализа распределения следующий.
1. Определяем размер выборки:
1.1. Если меньше предела для быстрого вычисления, то начинаем анализировать генеральную выборку
1.2. Если больше предела для быстрого вычисления, то определяем объем исследуемой выборки в которой ошибка среднего
     не значительна
2. Вычисляем сигму (среднеквадратичное отклонение)
3. Вычисляем доверительный интервал для одной, двух, треёх сигм. Вычисляем вероятность попадания в данные интервалы.
4. В итоге говорим по-русски: С вероятностью P можно ожидать "Название параметра" в таком диапазоне.
4.1. Размах диапазон математического ожидания тоже неплохо было бы посчитать. 


Соответсвенно стало понятно как анализировать огромные массивы данных, не обрабатывая их целиокм. 
Новые входящие данные нужно оценивать глядя на признак генеральной совокупности. 
- если генеральная совокупность мала, то новые данные не анализируются отдельно 
- если генеральная совокупность уже на момент приёма данных велика, то они новенькие анализируются отдельно 
  в том числе на предмет статистической значимости и соответсвия предыдущей модели данных. 
  Такая работа должна происходить опционально. Как отдельный сервис, предоставлять отдельный отчет. 
   
Коэффициент Фехнера - это оценка степени согласованности направлений отклонений индивидуальных значений факторного 
и результативного признаков от средних значений факторного и результативного признаков. Помогает оценить силу связи 
двух количественных признаков. Колеблется от -1 до 1. При значениях ближе к 0 выявляет отсутствие согласованности. 
Для вычисления требует наличие средних для X и Y. Определяют знаки отклонения (-,+) от среднего значения каждого 
из признаков. Если знаки совпадают, то для С = 1, для H = 0, если не совпадают то наоборот. Далее получаем суммы C и H.
Коэффициент равен отношению (C-H)\ (C+H). ПОзволяет быстро вычислить наличие связи, но не её харрактер.

На графике регрессии хорошо бы отображать средние X и Y такми образом, чтобы они разделяли поверхность 
на 4 прямоугольника (квадранта). Такая визуализация помогает оценить распределение.

Связь двух количественных параметров можно анализировать в рамках групп по X и Y. С помощью таких групп можно 
определять наличие связи (имперический коэффициент детерминации). Смотри выше "Дисперсионная характеристика".

Для исследования связи между двумя качественными параметрами создают таблицу, где в колонках и строчках значения каждого 
из параметра. В ячейках количество совпадений для каждго значения. Пример: по вертикали возраст домов. по горизонтали 
этажность. Так вот по каждому возрасту домов нужно будет записать количество домов с каждой этажностью. 
Далее этот метриал используется для расчета коэффициента корреляции с использованием Фи-квадрат. 
Считается количество степеней сводобы = (количество разбиений по X -1)*(количество разбиений по Y -1)
Расчитывают Хи-квадрат = количество измерений * Фи-квадрат и по таблице для количества степеней свободы ищут 
интерпретацию коэффициента. (Иннтерпретация по таблице - говно решение... для автоматизированной системы)

Коэффициент линейной корреляции в свою очередь тоже можно оценить. Вычисляется такая оценка (сигма-КК)
как отношение 1-КК/корень из количесва данный в выборке (n). Результатом будет напрмер: 0,03. Такой результат можно 
трактовать как 3% колебания КК. То есть это величина (по модулю) отклонения коэффициента корреляции. Предельное отклонение 
это 3 сигмы. И соотвсетвенно если КК больше погрешности в 3 сигмы-КК, то можно считать, что корреляция есть. 
Соответсвенно можно и ицентить достаточную выборку, для которой корреляция будет значима. То есть вычислить такое (n), 
при котором КК будет больше 3-х сигм-КК. Проведя такой анализ, можно сообщить о небоходимом колиестве данных в выборке 
для построения выводов. Если выборка не генеральная сделать проверку в БД на наличие необходимого количества данных. 
Если там её есть достаточно данных, то сформировать новую выборку и посчитать заново. И так пока данные не кончатся 
или не появится статистически значимый результат. 
https://www.youtube.com/watch?v=tMcqXfkMZGY&list=PLDrmKwRSNx7K3oySk9znyI4kolE8wQElL&index=15 - возобносить знания тут.

Остаточное отклонение. Оценка ошибки прогноза. Вычислив стандартное отклонение (корень из дисперсии) ряда разницы 
теоретического Y от реального, пможно поулчить величину описывающую ошибку прогноза. Это занчимая для отчета величина. 
Этот показатель лучше считать отдельно после получения уравнения регрессии. Дисперсия ошибок считается как сумма 
квадратов ошибок, деленный на количество экспериментов.

Если анаизировать регрессию по группам, то нужно учитывать и минимизировать не отклонение средней от модели, а ещё 
и досперсию (разброс) в каждой группе. Сложная тема. Сразу не уловил. 
Повторить материал: https://www.youtube.com/watch?v=nU0MLgxEV5g&list=PLDrmKwRSNx7K3oySk9znyI4kolE8wQElL&index=18

Анализировать сложную кривую выглядящую как пила можно с помощью набора гиперболически падающих и возрастающих величин.
Такой переъод начинается в момент, когда кривизна падения или восхождения достигает опредеённого угла по казательной.
Можно найти такой приблизительный угол, найдя все такие перепады. И тем самым предстазывать ближайший переход 
по скорости возрастания или падения. 
Поплыл вообще: https://www.youtube.com/watch?v=nlvq-L3s5Lc&list=PLDrmKwRSNx7K3oySk9znyI4kolE8wQElL&index=19
В данной лекции можно подсмотреть для квадратичной регрессии можно подглядеть формулу расчета критической точки. 
Вообще такую кривую можно анализировать разбиением на части и анализом каждой части. Разбивать можно находя экстремумы. 
Экстремумы можно искать анализируя изменение угла измерения каждого нового значения.

В список моделей нужно добавить квадратичную функцию y = a*x2 + b*x + c

Множественную корреляцию предлагается расчитывать решая дифур производных для уравнения с суммами всех переменных 
помноженых на коэффициенты. Далее проверять корреляцию отклонений искомой переменной.

Искать коэффициенты уравнения линейной регрессии можно не минимальное отклонение от Y, а отклонение по касательной. 
Тогда формула расчета будет более сложной и содержать тангенс. Придётся отказаться от функции scipy, но при этом меняя
X и Y разницы не будет. Прямые полчатся одинаковыми.

Можно вычислить погрешность для коэффициентов линейной регрессии. 
См. https://www.youtube.com/watch?v=nlvq-L3s5Lc&list=PLDrmKwRSNx7K3oySk9znyI4kolE8wQElL&index=19

Количественные и качественные признаки можно анализировать с помощью коэффициента ранговой корреляции Спирмена. 
Для этого у значений показателей должен быть ранг (вес). Количественнмы признакам ранг можно присвоить отсортировав их
и напротив каждого выставить порядковый номер. При этом одинаковые значения получают средний ранг из имеющихся. 
Складываем все ранги одинаковых значений и делим на их количество. Удобно ранжировать сгруппированные количественные 
данные. Точнее их средние значения по каждой гистограмме.   
Ранжируемые данные применяются при анализе анкетных данных, отборе победителей на сорревнованиях. 
Качественные данные можно ранжировать по значению частот.
Так же можно расчитывать ранговую корреляцию Кендела. Но его мы брать в расчет не станем, так как 
он "более чувствителен" не точен.
https://www.youtube.com/watch?v=XWdJsAAQGns&list=PLDrmKwRSNx7K3oySk9znyI4kolE8wQElL&index=20 
Всё это ранжирование пока кажется бесполезным...

Среди агрегатов для отчетов можно так же иметь темп изменения параметра. Это разница между новым и предыдущим значением. 
Оно наглядным образом указывает на скорость измерения параметра. Выводить его можно в абсолютных значениях, 
можно в процентах. Соответственно это будут два разных агрегата.
Ну ещё формальную кучу данных: https://www.youtube.com/watch?v=-Tlp0mG4XLw&list=PLDrmKwRSNx7K3oySk9znyI4kolE8wQElL&index=21

Как искать базис дял базисных агрегатов? Заставлять пользователя вводить его руками. 
И это похоже восстребованная задача именно в рамках построения отчетов, которые призваны показывать реализацию проекта.

Метод сглаживания по трём точкам. Считаем среднее для каждой точки из сыммы предыдущей, текущей и следующей точки. 
Соответсвенно первая и последняя точки не считаются при таком подходе. Можно считать и по большему количеству точек. 
Можно сглаживание пропорциональное сделать. 

Если есть возможность проранжировать качествкенную характеристику, то для ранга и количественной характеристики можно 
применить гипотезу  о линейной или квазилинейной регрессии.
https://www.youtube.com/watch?v=7AvYviiZ19A&list=PLDrmKwRSNx7K3oySk9znyI4kolE8wQElL&index=22

В общем-то регрессии лучше строить по группам и их вариантам (средним). Тогда прогноз можно и ценивать в промежутке 
лучше и вероятность считать точнее!!!

Чтобы нормально анализировать временные ряды, их нужно ранжировать. Точку отсчета рангов нужно начинать из центра ряда.
В одну сторону положительно, в тругую отрицательно. После ранжирования так же применять регрессионный анализ.

Сезонность. Это когда данные за какой-то период группируются по месяцам, неделям, дням недели. 
Для каждой группы считается среднее, делится на общее среднее за весь период и умножаеся на 100%. 
Индекс показывает долю объема показателя, который не представлен временем. По индексу можно наблюдать нагрузку, 
использовать его в предсказании параметра. 

Для каждой количественной величины можно посчитать автокорреляцию. Особенно это поезно в прикладном смылсе при анализе 
пар со временем. Автокорреляция это корреляция линейнной связи для двух рядов, где первый это простой набор чисел взятый 
в порядке получения по времени. Второй ряд это значения первого взятого со следующего по порядка месту. 
К примеру, если в перовм ряду (13, 24, 46), то во втором (24, 46, ...). Последнее значение отбрасываем 
и анализируем связь между такими рядами. Если автокорреляция высока, то можес считать, что явление 
со времененм изменяется с лагом 1. Можно второй ряд сформировать с логом в два значения. Поискать автокорреляцию там.
С помощью автокорреляции можно исследовать длинну волны в изменении параметра. Если корреляция второго порядка 
возрастает, то длинна волны явно больше одного порядка. Когда автокорреляция начинает убывать, то соответсвенно 
волна заканчивается.

При помощи автокорелляции можно прогнозировать следующе значение по времения на основе предыдущего. 
Соответсвенно порядку автокорелляции.

Для генерации отчетов было-стало хорошоо использовать статистические индексы. Индексы структурных сдвигов. 
Отчеты было-стало хороши для создания прогнозов и оценки выполнения прогнозов и анализа изменения наблюдаемой среды.
https://www.youtube.com/watch?v=KM1k7QqZOMA&list=PLDrmKwRSNx7K3oySk9znyI4kolE8wQElL&index=26

Для выполнения таких операций придется создать выборку за которой мы хотим наблюдать. Зафиксировать исходные данные.
Сформулировать цели, сделать прогноз и его сохранить. Далее сформулировать условия сохранения или получения данных 
об искомых результатах. К примеру, сохраняем данные на такую-то дату или с такими-то характеристиками. 
Получаем данные о том как стало. Расчитывем индексы. 

Структурные сдвиги показывают общий карактер изменения каченственных данных в предметной области. 
Для такого анализа требуется выбрать показатель, который предстоит оценивать. К прмиеру урожайность. 
Нужно иметь распределение этого показателя по качественному ряду (группам количественным). 
Нужно понимать какую долю значение качественнного признака занимает в общей выборке. 
Соответсвенно можем считать идексы и структурные сдвиги оценивать. 

По сути мы берем два показателя. Один количественный и другой качественный или количественный (разбитый на группы). 
Генерируем для них отчет-наблюдение, где собираем частоты качественного признака по значениям или группам в выборке, 
среднее значение количественного покзателя для каждого значения или группы. Отчет должен содержать две части:
было и стало. Нужно определить характеристики было и стало, чтобы машина понимала когда и как закрывать сбор данных. 

Можно было бы бля стало делать статистический прогноз с указанием его качества. Прогноз делать с указание модели, 
на основании которой он сделан. Пытаться генерировать прогнозные данные с жедаемым структурным сдвигом. 

Множественную корелляцию можно считать если парные корелляции считать отдельно от регерссии и по формуле с ковариацией.
https://www.youtube.com/watch?v=JcHCinmoef4&list=PLDrmKwRSNx7K3oySk9znyI4kolE8wQElL&index=28



'''
columns = [(6, 'рас', '', 0),(7, 'два', '', 8),(8, 'три', '', 11), (11, 'два', '', 6)]
class order(object):
    def __init__(self, columns):
        self.columns = columns
        self.result_columns =[]
        self.start()

    # Запуск поиск первого
    def search_first(self):
        for i in self.columns:
            if i[3] == 0:
                return i

    # Поиск следующего
    def search_next(self, prev):
        for i in self.columns:
            if i[3] == prev[0]:
                self.result_columns.append(i)
                self.start_next(i)

    # Запуск поиска следующего в очереди
    def start_next(self, last):
        if last != None:
            self.search_next(last)

    # Запуск выстраивния очереди
    def start(self):
        first = self.search_first()
        if first != None:
            self.result_columns.append(first)
            self.search_next(first)


one = order(columns)
print(one.columns)
print(one.result_columns)

