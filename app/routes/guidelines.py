from . import main
from flask import render_template

@main.route('/guidelines')
def guidelines():
    return render_template('guidelines.html')
