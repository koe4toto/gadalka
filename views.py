from flask import Blueprint,session, render_template
from decorators import is_logged_in
import databases.db_app as db_app

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
    user = str(session['user_id'])
    return render_template(
        'dashboard.html',
        data_areas=db_app.select_da(user),
        auto_models=db_app.select_complex_models(1),
        list = db_app.select_pairs()
    )

