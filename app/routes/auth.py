from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from ..user import HARDCODED_USER
from ..forms import LoginForm  # keep your existing login form

auth_bp = Blueprint('auth', __name__, template_folder='templates', url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        if email == HARDCODED_USER.email and password == HARDCODED_USER.password:
            login_user(HARDCODED_USER)
            return redirect(url_for('main.index'))
        else:
            flash("Invalid credentials", "danger")

    return render_template('auth/login.html', form=form)

# Registration is disabled for single-user app
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    flash("Registration is disabled.", "warning")
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('auth.login'))
