# Some front end/back end games/demos
from flask import Blueprint, render_template, request
from flask_wtf import FlaskForm
from flask import url_for, redirect
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

games_bp = Blueprint(
    'games_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)


@games_bp.route('/background_job', methods=['GET', 'POST'])
def background_job():
    """
    Triggers a background job on sheet submittion
    """
    from celery_jobs import celery_delay_method

    class SheetForm(FlaskForm):
        name = StringField('Text to add', validators=[DataRequired()])
        submit = SubmitField("Submit")

    form = SheetForm(request.form)
    if form.validate_on_submit():
        celery_delay_method.delay()
        return "hello"

    html = render_template('partials/reports/basic_form.html',
                           form=form,
                           action=url_for('reports_bp.success'))

    return render_template('html.html',
                           html=html)
