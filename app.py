# Библиотеки
from flask import Flask, render_template, flash, redirect, url_for, session, request
from passlib.hash import sha256_crypt
import constants
import database as db

# Мои модули
from forms import *

# Настройки
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = constants.UPLOAD_FOLDER

# Ограничение на загрузку файлов в 100 мегабайт
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# Работа с базами данных
db_user = db.users()

@app.errorhandler(404)
def page_not_found(error):
    return 'This page does not exist', 404



# Регистрация
@app.route("/register", methods =['GET', 'POST'] )
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Сохранение в базу данных
        db_user.create(name, username, email, password)

        flash('Вы зарегистрированны и можете войти', 'success')

        return redirect(url_for('about.index'))
    return render_template('register.html', form=form)

# Форма входа
@app.route("/login", methods =['GET', 'POST'] )
def login():
    if request.method == 'POST':
        # Даные полей формы авторизации
        username = request.form['username']
        password_candidate = request.form['password']


        # Поиск пользователя в базе по значению username
        result = db_user.search(username)

        if str(result) == '[]':
            error = 'Пользователь не найден'
            return render_template('login.html', error=error)
        else:
            password = result[0][4]
            if sha256_crypt.verify(password_candidate, password):
                app.logger.info('PASSWORD MATCHED')
                # Открывается сессия
                session['logged_in'] = True
                session['username'] = username
                session['user_id'] = result[0][0]

                flash('You are now logged in', 'success')
                return redirect(url_for('about.dashboard'))
            else:
                error = 'Не верный пароль'
                return render_template('login.html', error=error)

    return render_template('login.html')

# Выход
@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли', 'success')
    return redirect(url_for('login'))




# Информационный интерфейс
from views import mod as aboutModule
app.register_blueprint(aboutModule)

# Пердметные области
from data_areas import mod as areasModule
app.register_blueprint(areasModule)

# Справочники
from refs import mod as refsModule
app.register_blueprint(refsModule)

# Интерфейс результатов статистической обработки данных
from measures import mod as measuresModule
app.register_blueprint(measuresModule)

# Интерфейс результатов статистической обработки связей
from models import mod as modelsModule
app.register_blueprint(modelsModule)




# Запуск сервера
if __name__ == "__main__":
    app.secret_key = 'secret123'
    app.run(debug=True)