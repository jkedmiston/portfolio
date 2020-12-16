# basic flask form, WIP
from flask import request
from flask import Blueprint, render_template
from flask_wtf import FlaskForm
from flask import url_for, redirect
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

reports_bp = Blueprint(
    'reports_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)


@reports_bp.route('/success', methods=['POST'])
def success():
    return "Success"


@reports_bp.route('/upload_data', methods=["GET", "POST"])
def upload_data():
    class MyForm(FlaskForm):
        name = StringField('Label Name', validators=[DataRequired()])
        submit = SubmitField("Submit")

    form = MyForm(request.form)
    if form.validate_on_submit():
        # process form inputs here...
        # form.data["name"]
        return redirect(url_for('reports_bp.success'))

    html = render_template('partials/reports/basic_form.html',
                           form=form,
                           action=url_for('reports_bp.success'))

    return render_template('html.html',
                           html=html)
