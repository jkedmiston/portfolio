# Some front end/back end games/demos
# WIP
from flask import Blueprint, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

games_bp = Blueprint(
    'games_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)
