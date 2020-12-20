# basic flask form, WIP
import os
import json
import datetime
from flask import request, flash, Markup
from flask import Blueprint, render_template
from flask_wtf import FlaskForm
from flask import (url_for, redirect, send_from_directory)
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from googleapiclient.errors import HttpError
import pandas as pd
import pygsheets

import latex_reports.latex_doc
import latex_reports.latex_utilities

reports_bp = Blueprint(
    'reports_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)


def get_gsheets_slug_from_url(url):
    """
    Get the gsheets key , e.g. 
    turns https://docs.google.com/spreadsheets/d/1u9**abcdefg**61mqkg/edit#gid=0 into 1u9**abcdefg**61mqkg

    """
    return os.path.basename(os.path.split(url)[0])


def get_service_account_email():
    env_vars = json.loads(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
    email = env_vars["client_email"]
    return email


def clean_df(df):
    """
    Don't return a bunch of blank columns
    """
    import numpy as np
    col1 = df.columns[0]
    tmp = df[df[col1] != ""].copy()
    cols, = np.where(df.columns != '')
    tmp = tmp.iloc[:, cols].copy()
    return tmp


def get_df_from_worksheet(wks, cleaning):
    """
    Returns pandas dataframe from a pygsheets worksheet
    """
    try:
        df = wks.get_as_df()
    except AssertionError:
        df = wks.get_as_df(has_header=False)

    if cleaning:
        df = clean_df(df)
    return df


def get_writeable_worksheet(sheet, sheet_name):
    try:
        wks_in = sheet.worksheet_by_title(title=sheet_name)
        return {'sheet': wks_in, 'exit_code': 0}
    except pygsheets.exceptions.WorksheetNotFound:
        wks_in = sheet.add_worksheet(title=sheet_name)
        return {'sheet': wks_in, 'exit_code': 0}
    except HttpError as err:
        return {'exit_code': -1, 'error_message': 'Permission needed'}
    return {'exit_code': -1, 'error_message': 'Unknown'}


@reports_bp.route('/analyze_user_sheet', methods=['GET', 'POST'])
def analyze_user_sheet():
    """
    Takes in google sheet url, uploads automatic analysis and produces LaTeX report of the same. 
    """
    class SheetForm(FlaskForm):
        name = StringField('Sheet URL', validators=[DataRequired()])
        sheet_name = StringField('Targeted tab name to analyze',
                                 validators=[DataRequired()])
        submit = SubmitField("Analyze")

    form = SheetForm(request.form)
    if form.validate_on_submit():
        gsheets = pygsheets.authorize(
            service_account_env_var="GOOGLE_APPLICATION_CREDENTIALS")
        url = form.data["name"]
        sheet_name = form.data["sheet_name"]
        slug = get_gsheets_slug_from_url(url)
        try:
            sheet = gsheets.open_by_key(slug)
            wks_in = sheet.worksheet_by_title(title=sheet_name)
        except pygsheets.exceptions.WorksheetNotFound:
            flash(Markup("Sheet %s not found, check URL and sheet name" % sheet_name))
            return redirect(url_for('reports_bp.analyze_user_sheet'))
        except HttpError as err:
            email = get_service_account_email()
            flash(Markup(
                "Permission is needed to modify the sheet. Give this email: %s permission to edit the sheet. " % email))
            return redirect(url_for('reports_bp.analyze_user_sheet'))

        info = get_writeable_worksheet(
            sheet, sheet_name=sheet_name + '-analysis')
        if info['exit_code'] == 0:
            wks_out = info['sheet']
        else:
            flash(Markup(info['error_message']))
            return redirect(url_for('reports_bp.analyze_user_sheet'))

        # do the automatic analysis
        df = get_df_from_worksheet(wks_in, cleaning=True)
        basic_describe = df.describe()

        # write out latex file
        auto_report = latex_reports.latex_doc.LatexDoc(
            "tmp/latex_files.tex",
            preamble=latex_reports.STANDARD_PREAMBLE)

        doc_info = {'analysis_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'url': '#'.join(url.split('#')[0:-1]),
                    'sheet_name': sheet_name,
                    'table': basic_describe.to_latex()}
        auto_report.add_contents(r"""\section{Analysis of sheet}
Analysis date: %(analysis_date)s \\
Data source:  \href{%(url)s}{Google sheet}, tab:%(sheet_name)s \\

\section{Results}
%(table)s

\section{Appendix}
- full url to data source: \href{%(url)s}{\url{%(url)s}}
""" % doc_info
                                 )
        pdfname = auto_report.write()

        # set the new output dataframe
        wks_out.set_dataframe(basic_describe, (1, 1),
                              fit=True, nan='', copy_index=True)
        flash(Markup(
            '<div style="color:white;">Success, click <a href="%s">here</a></div>' % url))
        pdfname_only = os.path.basename(pdfname)
        assert os.path.isfile(os.path.join("tmp", pdfname_only))
        return send_from_directory("tmp", pdfname_only, as_attachment=True)

    form_html = render_template('partials/reports/basic_form.html',
                                form=form,
                                action=url_for('reports_bp.success'))

    return render_template('reports/analyze_user_sheet.html',
                           service_email=get_service_account_email(),
                           form_html=form_html)


@reports_bp.route('/present_sheet', methods=['GET', 'POST'])
def present_sheet():
    """
    Takes in a url 
    Upload pandas df to a google sheet and redirect there
    """
    class SheetForm(FlaskForm):
        name = StringField('Sheet URL', validators=[DataRequired()])
        sheet_name = StringField('Desired tab name',
                                 validators=[DataRequired()])
        submit = SubmitField("Submit")

    form = SheetForm(request.form)
    if form.validate_on_submit():
        gsheets = pygsheets.authorize(
            service_account_env_var="GOOGLE_APPLICATION_CREDENTIALS")
        url = form.data["name"]
        sheet_name = form.data["sheet_name"]
        slug = os.path.basename(os.path.split(url)[0])
        try:
            sheet = gsheets.open_by_key(slug)
            wks = sheet.worksheet_by_title(title=sheet_name)
        except pygsheets.exceptions.WorksheetNotFound:
            sheet = gsheets.open_by_key(slug)
            wks = sheet.add_worksheet(title=sheet_name)
        except HttpError as err:
            email = get_service_account_email()
            flash(Markup(
                "Permission is needed to modify the sheet. Give this email: %s permission to edit the sheet. " % email))
            return redirect(url_for('reports_bp.present_sheet'))

        # placeholder for more complicated function
        df = pd.DataFrame.from_dict({'x': [1, 2, 3],
                                     'y': ['a', 'b', 'c']})
        wks.set_dataframe(df, (1, 1), fit=True, nan='')
        flash(Markup('Success, click <a href="%s">here</a>' % url))
        return redirect(url_for('reports_bp.present_sheet'))

    form_html = render_template('partials/reports/basic_form.html',
                                form=form,
                                action=url_for('reports_bp.success'))

    return render_template('reports/present_sheet.html',
                           service_email=get_service_account_email(),
                           form_html=form_html)


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
