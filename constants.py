import os

UPLOAD_FOLDER = os.path.abspath('.') + '/uploaded_files/'
ERROR_FOLDER = os.path.abspath('.') + '/error_files/'
TEST_FOLDER = os.path.abspath('.') + '/data_for_test/'
ALLOWED_EXTENSIONS = set(['xls', 'xlsx'])
USERS_DATABASE_NAME = "users_data"
QUEUE_DATABASE_NAME = "queue"
DATABASE_NAME = "test111"
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
    ('1', 'Синий'),
    ('2', 'Зеленый'),
    ('3', 'Красный')
]





