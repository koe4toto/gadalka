from wtforms import *
import constants

# Форма создания преметной области
class DataAreaForm(Form):
    title = StringField('Название',[validators.required(message='Обязательное поле'), validators.Length(min=3, max=200, message='Поле должно содержать не менее 3 и не более 200 знаков')])
    description = TextAreaField('Комментарий', [validators.required(message='Обязательное поле')])

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
    description = StringField('Комментарий', [validators.required(message='Обязательное поле')])
    kind_of_metering = RadioField('Величина', choices=constants.KIND_OF_METERING)

# Форма создания измерения-справочника
class RefMeasureForm(Form):
    description = StringField('Комментарий', [validators.required(message='Обязательное поле')])
    ref = SelectField('Величина')

# Форма добавления справочника
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