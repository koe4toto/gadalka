from flask import Blueprint, render_template
from decorators import is_logged_in

mod = Blueprint('about', __name__)

# О проекте
@mod.route("/about")
def about():
    return render_template('about.html')

# Главная
@mod.route("/")
def index():
    return render_template('home.html')

# Сводка
@mod.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')

