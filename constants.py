import os

UPLOAD_FOLDER = os.path.abspath('.') + '/uploaded_files/'
ALLOWED_EXTENSIONS = set(['xls', 'xlsx'])
DATABASE_NAME = "test111"
DATABASE_USER = "postgres"
DATABASE_PASSWORD = "gbcmrf"
DATABASE_HOST = "localhost"
DATABASE_PORT = "5432"
AREA_DESCRIPTION_TYPE = {'Мера': '1', 'Время': '2', 'Справочник': '3'}
KIND_OF_METERING = [('1', 'Дискретная'), ('2', 'Непрерывная')]






