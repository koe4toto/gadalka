import os

UPLOAD_FOLDER = os.path.abspath('.') + '/uploaded_files/'
ERROR_FOLDER = os.path.abspath('.') + '/error_files/'
TEST_FOLDER = os.path.abspath('.') + '/data_for_test/'
ALLOWED_EXTENSIONS = set(['xls', 'xlsx'])
USERS_DATABASE_NAME = "users_data"
QUEUE_DATABASE_NAME = "queue"
DATABASE_NAME = "mdb"
DATABASE_USER = "postgres"
DATABASE_PASSWORD = "gbcmrf"
DATABASE_HOST = "localhost"
DATABASE_PORT = "5432"
AREA_DESCRIPTION_TYPE = {'Мера': '1', 'Время': '2', 'Справочник': '3'}
KIND_OF_METERING = [('1', 'Дискретная'), ('2', 'Непрерывная')]
TYPE_OF_MEASURE = {
    1: 'REAL',
    2: 'VARCHAR',
    3: 'VARCHAR references',
    4: 'TIME',
    5: 'DATE',
    6: 'timestamp without time zone'
}
TYPE_OF_MODEL = {
    'Автоматически расчитанный': 1,
    'Пользовательская': 2
}
KIND_OF_MODEL = {
    'Сильная связь': 1,
    'Слабая связь': 2,
    'Нет связи': 3
}
# КОэффициент корреляции простых связей,
# которые можно считать значимым для формирования сложно связи в автоматическом режиме
COMPLEX_MODEL_KOEF = 0.7
COLORS_IN_OREDERS=[
    ('0', 'Без оформления', '#ffffff', '#ffffff'),
    ('1', 'Синий', '#a6cbdc', '#90b3c3'),
    ('2', 'Зеленый', '#caf09c', '#afd087'),
    ('3', 'Красный', '#f7be8f', '#f7a969'),
    ('4', 'Фиолетовый', '#f7a9e7', '#da90cb'),
    ('5', 'Сиреневый', '#d6a6ed', '#c285df'),
    ('6', 'Морская волна', '#a6f4ed', '#7ed5cd'),
    ('7', 'Трава', '#9ef0b1', '#80d093'),
    ('8', 'Желтый', '#f3f597', '#d9db7e'),
    ('9', 'Серый', '#eaeaea', '#d6d6d6')
]

KIND_OF_STATISTIC = {
    'Выборочная': 1,
    'Генеральная': 2
}

TIPE_OF_STATISTIC = {
    'Объем выборки': 1,
    'Сумма значений': 2,
    'Максимальное значение': 3,
    'Минимальное значение': 4,
    'Размах': 5,
    'Сренее': 6,
    'Медиана': 7,
    'Первый дециль': 8,
    'Последний дециль': 9,
    'Децильный коэфициент': 10,
    'Межквартильный размах': 11,
    'Мода': 12,
    'Максимальная частота': 13,
    'Дисперсия': 14,
    'Стандартное отклонение': 15,
    'Стандартная ошибка средней': 16,
    'Вариация': 17
}



