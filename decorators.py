from functools import wraps
from flask import flash, redirect, url_for, session


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Вы не авторизованы', 'danger')
            return redirect(url_for('login'))
    return wrap