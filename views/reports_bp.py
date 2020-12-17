# basic flask form, WIP
import os
from flask import request, flash
from flask import Blueprint, render_template
from flask_wtf import FlaskForm
from flask import url_for, redirect
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import pandas as pd
import pygsheets
from googleapiclient.errors import HttpError
import requests
import json

reports_bp = Blueprint(
    'reports_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)


@reports_bp.route('/present_sheet', methods=['GET', 'POST'])
def present_sheet():
    """
    Takes in a url 
    Upload pandas df to a google sheet and redirect there
    """
    class SheetForm(FlaskForm):
        name = StringField('Sheet URL', validators=[DataRequired()])
        submit = SubmitField("Submit")

    form = SheetForm(request.form)
    if form.validate_on_submit():
        gsheets = pygsheets.authorize(
            service_account_env_var="GOOGLE_APPLICATION_CREDENTIALS")
        url = form.data["name"]
        slug = os.path.basename(os.path.split(url)[0])
        try:
            sheet = gsheets.open_by_key(slug)
            wks = sheet.worksheet_by_title(title="Sheet-test")
        except pygsheets.exceptions.WorksheetNotFound:
            sheet = gsheets.open_by_key(slug)
            wks = sheet.add_worksheet(title="Sheet-test")
        except HttpError as err:
            env_vars = json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
            email = env_vars["client_email"]
            flash("Permission is needed to modify %s" % email)
            return redirect(url_for('reports_bp.present_sheet'))

        # placeholder for more complicated function
        df = pd.DataFrame.from_dict({'x': [1, 2, 3],
                                     'y': ['a', 'b', 'c']})
        wks.set_dataframe(df, (1, 1), fit=True, nan='')
        return redirect(url)

    html = render_template('partials/reports/basic_form.html',
                           form=form,
                           action=url_for('reports_bp.success'))

    return render_template('html.html',
                           html=html)


@reports_bp.route('/success', methods=['POST'])
def success():
    return "Success"


@reports_bp.route('/latex_demo', methods=["GET"])
def latex_demo():
    from flask import send_from_directory
    dummy_file = r"""
\documentclass[12pt]{article}
\usepackage{graphicx}
\begin{document}
\section{Introduction}
An example of LaTeX usage, which may be integrated with python for reports easily.
\begin{enumerate}
\item{This}
\item{Next, see Figure \ref{fig:label}}
\end{enumerate}
\begin{figure}
  \centering
\includegraphics[width=1\textwidth]{figures/getty_images.jpg}
\caption{Caption}
\label{fig:label}
\end{figure}
\end{document}
    """
    f = open("tmp/dummy.tex", "w")
    f.write(dummy_file)
    f.close()
    for j in range(3):
        out = os.system(
            "pdflatex -output-directory=/app/tmp /app/tmp/dummy.tex")
    if out == 0:
        return send_from_directory("/app/tmp", "dummy.pdf", as_attachment=True)
    else:
        return "Error"


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
