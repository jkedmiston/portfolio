# basic flask form, WIP
import os
import copy
import json
import numpy as np
import datetime
from misc_utilities import generate_uuid
from flask import request, flash, Markup
from flask import Blueprint, render_template
from flask_wtf import FlaskForm
from flask import (url_for, redirect, send_from_directory)
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from googleapiclient.errors import HttpError
import pandas as pd
import pygsheets
import google_functions.google_slides
import latex_reports.latex_doc
import latex_reports.latex_utilities
from flask import current_app
reports_bp = Blueprint(
    'reports_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)


@reports_bp.route('/retrieve_pdf', methods=["GET"])
def retrieve_pdf():
    pdfname_only = request.args.get('fname')
    return send_from_directory("tmp", pdfname_only, as_attachment=True)


def perform_automatic_analysis(df, unique_tag, sheet_url, sheet_name):
    """
    From the dataframe, produce plots and summary stats, and present findings as a list of dictionary
    """
    import seaborn as sns
    import matplotlib.pyplot as plt
    #from pandas.api.types import is_numeric_dtype
    sns.set_style('ticks')  # darkgrid, whitegrid, dark, white, ticks}
    plt.rcParams.update({'font.size': 16})
    basic_describe = df.describe(include='all')
    fignames = []

    for i, colname in enumerate(df.columns):
        if colname not in basic_describe.columns:
            continue
        if not np.issubdtype(df[colname].dtype, np.number):
            # do categorical
            print("categorical detected, %s" % colname)
            continue
        else:
            # numeric analysisn
            valid_data = df[df[colname].notnull()][colname]
            count_invalid_data = df[colname].isnull().sum()  # TODO, add to tabular output # noqa
            count_valid_data = len(valid_data)  # TODO, add to tabular output # noqa
            mean = np.mean(valid_data)
            median = np.median(valid_data)
            stdev = np.std(valid_data)

            # make a single basic histogram of this variable
            figname = "tmp/fig%s_%d.png" % (unique_tag, i)
            try:
                # TODO: add test for categorical / string features
                fig, ax = plt.subplots(1, 1, figsize=(
                    6.67, 5))  # fontFamily is serif
                ax.hist(valid_data.values)
                # keep the plots bare bones, so that labels are added at Google slides layer
                fig.savefig(figname)
                plt.close(fig)
            except:
                # Log error TODO
                current_app.logger.warning(
                    "Error occured on column %s" % colname)
                pass

            if os.path.isfile(figname):
                description = f'Basic histogram of {colname}, from the data source <linked here>\ntab {sheet_name}\n\nValid data counts: {count_valid_data}\nInvalid data counts: {count_invalid_data}\nMean: {mean:.2f}\nMedian: {median:.2f}\nStd. dev: {stdev:.2f}\n'

                fignames.append({'figure': figname,
                                 'description': description,
                                 'xlabel': colname,
                                 "slide_title": "Exploratory plots - histograms",
                                 'ylabel': 'Counts'})

    return {'basic_describe': basic_describe,
            'figures': fignames}


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
    """
    returns pygsheets object for a given google sheet. If an error occurs, the type of error is returned so that it can be displayed on a web page
    """
    try:
        wks_in = sheet.worksheet_by_title(title=sheet_name)
        return {'sheet': wks_in, 'exit_code': 0}
    except pygsheets.exceptions.WorksheetNotFound:
        wks_in = sheet.add_worksheet(title=sheet_name)
        return {'sheet': wks_in, 'exit_code': 0}
    except HttpError as err:
        return {'exit_code': -1, 'error_message': 'Permission needed'}
    return {'exit_code': -1, 'error_message': 'Unknown'}


def get_worksheet_from_url(url, sheet_name):
    gsheets = pygsheets.authorize(
        service_account_env_var="GOOGLE_APPLICATION_CREDENTIALS")
    slug = get_gsheets_slug_from_url(url)
    try:
        sheet = gsheets.open_by_key(slug)
        worksheet_to_read = sheet.worksheet_by_title(title=sheet_name)
        return {'sheet': sheet,
                'worksheet': worksheet_to_read,
                'exit_code': 0}
    except pygsheets.exceptions.WorksheetNotFound:
        flash(Markup("Sheet %s not found, check URL and sheet name" % sheet_name))
        return {'exit_code': -1,
                'redirect': url_for('reports_bp.analyze_user_sheet')
                }
    except HttpError as err:
        email = get_service_account_email()
        flash(Markup(
            "Permission is needed to modify the sheet. Give this email: %s permission to edit the sheet. " % email))
        return {'exit_code': -1,
                'redirect': url_for('reports_bp.analyze_user_sheet')}


def replace_figures_with_urls(figures):
    """ replace figure filenames with urls after upload
    """
    figures2 = copy.deepcopy(figures)
    from google_functions.google_storage import upload_file, get_signed_url_from_blob
    for kk, finfo in enumerate(figures):
        blob = upload_file(finfo["figure"])
        url = get_signed_url_from_blob(blob)
        figures2[kk]["url"] = url
    return figures2


@reports_bp.route('/poc')
def poc():
    """
    A POC of google slides, for testing
    """
    doc_info = {
        'url': 'https://www.cnn.com/2020/12/23/politics/trump-ndaa-veto/index.html',
        'email': os.environ["TEST_EMAIL"]}
    figures = [{'figure': 'tmp/fig0.png'},
               {'figure': 'tmp/fig1.png'},
               {'figure': 'tmp/fig2.png'}]
    replace_figures_with_urls(figures)
    doc_info["figures"] = figures

    out = google_functions.google_slides.make_slideshow(doc_info)
    return """<a href="%s">link</a>""" % out


@reports_bp.route('/analyze_user_sheet_results', methods=['GET'])
def analyze_user_sheet_results():
    # TODO, make this retreive from db.
    slides_url = request.args.get('slides_url')
    pdf_filename = request.args.get('pdf_filename')
    return render_template('reports/analyze_user_sheet_finished.html',
                           slides_link=slides_url,
                           pdf_filename=pdf_filename)


@reports_bp.route('/analyze_user_sheet', methods=['GET', 'POST'])
def analyze_user_sheet():
    """
    Takes in google sheet url, uploads automatic analysis and produces LaTeX report of the same. 
    """
    class SheetForm(FlaskForm):
        name = StringField('Sheet URL', validators=[DataRequired()])
        sheet_name = StringField('Targeted tab name to analyze',
                                 validators=[DataRequired()])
        email = StringField(
            'Email address to share results', validators=[DataRequired()])
        submit = SubmitField("Analyze")

    form = SheetForm(request.form)
    if form.validate_on_submit():
        url = form.data["name"]
        sheet_name = form.data["sheet_name"]
        email = form.data["email"]
        info = get_worksheet_from_url(
            url=url, sheet_name=sheet_name)
        if info['exit_code'] == 0:
            sheet = info['sheet']
            worksheet_to_read = info['worksheet']
        else:
            return redirect(info["redirect"])

        info = get_writeable_worksheet(
            sheet=sheet, sheet_name=sheet_name + '-analysis')
        if info['exit_code'] == 0:
            wks_out = info['sheet']
        else:
            flash(Markup(info['error_message']))
            return redirect(url_for('reports_bp.analyze_user_sheet'))

        # do the automatic analysis
        df = get_df_from_worksheet(worksheet_to_read, cleaning=True)
        unique_tag = generate_uuid()
        analysis = perform_automatic_analysis(
            df, unique_tag=unique_tag, sheet_url=url, sheet_name=sheet_name)  # generate figures and labels

        basic_describe = analysis["basic_describe"]
        figures = analysis["figures"]

        # write out latex file
        tex_filename = "tmp/latex_files_%s.tex" % unique_tag
        auto_report = latex_reports.latex_doc.LatexDoc(
            tex_filename,
            preamble=latex_reports.STANDARD_PREAMBLE)

        doc_info = {'analysis_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'url': '#'.join(url.split('#')[0:-1]),
                    'sheet_name': sheet_name,
                    'raw_table': basic_describe,
                    'figures': figures,
                    'title': '',
                    'email': email,
                    'table': basic_describe.to_latex()}

        auto_report.add_contents(r"""\section{Analysis of sheet}
Analysis date: %(analysis_date)s \\
Data source:  \href{%(url)s}{Google sheet}, tab:%(sheet_name)s \\

\section{Overall results}
%(table)s
""" % doc_info)
        auto_report.add_clearpage()
        for fig in figures:
            auto_report.add_figure(
                fig["figure"], caption="Data column %s" % fig["xlabel"])
            auto_report.add_clearpage()

        auto_report.add_contents(r"""\section{Appendix}
- full url to data source: \href{%(url)s}{\url{%(url)s}}
""" % doc_info)
        pdfname = auto_report.write()

        # Produce Google slides version of the report.
        figures2 = replace_figures_with_urls(figures)
        doc_info_slides = doc_info.copy()
        doc_info_slides["figures"] = figures2
        slides_url = google_functions.google_slides.make_slideshow(
            doc_info_slides)

        # gsheets_functions.append_summary(basic_describe)
        # set the new output dataframe
        wks_out.set_dataframe(basic_describe, (1, 1),
                              fit=True, nan='', copy_index=True)
        pdfname_only = os.path.basename(pdfname)
        assert os.path.isfile(os.path.join("tmp", pdfname_only))
        return redirect(url_for("reports_bp.analyze_user_sheet_results", slides_url=slides_url,
                                pdf_filename=pdfname_only))

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
This document is prepared in LaTeX, which may be integrated with python for automated reports easily.
\begin{enumerate}
\item{Item 1 - [Text here]}
\item{Item 2 - for an example ofembedded graphics, see Figure \ref{fig:label}}
\end{enumerate}
\begin{figure}
  \centering
\includegraphics[width=1\textwidth]{figures/getty_images.jpg}
\caption{Caption}
\label{fig:label}
\end{figure}
\end{document}
    """
    f = open("tmp/example_report.tex", "w")
    f.write(dummy_file)
    f.close()
    for j in range(3):
        out = os.system(
            "pdflatex -output-directory=/app/tmp /app/tmp/example_report.tex")
    if out == 0:
        return send_from_directory("/app/tmp", "example_report.pdf", as_attachment=True)
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
