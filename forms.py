from wtforms import *
import constants

# Классы полей ввода
forrms = {
    'TextAreaField': TextAreaField,
    'StringField': StringField,
    'PasswordField': PasswordField,
    'RadioField': RadioField,
    'SelectField': SelectField,
    'SelectMultipleField': SelectMultipleField,
    'BooleanField': BooleanField

}

# Форма создания преметной области
class DataAreaForm(Form):
    title = StringField('Название',[validators.required(message='Обязательное поле'), validators.Length(min=3, max=200, message='Поле должно содержать не менее 3 и не более 200 знаков')])
    description = TextAreaField('Комментарий')

# Фрма регистрации
class RegisterForm(Form):
    name = StringField('Имя', [validators.Length(min=1, max=50)])
    username = StringField('Логин', [validators.Length(min=4, max=25)])
    email = StringField('Адрес электронной почты', [validators.Length(min=4, max=25)])
    password = PasswordField('Пороль', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Пароли не совпали')
    ])
    confirm = PasswordField('Повторите пароль, пожалуйста')

# Форма подключения к базе данных по предметной области
class DataConForm(Form):
    database = StringField('База данных', [validators.required(message='Обязательное поле')])
    database_user = StringField('Пользователь', [validators.required(message='Обязательное поле')])
    database_password = PasswordField('Пароль')
    database_host = StringField('Хост', [validators.required(message='Обязательное поле')])
    database_port = StringField('Порт', [validators.required(message='Обязательное поле')])
    database_table = StringField('Таблица', [validators.required(message='Обязательное поле')])

# Форма создания меры
class MeasureForm(Form):
    column_name = StringField('Название колонки в таблице', [validators.required(message='Обязательное поле')])
    description = StringField('Название парамтера', [validators.required(message='Обязательное поле')])

# Форма создания измерения-справочника
class RefMeasureForm(Form):
    column_name = StringField('Название колонки в таблице', [validators.required(message='Обязательное поле')])
    description = StringField('Название парамтера', [validators.required(message='Обязательное поле')])
    ref = SelectField('Справочник')

# Форма добавления справочника
class DataFile(Form):
    file = FileField(u'Таблица с данными')
    type_of = RadioField(
        'Тип обработки',
        [validators.required(message='Обязательное поле')],
        choices=[('1', 'Замена данных'), ('2', 'Добавление новых')],
        default = '1'
    )

# Форма загрузки данных из файла
class RefForm(Form):
    name = StringField('Название', [validators.required(message='Обязательное поле')])
    description = TextAreaField('Комментарий')

# Форма вероятности измерения
class IntervalForm(Form):
    di_from = StringField('Доверительный интерфал от', [validators.required(message='Обязательное поле')])
    di_to = StringField('Доверительный интерфал до', [validators.required(message='Обязательное поле')])

# Форма вероятности измерения
class ProbabilityForm(Form):
    probability = StringField('Вероятность', [validators.required(message='Обязательное поле')])

# Форма фильтра меры
class MeFilterForm(Form):
    test1 = StringField('тест1', [validators.required(message='Обязательное поле')])
    test2 = StringField('тест1', [validators.required(message='Обязательное поле')])

class FormGenerator(Form):
    favor = core.SelectMultipleField(
        label="По умолчанию",
        choices=(
            (1, 'Ап-ап'),
            (2, 'Два'),
            (3, 'Три')
        ),
        default=2
    )
    pass

# Генератор формы принимает количество полей и список параметров для отображения
def AssosiationsForm(request, args):
    value = 2
    for i in args:
        setattr(FormGenerator, i[0], forrms[i[1]](i[2], choices=i[3], default=value))
        print(i[0])
    FormGenerator.first.default = [(2, 'Время')]
    return FormGenerator(request)


