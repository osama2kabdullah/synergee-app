from . import main
from flask import render_template

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/api-button')
def api_button():
    return render_template('api_button.html')