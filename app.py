# Библиотеки
import psycopg2
from flask import Flask, render_template, flash, redirect, url_for, session, request
from passlib.hash import sha256_crypt
import constants

# Мои модули
from forms import *

# Настройки
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = constants.UPLOAD_FOLDER

# Подключение к базе данных
conn = psycopg2.connect(
    database=constants.DATABASE_NAME,
    user=constants.DATABASE_USER,
    password=constants.DATABASE_PASSWORD,
    host=constants.DATABASE_HOST,
    port=constants.DATABASE_PORT)
cursor = conn.cursor()

# Регистрация
@app.route("/register", methods =['GET', 'POST'] )
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Подключение к базе данных
        cursor.execute('INSERT INTO users (name, username, email, password) VALUES (%s, %s, %s, %s);', (name, username, email, password))
        conn.commit()

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
        cursor.execute("SELECT * FROM users WHERE username = %s", [username])
        result = cursor.fetchall()
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




# Запуск сервера
if __name__ == "__main__":
    app.secret_key = 'secret123'
    app.run(debug=True)