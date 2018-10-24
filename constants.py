import os

UPLOAD_FOLDER = os.path.abspath('.') + '/uploaded_files/'
ALLOWED_EXTENSIONS = set(['xls', 'xlsx'])
USERS_DATABASE_NAME = "users_data"
DATABASE_NAME = "test111"
DATABASE_USER = "postgres"
DATABASE_PASSWORD = "gbcmrf"
DATABASE_HOST = "localhost"
DATABASE_PORT = "5432"
AREA_DESCRIPTION_TYPE = {'Мера': '1', 'Время': '2', 'Справочник': '3'}
KIND_OF_METERING = [('1', 'Дискретная'), ('2', 'Непрерывная')]
TYPE_OF_MEASURE = {
    1: 'VARCHAR',
    2: 'REAL',
    3: 'VARCHAR',
    4: 'TIME',
    5: 'DATE',
    6: 'timestamp without time zone'
}






