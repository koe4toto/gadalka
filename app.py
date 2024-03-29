# Библиотеки
from ast import Import
from flask import Flask, render_template, flash, redirect, url_for, session, request, jsonify
from passlib.hash import sha256_crypt
from flask_cors import CORS, cross_origin

# Мои модули
from forms import *
import constants
import databases.db_app as db_app
from decorators import api_is_logged_in

# Настройки
app = Flask(__name__)
cors = CORS(app)
app.config['UPLOAD_FOLDER'] = constants.UPLOAD_FOLDER
app.config['SECRET_KEY'] = '4385nkjcshcfn8642768m,5hbx398sdf234blwkjrlw23t42'
app.config['CORS_HEADERS'] = 'Content-Type'

# Ограничение на загрузку файлов в 100 мегабайт
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

@app.errorhandler(404)
def page_not_found(error):
    return 'This page does not exist', 404

# Проверка авторизации
@app.route("/api/authcheck", methods =['GET'] )
@api_is_logged_in
def api_auth_check():
    return jsonify({'result': True}), 200


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
        db_app.create_user(name, username, email, password)

        flash('Вы зарегистрированны и можете войти', 'success')

        return redirect(url_for('about.index'))
    return render_template('register.html', form=form)

# Форма входа
@app.route("/login", methods =['GET', 'POST'] )
def login():
    if request.method == 'POST':
        # Даные полей формы авторизации
        username = request.form['username']
        password_candidate = sha256_crypt.encrypt(str(request.form['password'])) 


        # Поиск пользователя в базе по значению username
        result = db_app.user_search(username)

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


# Форма входа
@app.route("/api/login", methods =['POST'] )
def api_login():
    if request.method == 'POST':
        data = request.get_json()
        username = data['username']
        password_candidate = data['password']

        result = db_app.user_search(username)

        if str(result) == '[]':
            return jsonify({'result': 'Пользователь не найден'}), 401
        else:
            password = result[0][4]
            if sha256_crypt.verify(password_candidate, password):
                app.logger.info('PASSWORD MATCHED')
                # Открывается сессия
                session['logged_in'] = True
                session['username'] = username
                session['user_id'] = result[0][0]

                return jsonify({'result': True}), 200
            else:
                return jsonify({'result': 'Не верный пароль'}), 401



# Выход
@app.route('/logout')
def logout():
    session.clear()
    session.modifited = True
    flash('Вы вышли', 'success')
    return redirect(url_for('login'))


# Выход
@app.route('/api/logout', methods =['GET'])
def api_logout():
    session.clear()
    error = 'Вы вышли'
    return jsonify({'result': error})




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

# Отчеты
from reports import mod as modelsModule
app.register_blueprint(modelsModule)




# Запуск сервера
if __name__ == "__main__":
    app.secret_key = 'secret123'
    app.run(debug=True)