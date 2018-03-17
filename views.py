from flask import Blueprint, render_template

mod = Blueprint('about', __name__)

# О проекте
@mod.route("/about")
def about():
    return render_template('about.html')

# Главная
@mod.route("/")
def index():
    return render_template('home.html')