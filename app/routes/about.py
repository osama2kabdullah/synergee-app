from . import main
from flask import render_template

@main.route('/about')
def about():
    return render_template('about.html')
