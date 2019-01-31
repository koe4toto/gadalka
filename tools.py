import constants

# Проверка формата загружаемого файлв
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in constants.ALLOWED_EXTENSIONS

# Поиск совпадений в списке
def looking(item, list):
    for i in list:
        if i[1] == item:
            return i

def sqllist(row):
    rows = str(row[0])
    for i in row:
        if row.index(i) > 0:
            if i != '':
                rows += ', ' + str(i)
            else:
                rows += ', None'
    return rows

def sqlvar(row):
    rows = "'" +str(row[0]) + "'"
    for i in row:
        if row.index(i) > 0:
            if i != '':
                rows += ", '" + str(i) + "'"
            else:
                rows += ", 'None'"
    return rows



